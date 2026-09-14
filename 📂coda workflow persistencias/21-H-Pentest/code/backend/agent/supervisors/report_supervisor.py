"""
Report Supervisor - 负责漏洞检测和报告生成
"""
import json
from typing import List, Dict, Any, Optional


class ReportSupervisor:
    """报告监督 - 分析对话历史，提取漏洞"""
    
    def __init__(self, llm_client, output_manager):
        self.llm = llm_client
        self.output = output_manager
        self.context_mgr = None  # 由Agent注入
    
    async def extract_vulnerabilities(
        self,
        conversation_history: List[Dict[str, Any]],
        target_url: str
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:  # 🔥 返回漏洞和攻击路径
        """
        从对话历史中提取漏洞和攻击路径
        
        Args:
            conversation_history: 完整的对话历史
            target_url: 目标URL
        
        Returns:
            (漏洞列表, 攻击路径)
        """
        # 🔥 智能压缩对话历史（保留关键信息）
        if self.context_mgr:
            current_tokens = self.context_mgr.count_messages_tokens(conversation_history)
            self.output.log("info", f"📊 对话历史tokens: {current_tokens}")
            
            # 如果超过80000 tokens，触发压缩
            if current_tokens > 80000:
                self.output.log("warning", "⚠️  对话历史过大，触发压缩...")
                conversation_history = await self.context_mgr.smart_compress(
                    conversation_history,
                    keep_recent=20,  # 保留最近20条
                    target_ratio=0.6  # 压缩到60%
                )
                new_tokens = self.context_mgr.count_messages_tokens(conversation_history)
                self.output.log("success", f"✅ 压缩完成: {current_tokens} -> {new_tokens} tokens")
        
        # 构建提示词
        prompt = self._build_extraction_prompt(target_url)
        
        # 准备消息
        messages = [
            {"role": "system", "content": prompt}
        ]
        
        # 🔥 添加对话历史（只保留assistant和tool消息，过滤system）
        for msg in conversation_history:
            role = msg.get('role')
            content = msg.get('content', '')
            
            if role == 'assistant':
                # Assistant的思考内容
                messages.append({
                    "role": "assistant",
                    "content": content[:5000]  # 限制长度
                })
            elif role == 'tool':
                # 工具执行结果
                tool_name = msg.get('name', 'unknown')
                messages.append({
                    "role": "user",  # 🔥 转换为user，避免LLM不支持tool role
                    "content": f"[工具: {tool_name}]\n{content[:5000]}"
                })
        
        # 添加分析请求
        messages.append({
            "role": "user",
            "content": "请分析以上对话，提取所有发现的漏洞。以JSON格式输出。"
        })
        
        # 调用LLM
        try:
            response = await self.llm.chat(
                messages=messages,
                temperature=0.3,
                stream=False,  # 不流式
                response_format={"type": "json_object"}  # 强制JSON
            )
            
            content = response.get('content', '{}')
            
            # 解析JSON
            try:
                data = json.loads(content)
            except Exception as e:
                self.output.log("error", f"❌ JSON解析失败: {e}")
                self.output.log("debug", f"原始输出: {content[:500]}")
                return []
            
            # 提取漏洞列表
            vulnerabilities = data.get('vulnerabilities', [])
            
            # 🔥🔥🔥 提取攻击路径
            attack_path = data.get('attack_path', [])
            
            # 标准化漏洞格式（添加复现步骤）
            standardized_vulns = []
            for vuln in vulnerabilities:
                standardized_vulns.append({
                    'type': vuln.get('type', 'Unknown'),
                    'severity': vuln.get('severity', 'MEDIUM').upper(),
                    'cvss_score': vuln.get('cvss_score', 5.0),  # 🔥 CVSS评分
                    'description': vuln.get('description', ''),
                    'impact': vuln.get('impact', ''),  # 🔥 影响分析
                    'url': vuln.get('url', target_url),
                    'evidence': vuln.get('evidence', ''),
                    'discovered_at': vuln.get('discovered_at', ''),
                    'reproduction_steps': vuln.get('reproduction_steps', [])  # 🔥 复现步骤
                })
            
            self.output.log("success", f"✅ 提取到 {len(standardized_vulns)} 个漏洞, {len(attack_path)} 个攻击步骤")
            return standardized_vulns, attack_path
        
        except Exception as e:
            self.output.log("error", f"❌ 漏洞提取失败: {e}")
            import traceback
            traceback.print_exc()
            return [], []  # 🔥 返回空列表
    
    def _build_extraction_prompt(self, target_url: str) -> str:
        """构建漏洞提取提示词"""
        return f"""你是一个专业的渗透测试报告分析师，负责从渗透测试对话历史中提取发现的漏洞、攻击路径和复现步骤。

## 目标
目标URL: {target_url}

## 任务
分析以下对话历史，识别所有**成功发现**的漏洞，并提取完整的攻击路径和详细的复现步骤。

## 判断标准
一个漏洞被认为是"发现"需要满足以下条件之一：
1. **工具明确检测到**: 如sqlmap返回"vulnerable"、nuclei报告漏洞
2. **手工验证成功**: 如payload返回了敏感信息、执行了命令
3. **明显的异常行为**: 如错误信息泄露、未授权访问成功

**不要包含**：
- 仅是尝试但未成功的测试
- 仅是猜测或可能存在的漏洞
- 工具扫描但未验证的结果

## 输出格式
以JSON格式输出，结构如下：

```json
{{
  "vulnerabilities": [
    {{
      "type": "SQL注入",
      "severity": "CRITICAL",
      "cvss_score": 9.8,
      "description": "在登录接口发现SQL注入漏洞，可绕过认证并直接访问数据库",
      "impact": "攻击者可以绕过身份验证，获取数据库中的敏感信息，包括用户凭据和flag",
      "url": "{target_url}/login",
      "evidence": "payload: ' OR 1=1# 成功返回了所有用户数据和flag",
      "discovered_at": "round 3",
      "reproduction_steps": [
        "访问目标URL: {target_url}/login",
        "在username字段输入payload: ' OR 1=1#",
        "在password字段输入任意内容",
        "点击登录按钮，观察响应",
        "成功绕过认证并在响应中获取flag{{...}}"
      ]
    }}
  ],
  "attack_path": [
    {{
      "step": 1,
      "action": "信息收集",
      "description": "访问目标网站，发现登录表单使用GET方法提交到check.php，分析HTML源码发现username和password参数",
      "tool": "execute_python",
      "result": "确认存在登录功能，表单使用GET方法，可能存在SQL注入风险"
    }},
    {{
      "step": 2,
      "action": "漏洞发现",
      "description": "尝试在username参数中注入SQL测试payload: ' OR '1'='1",
      "tool": "execute_python",
      "result": "服务器返回异常，确认存在SQL注入漏洞"
    }},
    {{
      "step": 3,
      "action": "漏洞利用",
      "description": "使用payload: ' OR 1=1# 绕过登录认证",
      "tool": "execute_python",
      "result": "成功绕过认证，获取flag{{test_flag_12345}}"
    }}
  ]
}}
```

## 严重程度定义
- CRITICAL (9.0-10.0): 可直接获取系统权限、数据库访问、RCE
- HIGH (7.0-8.9): 可获取敏感信息、绕过认证
- MEDIUM (4.0-6.9): 信息泄露、低危XSS
- LOW (0.1-3.9): 配置问题、信息收集

## 攻击路径要求
- 按实际执行顺序记录每个关键步骤（信息收集 → 漏洞发现 → 漏洞利用 → 获取flag）
- 每步必须包含: step(序号)、action(行动类型)、description(详细描述)、tool(使用的工具)、result(执行结果)
- 描述要详细具体，包含关键的payload和参数
- step必须从1开始连续编号

## 复现步骤要求
- 每个步骤要具体明确，可直接执行
- 必须包含完整的URL、参数名、payload内容
- 步骤之间要有逻辑连贯性
- 最后一步要明确说明如何获取flag或验证漏洞成功

## 漏洞字段说明
- type: 漏洞类型（如：SQL注入、XSS、文件上传等）
- severity: 严重程度（CRITICAL/HIGH/MEDIUM/LOW）
- cvss_score: CVSS评分（0.0-10.0）
- description: 漏洞描述（简洁说明漏洞是什么）
- impact: 影响分析（说明漏洞可能造成的危害）
- url: 漏洞URL（完整地址）
- evidence: 验证证据（关键的payload和响应）
- discovered_at: 发现轮数
- reproduction_steps: 复现步骤数组

**重要**：
1. 只输出JSON，不要任何额外说明
2. 如果没有发现任何漏洞，返回空数组: {{"vulnerabilities": [], "attack_path": []}}
3. 所有字段必须用中文填写（除了字段名）
4. cvss_score必须是数字类型
5. reproduction_steps和attack_path都必须是数组
6. 确保JSON格式完全正确，可以被json.loads()解析
"""
