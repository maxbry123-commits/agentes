import json
import logging
import litellm
import time
import yaml
import os
from datetime import datetime
from typing import Optional
from agent.solve_agent import SolveAgent
from agent.attack_surface import AttackSurface
from agent.user_interface import UserInterface, CLIUserInterface
from rag.knowledge_base import KnowledgeBase
from rag.seed_knowledge import seed_knowledge_base
from utils.skill_seeder import seed_skills
from utils.text import optimize_text
from utils.llm_request import LLMRequest

logger = logging.getLogger(__name__)


class Workflow:
    def __init__(self, config: dict, mode: str = "ctf", ui: Optional[UserInterface] = None):
        if config is None:
            raise ValueError("配置文件不存在")
        self.config = config
        self.mode = mode
        self.ui = ui or CLIUserInterface()
        self.processor_llm: dict = self.config["llm"]["pre_processor"]

        # 根据模式加载不同的 Prompt 文件
        prompt_file = "pentest_prompt.yaml" if mode == "pentest" else "prompt.yaml"
        prompt_path = f"./prompts/{config.get('prompt_version', 'v1')}/{prompt_file}"
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt: dict = yaml.safe_load(f)

        # 自动种子知识库（仅首次运行或知识库为空时）
        try:
            self.knowledge_base = KnowledgeBase()
            self._auto_seed_knowledge()
        except Exception as e:
            logger.warning(f"知识库初始化失败 (不影响核心流程): {e}")
            self.knowledge_base = None

        # 渗透模式：累积漏洞发现
        self.findings: list = []

    def _auto_seed_knowledge(self):
        """自动种子知识库（仅在知识库为空时）。"""
        try:
            existing = self.knowledge_base.search_knowledge("CTF", n_results=1)
            if not existing:
                stats = seed_knowledge_base(self.knowledge_base)
                if stats:
                    total = stats.pop("total", 0)
                    logger.info(f"知识库种子导入完成: 共 {total} 条")
                    for cat, count in stats.items():
                        logger.info(f"  {cat}: {count} 条")

            # 技能库种子（仅在未导入时）
            existing_skills = self.knowledge_base.search_knowledge("【安全技能】", n_results=1)
            if not existing_skills:
                skill_stats = seed_skills(self.knowledge_base)
                if skill_stats:
                    logger.info(f"技能库导入完成: {skill_stats.get('imported', 0)} 条")
        except Exception as e:
            logger.warning(f"自动种子知识库失败 (可手动导入): {e}")

    def solve(self, problem: str, auto_mode: bool = None, interactive: bool = False, **kwargs) -> str:
        """
        统一入口。根据 self.mode 分发到 CTF 或渗透测试流程。
        参数:
            auto_mode (bool|None)  : True=自动, False=手动, None=让 SolveAgent 交互选择
            interactive (bool)     : 强制启用交互模式
            stop_event (Event)     : threading.Event，设置后终止
            confirm_handler (callable): flag/发现确认回调
            export_writeup (bool)  : 导出报告
            checkpoint_data (dict) : 从 checkpoint 恢复的运行时状态
        """
        # 将 auto_mode 注入 kwargs，统一传递给 SolveAgent
        if auto_mode is not None:
            kwargs["auto_mode"] = auto_mode
        if interactive:
            kwargs["interactive"] = interactive
        start_time = time.time()

        if self.mode == "pentest":
            return self._solve_pentest(problem, start_time, **kwargs)
        return self._solve_ctf(problem, start_time, **kwargs)

    # ── CTF 流程 ────────────────────────────────────────────────────

    def _solve_ctf(self, problem: str, start_time: float, **kwargs) -> str:
        checkpoint_data = kwargs.pop("checkpoint_data", None)
        if checkpoint_data:
            # 恢复时使用存档中的预处理文本，跳过 _summary_input
            processed = checkpoint_data["meta"]["problem_text"]
        else:
            processed = self._summary_input(problem)

        agent = SolveAgent(processed, agent_options=kwargs, knowledge_base=self.knowledge_base,
                           checkpoint_data=checkpoint_data, ui=self.ui)
        agent.confirm_flag_callback = self.confirm_flag
        # Web UI step callback — 推送结构化步骤快照到前端
        step_cb = kwargs.pop("on_step_callback", None)
        if step_cb:
            agent._on_step_done = step_cb

        result = None
        try:
            result = agent.solve()
        finally:
            elapsed = time.time() - start_time
            # 即使 Ctrl+C 中断也尝试导出 Writeup（与渗透模式行为对齐）
            # 注意：Ctrl+C 时 result 为 None，仍需生成（从 checkpoint 历史重建）
            if kwargs.get("export_writeup", False):
                try:
                    self._generate_writeup(agent, processed, result, elapsed)
                except Exception:
                    pass

        # RAG 白名单：仅 solve() 返回真实 flag 时才写入知识库
        if result and self._should_learn_ctf(result):
            self._auto_learn(agent, flag=result)

        return result or "解题终止：异常中断"

    # ── 渗透测试流程 ────────────────────────────────────────────────

    def _solve_pentest(self, problem: str, start_time: float, **kwargs) -> str:
        """渗透测试流程: scope 解析 → 攻击面枚举 → 深度测试 → 报告生成。"""
        checkpoint_data = kwargs.pop("checkpoint_data", None)
        if checkpoint_data:
            scope = checkpoint_data["meta"]["problem_text"]
        else:
            scope = self._summary_input(problem)
        self.ui.display(f"\n授权范围:\n{scope}\n")

        # 初始化攻击面管理
        if checkpoint_data and "attack_surface" in checkpoint_data.get("agent_state", {}):
            self.attack_surface = AttackSurface.from_dict(
                checkpoint_data["agent_state"]["attack_surface"]
            )
        else:
            self.attack_surface = AttackSurface()

        agent = SolveAgent(problem, agent_options=kwargs, knowledge_base=self.knowledge_base,
                           mode="pentest", checkpoint_data=checkpoint_data,
                           attack_surface=self.attack_surface, ui=self.ui)
        agent.confirm_flag_callback = self._confirm_finding
        step_cb = kwargs.pop("on_step_callback", None)
        if step_cb:
            agent._on_step_done = step_cb

        result = None
        try:
            result = agent.solve()
        finally:
            elapsed = time.time() - start_time
            # 收集漏洞发现（攻击面数据在内存中完整保留，即使中断也能提取）
            self._collect_findings(agent)
            # 生成渗透测试报告（无论正常结束还是 Ctrl+C 中断都生成）
            export = kwargs.get("export_writeup", False)
            if export or self.mode == "pentest":
                self._generate_pentest_report(agent, problem, scope, elapsed)

        # RAG 白名单：仅正常完成（非解题终止/非中断）时才沉淀经验
        if result and not result.startswith("解题终止"):
            self._auto_learn(agent)
        else:
            logger.info("渗透测试异常结束，跳过自动学习 (%s)", result or "KeyboardInterrupt")

        if self.findings:
            critical = sum(1 for f in self.findings if f.get("severity") == "critical")
            high = sum(1 for f in self.findings if f.get("severity") == "high")
            return (
                f"渗透测试完成。"
                f"发现 {len(self.findings)} 个漏洞"
                f"（严重: {critical}, 高危: {high}），"
                f"报告已保存至 reports/ 目录。"
            )
        return "渗透测试完成。未发现漏洞。报告已保存至 reports/ 目录。"

    def _collect_findings(self, agent: SolveAgent):
        """从攻击面管理器（优先）或 Agent 历史中提取漏洞发现。"""
        self.findings = []
        if agent.attack_surface and agent.attack_surface.findings:
            # 使用结构化攻击面管理的发现（已去重）
            for f in agent.attack_surface.findings:
                self.findings.append({
                    "type": f.type,
                    "severity": f.severity,
                    "confidence": f.confidence,
                    "evidence": f.evidence,
                    "cvss_base": f.cvss_base,
                    "affected_component": f.affected_component,
                    "owasp_category": f.owasp_category,
                    "id": f.id,
                })
        else:
            for step in agent.memory.history:
                analysis = step.get("analysis", {})
                if isinstance(analysis, dict) and analysis.get("vulnerability_found"):
                    vuln = analysis.get("vulnerability", {})
                    if vuln and isinstance(vuln, dict):
                        vuln["step"] = step.get("step", 0)
                        vuln["tool_args"] = step.get("tool_args", {})
                        self.findings.append(vuln)

    def _confirm_finding(self, finding_candidate: str) -> bool:
        """渗透模式 — 让操作者确认一个发现是否为真实漏洞。"""
        self.ui.display(f"\n=== 潜在发现 ===\n{finding_candidate}")
        choice = self.ui.choose(
            "请确认这是否为真实漏洞？",
            ["确认为漏洞", "标记为误报", "跳过"],
        )
        if "确认为漏洞" in choice:
            return True
        self.ui.display(f"已{'标记为误报' if '误报' in choice else '跳过'}")
        return False

    def _generate_pentest_report(self, agent: SolveAgent, scope_doc: str,
                                  scope_summary: str, elapsed: float):
        """生成渗透测试报告 (Markdown + JSON) — LLM 增强版。

        包含: 执行摘要 / 完整 PoC(漏洞位置+利用手段+工具+结果) /
              CVSS 向量 / 修复建议 / 攻击链 / 凭据清单。
        """
        report_dir = "reports"
        os.makedirs(report_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        self._collect_findings(agent)
        findings = self.findings
        total_steps = len(agent.memory.history)
        history_summary = agent.memory.get_summary(include_key_facts=True)

        # 统计
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for f in findings:
            sev = f.get("severity", "info")
            if sev in severity_counts:
                severity_counts[sev] += 1

        # ── 构建每个 finding 的 PoC 上下文 ──
        poc_contexts = []
        for i, f in enumerate(findings):
            ctx = (
                f"漏洞 #{i + 1}: {f.get('type', '未知')} (严重度: {f.get('severity', '?')}, "
                f"置信度: {f.get('confidence', '?')})\n"
                f"  受影响组件: {f.get('affected_component', 'N/A')}\n"
                f"  证据: {str(f.get('evidence', ''))[:500]}\n"
                f"  工具参数: {str(f.get('tool_args', ''))[:500]}\n"
            )
            step_num = f.get("step", 0)
            if step_num and agent.memory.history:
                for h in agent.memory.history:
                    if h.get("step") == step_num:
                        ctx += (
                            f"  步骤{step_num} 思考: {str(h.get('think', ''))[:300]}\n"
                            f"  步骤{step_num} 输出: {str(h.get('output', ''))[:500]}\n"
                        )
                        break
            poc_contexts.append(ctx)

        # ── 凭据清单 ──
        creds_text = ""
        if agent.attack_surface and agent.attack_surface.credentials_found:
            creds_text = agent.attack_surface.get_credentials_summary(include_header=False)

        # ── Per-finding 生成: PoC (LLM) + CVSS (代码计算, 方案C) ──
        poc_details = {}
        cvss_vectors = {}
        remediation_map = {}
        for i, (f, ctx) in enumerate(zip(findings, poc_contexts), 1):
            # PoC + 修复建议: 单 finding 上下文的 LLM 调用（避免交叉污染）
            poc_result = self._generate_poc_for_finding(f, ctx)
            poc_details[str(i)] = poc_result.get("poc", "")
            remediation_map[str(i)] = poc_result.get("remediation", "")
            # CVSS: 代码计算（方案C — 代码为主，无需 LLM 校正时直接用）
            cvss_vectors[str(i)] = self._calculate_cvss(f)

        # ── 执行摘要 + 攻击链: 1 次 LLM 调用（仅传结构化摘要，不用原始证据） ──
        enhanced = self._generate_executive_summary(
            findings, severity_counts, creds_text, history_summary, scope_summary, total_steps,
        )

        # ── Markdown 报告 ──
        lines = [
            "# 渗透测试报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**测试用时**: {elapsed:.1f} 秒 | **总步骤**: {total_steps}",
            "",
            "---",
            "",
            enhanced.get("executive_summary", "## 1. 执行摘要\n\n无"),
            "",
            "---",
            "",
            "## 2. 测试范围",
            "",
            (scope_summary or "(未提取到授权范围摘要)")[:2000],
            "",
            "---",
            "",
            "## 3. 漏洞清单与 PoC",
            "",
        ]

        if findings:
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
            sorted_findings = sorted(findings, key=lambda f: severity_order.get(f.get("severity", "info"), 99))

            for i, vuln in enumerate(sorted_findings, 1):
                vuln_id = f"PT-{i:03d}"
                sev = vuln.get("severity", "info").upper()
                sev_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢", "INFO": "🔵"}

                lines.extend([
                    f"### {sev_emoji.get(sev, '')} {vuln_id}: {vuln.get('type', '未分类漏洞')}",
                    "",
                    f"| 属性 | 值 |",
                    f"|------|-----|",
                    f"| **严重等级** | {sev} |",
                    f"| **CVSS 向量** | {cvss_vectors.get(str(i), 'N/A')} |",
                    f"| **OWASP** | {vuln.get('owasp_category', 'N/A')} |",
                    f"| **置信度** | {vuln.get('confidence', 'N/A')} |",
                    f"| **受影响组件** | {vuln.get('affected_component', 'N/A')} |",
                    "",
                ])

                poc = poc_details.get(str(i), "")
                if poc:
                    lines.extend(["**PoC (概念验证):**", "", poc, ""])

                evidence = str(vuln.get("evidence", ""))
                if evidence:
                    lines.extend(["**原始证据:**", "```", evidence[:1000], "```", ""])

                rem = remediation_map.get(str(i), "")
                if rem:
                    lines.extend([f"**修复建议:** {rem}", ""])

                lines.extend(["---", ""])
        else:
            lines.append("本次测试未发现安全漏洞。")

        # ── 攻击面详情 ──
        if agent.attack_surface and agent.attack_surface.targets:
            lines.extend(["## 4. 攻击面详情", ""])
            for host, target in sorted(agent.attack_surface.targets.items()):
                tech_str = f" [{', '.join(target.technologies)}]" if target.technologies else ""
                lines.append(f"- **{host}** ({target.status}){tech_str}")
                for port in sorted(target.services.keys()):
                    svc = target.services[port]
                    banner = svc.banner[:80] if svc.banner else ""
                    lines.append(f"  - {svc.port}/{svc.protocol} {svc.status}{' (' + svc.service_name + ')' if svc.service_name else ''}{' — ' + banner if banner else ''}")
            lines.extend(["", "---", ""])

        # ── 凭据清单 ──
        if creds_text:
            lines.extend(["## 5. 已获取凭据/密钥", "", creds_text, "---", ""])

        # ── 攻击链 ──
        chain = enhanced.get("attack_chain", "")
        if chain:
            sec_num = 6 if creds_text else 5
            lines.extend([f"## {sec_num}. 攻击链路", "", chain, "", "---", ""])

        # 截断保护: 在最后一个完整句号/换行处截断
        truncated = history_summary[:3000] if history_summary else ""
        if len(history_summary or "") > 3000:
            truncated = truncated.rsplit("\n", 1)[0] + "\n\n...(后续已截断，详见完整日志)"
        lines.extend([
            "## 测试过程摘要",
            "",
            truncated,
            "",
            "---",
            "",
            f"*由渗透测试 Agent 自动生成 — {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        ])

        md_content = "\n".join(lines)
        md_path = os.path.join(report_dir, f"pentest_report_{timestamp}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # ── JSON 报告 ──
        json_path = os.path.join(report_dir, f"pentest_report_{timestamp}.json")
        try:
            report_data = {
                "generated_at": datetime.now().isoformat(),
                "duration_seconds": round(elapsed, 1),
                "total_steps": total_steps,
                "scope": scope_summary[:1000],
                "severity_summary": severity_counts,
                "total_findings": len(findings),
                "findings": findings,
                "enhanced": {k: v for k, v in enhanced.items() if isinstance(v, (str, dict, list))},
                "credentials": agent.attack_surface.credentials_found if agent.attack_surface else [],
            }
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"JSON 报告写入失败: {e}")

        logger.info(f"渗透测试报告已导出: {md_path}")

    def _generate_executive_summary(self, findings, severity_counts, creds_text,
                                     history_summary, scope_summary, total_steps) -> dict:
        """LLM 生成执行摘要 + 攻击链（仅传结构化摘要，不使用原始证据）。"""
        if not findings:
            return {}
        findings_txt = "\n".join(
            f"- {f.get('type', '?')} ({f.get('severity', '?')}) → {f.get('affected_component', '?')}"
            for f in findings
        )
        prompt = (
            "你是资深渗透测试工程师，请撰写报告的执行摘要和攻击链路。\n\n"
            f"## 测试范围\n{(scope_summary or '')[:500]}\n\n"
            f"## 漏洞统计\n严重:{severity_counts['critical']} 高危:{severity_counts['high']}"
            f" 中危:{severity_counts['medium']} 低危:{severity_counts['low']} 信息:{severity_counts['info']}\n"
            f"总步骤: {total_steps}\n\n"
            f"## 凭据\n{creds_text or '无'}\n\n"
            f"## 漏洞清单\n{findings_txt}\n\n"
            f"## 测试过程\n{(history_summary or '')[:1000]}\n\n"
            "请严格按 JSON 格式输出:\n"
            "{\n"
            '  "executive_summary": "200-300字执行摘要Markdown，概括关键发现和整体风险等级",\n'
            '  "attack_chain": "攻击链路Markdown: 从信息收集到漏洞利用的完整路径，说明各漏洞的关联关系"\n'
            "}"
        )
        try:
            from utils.llm_request import LLMRequest
            llm = LLMRequest("analyzer")
            response = llm.text_completion(prompt=prompt, json_check=True)
            import json as _json
            return _json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.warning("执行摘要生成失败: %s", e)
            return {"executive_summary": "## 1. 执行摘要\n\n(生成失败)", "attack_chain": ""}

    def _generate_poc_for_finding(self, f: dict, poc_ctx: str) -> dict:
        """为单个 finding 生成 PoC + 修复建议。上下文隔离，避免交叉污染。"""
        prompt = (
            "你是一名渗透测试报告工程师，请为此漏洞撰写 PoC 和修复建议。\n\n"
            f"## 漏洞信息\n{poc_ctx}\n\n"
            "请严格按 JSON 格式输出:\n"
            "{\n"
            '  "poc": "PoC:\\n- 漏洞位置: (URL/端点/参数)\\n- 利用手段: (攻击方法)\\n'
            '- 使用工具: (工具名+参数)\\n- 最终结果: (成功获取/证明了什么影响)",\n'
            '  "remediation": "修复建议 (1-2句话)"\n'
            "}\n\n"
            "注意: PoC 和修复建议必须基于上述漏洞信息，不要编造不存在的数据。"
        )
        try:
            from utils.llm_request import LLMRequest
            llm = LLMRequest("analyzer")
            response = llm.text_completion(prompt=prompt, json_check=True)
            import json as _json
            return _json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.warning("PoC 生成失败 for %s: %s", f.get("type", ""), e)
            return {"poc": "", "remediation": ""}

    @staticmethod
    def _calculate_cvss(finding: dict) -> str:
        """基于 finding 的结构化字段计算 CVSS 3.1 向量（纯代码，不用 LLM）。"""
        comp = (finding.get("affected_component") or "").lower()
        ev = (finding.get("evidence") or "").lower()
        ftype = (finding.get("type") or "").lower()
        sev = finding.get("severity", "info")

        # 攻击向量 (AV)
        av = "N"  # default Network
        if any(k in comp for k in ("127.0.0.1", "localhost", "169.254", "10.", "172.16.", "192.168.")):
            av = "A"  # Adjacent (SSRF 内网)

        # 攻击复杂度 (AC)
        ac = "L"
        if any(k in ev for k in ("race", "timing", "race condition", "时序攻击")):
            ac = "H"

        # 所需权限 (PR)
        pr = "N"
        for kw in ("认证绕过", "硬编码", "默认凭据", "未授权", "bypass", "unauthenticated", "no auth"):
            if kw in ftype or kw in ev:
                pr = "N"
                break

        # 用户交互 (UI)
        ui = "R" if any(k in ftype for k in ("xss", "csrf", "clickjacking", "钓鱼")) else "N"

        # 范围 (S)
        s = "C" if any(k in ftype for k in ("ssrf", "容器逃逸", "docker")) else "U"

        # C/I/A — 从 type 推断
        cia_map = {
            "sql注入": ("H", "H", "H"), "sqli": ("H", "H", "H"),
            "命令注入": ("H", "H", "H"), "cmdi": ("H", "H", "H"),
            "代码执行": ("H", "H", "H"), "rce": ("H", "H", "H"),
            "文件上传": ("H", "H", "H"), "上传": ("H", "H", "H"),
            "webshell": ("H", "H", "H"),
            "ssrf": ("H", "N", "N"),
            "认证绕过": ("H", "H", "N"), "bypass": ("H", "H", "N"),
            "信息泄露": ("H", "N", "N"), "泄露": ("M", "N", "N"),
            "路径泄露": ("L", "N", "N"),
            "xss": ("L", "L", "N"), "csrf": ("L", "L", "N"),
            "越权": ("H", "L", "N"), "idor": ("H", "L", "N"),
            "lfi": ("H", "N", "N"), "文件包含": ("H", "N", "N"),
            "xxe": ("H", "N", "H"),
            "配置错误": ("L", "N", "N"), "misconfig": ("L", "N", "N"),
        }
        c, i, a = "L", "N", "N"
        for key, (c_, i_, a_) in cia_map.items():
            if key in ftype:
                c, i, a = c_, i_, a_
                break
        # severity 校正
        if sev == "critical" and c == "L":
            c = "H"
        if sev == "high" and c == "L" and i == "N":
            c = "H"
        if sev in ("info", "low") and c == "H":
            c = "L"

        return f"CVSS:3.1/AV:{av}/AC:{ac}/PR:{pr}/UI:{ui}/S:{s}/C:{c}/I:{i}/A:{a}"

    # ── 共用方法 ────────────────────────────────────────────────────

    def _summary_input(self, text: str) -> str:
        """预处理输入（题目描述 / 授权范围文档）。"""
        attachment_info = ""
        if os.path.isdir("./attachments") and len(os.listdir("./attachments")) > 0:
            attachment_info = "\n附件如下："
            for filename in os.listdir("./attachments"):
                attachment_info += f"\n- {filename}"

        if len(text) < 256:
            return text + attachment_info

        template_key = "scope_summary" if self.mode == "pentest" else "problem_summary"
        template = str(self.prompt.get(template_key, ""))
        placeholder = "{scope}" if self.mode == "pentest" else "{question}"
        prompt = template.replace(placeholder, text)
        message = litellm.Message(role="user", content=optimize_text(prompt))
        try:
            response = litellm.completion(
                model=self.processor_llm["model"],
                api_key=self.processor_llm["api_key"],
                api_base=self.processor_llm["api_base"],
                messages=[message],
            )
            return response.choices[0].message.content + attachment_info
        except Exception as e:
            logger.warning(f"LLM 摘要生成失败，使用原始输入: {e}")
            return text + attachment_info

    def _auto_learn(self, agent, flag: str = ""):
        """自动学习 — 根据当前模式分发到 CTF 或渗透测试的学习流程。"""
        if not self.knowledge_base:
            return
        try:
            if self.mode == "pentest":
                self._auto_learn_pentest(agent)
            else:
                self._auto_learn_ctf(agent, flag or "")
        except Exception as e:
            logger.warning(f"自动学习失败: {e}")

    def _quality_gate_ctf(self, history_summary: str, flag: str,
                          step_count: int = 0, tools_used: set = None) -> bool:
        """CTF 学习质量门控 — 防止低质量经验污染知识库。"""
        # 1. 最小长度检查
        if len(history_summary.strip()) < 50:
            logger.debug("质量门控: 解题摘要太短，跳过学习")
            return False
        # 2. flag 必须是真实 flag 格式，不能是终止消息或错误信息
        if not flag or not self._looks_like_flag(flag):
            logger.debug("质量门控: flag 格式不合法 (%s)，跳过学习", flag[:50])
            return False
        # 3. 最少步数: ≤1 步解出大概率是幻觉/巧合，不入库
        if step_count <= 1:
            logger.debug("质量门控: 步数过少 (%d 步)，跳过学习", step_count)
            return False
        # 4. 最少工具数: 必须至少真正调用过一个工具
        if not tools_used or len(tools_used) == 0:
            logger.debug("质量门控: 无工具使用记录，跳过学习")
            return False
        return True

    @staticmethod
    def _looks_like_flag(text: str) -> bool:
        """检查文本是否包含真实 flag 模式（排除终止消息/错误信息）。"""
        import re
        if not text:
            return False
        # 排除系统终止消息和错误信息
        if text.startswith("解题终止") or text.startswith("未找到flag"):
            return False
        if text.startswith("Error") or text.startswith("Exception"):
            return False
        # 必须包含典型 flag 格式：prefix{content}，content ≥ 4 字符
        flag_patterns = [
            # 已知标准格式
            r'flag\{[^}]{4,}\}', r'FLAG\{[^}]{4,}\}',
            r'CTF\{[^}]{4,}\}', r'HTB\{[^}]{4,}\}',
            # 常见赛事前缀
            r'(?:shellmates|inctf|picoCTF|csaw|hitcon|defcon|sekai|dice|idek|uiuctf|plaid|ductf|wpictf|b01lers|corctf|maple|osu|pbctf|TFCCTF|vishwaCTF|zer0pts)\{[^}]{4,}\}',
            # 通用兜底：字母数字前缀{含至少一个下划线的长内容 ≥10 字符}
            r'[A-Za-z0-9_]{3,}\{[^}]*_[^}]{4,}\}',
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in flag_patterns)

    @staticmethod
    def _should_learn_ctf(result: str) -> bool:
        """CTF 知识库写入白名单 — 仅 solve() 返回真实 flag 时才允许。

        白名单条件（全部满足）:
          1. result 非空
          2. result 通过 _looks_like_flag 格式校验
          3. result 不是已知的终止/异常消息

        被排除的值:
          - "" / None                        → 异常退出
          - "解题终止" / "解题终止：*"       → 中断/卡住/超步数
          - "未找到flag：提前终止"           → LLM 放弃
          - "渗透测试完成*"                  → 渗透模式结果串（不应出现在 CTF 流）
        """
        if not result:
            return False
        # 双重保险：_looks_like_flag 已排除解题终止/Error/Exception 开头
        return Workflow._looks_like_flag(result)

    def _generate_structured_ctf_summary(self, history_summary: str) -> str:
        """使用 LLM 从解题历史中提炼结构化知识（替代裸截断 history_summary[:500]）。

        返回结构化文本，包含: 成功路径、关键技巧、失败教训、环境信息。
        失败时降级为原文前 500 字符。
        """
        max_chars = self.config.get("knowledge_entry_max_chars", 2000)
        prompt = (
            "你是一个CTF竞赛知识提取器。请从以下解题过程记录中提取结构化知识，"
            "保留所有关键技术细节，供后续类似题目复用。\n\n"
            f"## 解题过程\n{history_summary}\n\n"
            "## 输出格式\n"
            "请按以下结构输出（直接输出，不要用JSON包裹）：\n\n"
            "**成功路径**: 1-2句话说明解决此题的关键思路\n"
            "**关键技巧**:\n"
            "- 具体的技术手法（如注入点类型、绕过方式、利用链）\n"
            "- 使用的具体命令、参数和 payload\n"
            "- 关键代码片段或解题脚本的核心逻辑\n"
            "**失败教训**:\n"
            "- 尝试过但无效的方法（避免后人踩坑）\n"
            "**环境信息**:\n"
            "- 端口/服务/版本/框架等侦察发现\n"
            "- 题目提供的关键文件或信息\n\n"
            f"请直接按上述格式输出，总字数控制在{max_chars}字以内。不要输出JSON包装。"
        )
        try:
            llm = LLMRequest("solve_agent")
            response = llm.text_completion(
                prompt=prompt, json_check=False, use_cache=False,
            )
            result = response.choices[0].message.content.strip()
            if len(result) > max_chars * 2:
                result = result[:max_chars * 2]
            return result
        except Exception as e:
            logger.warning("结构化摘要生成失败，降级为原文截断: %s", e)
            return history_summary[:500]

    def _auto_learn_ctf(self, agent, flag: str):
        """从成功解题中自动提取知识并存入知识库（CTF 模式）。"""
        history_summary = agent.memory.get_summary(include_key_facts=True)
        if not history_summary:
            return

        # ── 质量门控（先收集工具使用信息以便门控校验） ──
        tools_used = set()
        for step_data in agent.memory.history:
            tool_name = step_data.get("tool_name", "")
            if tool_name:
                tools_used.add(tool_name)
        step_count = len(agent.memory.history)

        if not self._quality_gate_ctf(history_summary, flag,
                                       step_count=step_count, tools_used=tools_used):
            return

        problem_text = agent.problem[:500]
        from ctf_tool.challenge_classifier import classify as classify_challenge
        files = os.listdir("attachments") if os.path.isdir("attachments") else []
        classification = classify_challenge(problem_text, files, "")
        challenge_type = classification.get("primary_type", "unknown")

        # LLM 结构化摘要：替代裸截断 history_summary[:500]
        structured_summary = self._generate_structured_ctf_summary(history_summary)

        knowledge_text = "\n".join([
            f"【CTF 解题记录】题型: {challenge_type}",
            f"题目: {problem_text[:200]}",
            f"Flag: {flag}",
            f"使用工具: {', '.join(sorted(tools_used))}",
            f"解题要点:\n{structured_summary}",
        ])

        tags = [challenge_type] + list(tools_used) + ["auto_learned"]
        self.knowledge_base.add_general_knowledge(knowledge_text, tags=tags)
        for tname in sorted(tools_used):
            self.knowledge_base.add_tool_knowledge(
                tool_name=tname,
                usage_examples=[f"{challenge_type} 题型: {flag}"],
                best_practices=[structured_summary[:800]],
            )
        logger.info(f"自动学习: 题型={challenge_type}, 工具={len(tools_used)}个")
        self.ui.display(f"\n[自动学习] 已记录到知识库: 题型={challenge_type}, "
                        f"工具={', '.join(sorted(tools_used)) or '无'}, Flag={flag}")

    def _quality_gate_pentest(self, findings: list) -> bool:
        """渗透测试学习质量门控 — 至少有一个 confirmed/likely 发现。"""
        if not findings:
            return False
        quality_count = sum(
            1 for f in findings
            if getattr(f, 'confidence', 'possible') in ('confirmed', 'likely')
        )
        if quality_count == 0:
            logger.debug("质量门控: 无 confirmed/likely 发现，跳过学习")
            return False
        return True

    def _auto_learn_pentest(self, agent):
        """渗透测试自动学习 — 从攻击面管理器中提取可复用模式存入知识库。"""
        if not agent.attack_surface:
            return
        findings = agent.attack_surface.findings
        if not self._quality_gate_pentest(findings):
            return

        # 1. 提取漏洞类型分布
        vuln_types = {}
        for f in findings:
            vt = f.type or "unknown"
            vuln_types[vt] = vuln_types.get(vt, 0) + 1

        # 2. 提取目标技术栈
        techs = set()
        for t in agent.attack_surface.targets.values():
            for tech in t.technologies:
                techs.add(tech)

        # 3. 构建知识文本
        knowledge_lines = [
            "【渗透测试记录】",
            f"目标数: {len(agent.attack_surface.targets)}",
            f"漏洞数: {len(findings)}",
            f"漏洞类型: {', '.join(f'{k}({v})' for k, v in vuln_types.items())}",
        ]
        if techs:
            knowledge_lines.append(f"技术栈: {', '.join(sorted(techs))}")

        for f in findings:
            if getattr(f, 'confidence', '') in ('confirmed', 'likely'):
                knowledge_lines.append(
                    f"[发现] {f.type} | {f.severity} | {f.target} | {str(f.evidence)[:200]}"
                )

        knowledge_text = "\n".join(knowledge_lines)

        # 质量门控：最小长度
        if len(knowledge_text) < 100:
            logger.debug("质量门控: 学习文本太短，跳过")
            return

        tags = list(vuln_types.keys()) + ["pentest", "auto_learned"] + list(techs)
        self.knowledge_base.add_general_knowledge(knowledge_text, tags=tags)

        # 4. 按漏洞类型写入工具知识
        for f in findings:
            if getattr(f, 'confidence', '') in ('confirmed', 'likely'):
                self.knowledge_base.add_tool_knowledge(
                    tool_name=f"pentest_{f.type}",
                    usage_examples=[str(f.evidence)[:500]],
                    best_practices=[f"[渗透] {f.type} 在 {f.target} 验证成功，严重度 {f.severity}"],
                )

        logger.info(f"渗透自动学习: {len(findings)} 个发现, {len(techs)} 个技术栈")
        self.ui.display(f"\n[自动学习] 渗透测试经验已记录到知识库: "
                        f"{', '.join(vuln_types.keys()) or '无漏洞类型'}")

    def _generate_writeup(self, agent: SolveAgent, problem: str, flag: str, elapsed: float):
        """CTF Writeup 生成。"""
        writeup_dir = "writeups"
        os.makedirs(writeup_dir, exist_ok=True)

        tools_used = set()
        for step_data in agent.memory.history:
            tool_args = step_data.get("tool_args", {})
            tool_name = step_data.get("tool_name", "")
            if tool_name:
                tools_used.add(tool_name)

        try:
            files = os.listdir("attachments") if os.path.isdir("attachments") else []
            from ctf_tool.challenge_classifier import classify as classify_challenge
            classification = classify_challenge(problem[:500], files, "")
            challenge_type = classification.get("primary_type", "未分类")
        except Exception:
            challenge_type = "未分类"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 中断/异常终止时 flag 可能为 None — 标注但不崩溃
        flag_display = flag if (flag and not str(flag).startswith("解题终止")) else "（中断未取得 flag）"
        lines = [
            f"# CTF Writeup",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**题型**: {challenge_type}",
            f"**Flag**: `{flag_display}`",
            f"**用时**: {elapsed:.1f} 秒",
            f"**总步骤数**: {len(agent.memory.history)}",
            f"**使用工具数**: {len(agent.tools)}",
            "",
            "---", "",
            "## 题目摘要", "",
            problem[:500] if len(problem) <= 500 else problem[:500] + "...",
            "",
            "---", "",
            "## 解题过程", "",
        ]

        for i, step in enumerate(agent.memory.history):
            step_num = i + 1
            lines.append(f"### Step {step_num}")
            think = step.get("think", "")
            if think:
                lines.append(f"**思考**: {str(think)[:200]}")
            tool_args = step.get("tool_args", "")
            if tool_args:
                lines.append(f"**参数**: `{str(tool_args)[:300]}`")
            output = step.get("output", "")
            if output:
                lines.append("**输出**:")
                lines.append("```")
                lines.append(str(output)[:800])
                lines.append("```")
            analysis = step.get("analysis", {})
            if isinstance(analysis, dict) and analysis.get("analysis"):
                lines.append(f"**分析**: {str(analysis['analysis'])[:300]}")
            # 来源引用
            citation = step.get("source_citation", "")
            if citation:
                lines.append(f"*来源: {citation}*")
            lines.append("")

        lines.extend([
            "---", "",
            "## 解题摘要", "",
            agent.memory.get_summary(include_key_facts=True)[:2000],
            "", "---", "",
            f"*由 CTF Agent 自动生成 — {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        ])

        md_path = os.path.join(writeup_dir, f"writeup_{timestamp}.md")
        json_path = os.path.join(writeup_dir, f"writeup_{timestamp}.json")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        try:
            writeup_data = {
                "challenge_type": challenge_type, "flag": flag_display,
                "elapsed_seconds": round(elapsed, 1),
                "total_steps": len(agent.memory.history),
                "tools_used": sorted(tools_used),
                "problem_summary": problem[:500],
                "generated_at": datetime.now().isoformat(),
            }
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(writeup_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        logger.info(f"Writeup 已导出: {md_path}")

    def confirm_flag(self, flag_candidate: str) -> bool:
        """CTF 模式 — 让用户确认 flag 是否正确。"""
        return self.ui.confirm(
            f"\n发现flag：{flag_candidate}\n请确认这个flag是否正确？",
            yes_label="y", no_label="n",
        )
