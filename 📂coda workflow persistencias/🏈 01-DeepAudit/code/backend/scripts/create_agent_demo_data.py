#!/usr/bin/env python3
"""
创建 Agent 审计任务演示数据
用于生成 HTML 报告示例展示

运行方式:
cd backend && python -m scripts.create_agent_demo_data
"""

import asyncio
import json
import uuid
import sys
import os
from datetime import datetime, timedelta, timezone

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from app.core.config import settings
from app.models.user import User
from app.models.project import Project
from app.models.agent_task import (
    AgentTask, AgentEvent, AgentFinding, AgentTreeNode, AgentCheckpoint,
    AgentTaskStatus, AgentTaskPhase, AgentEventType,
    VulnerabilitySeverity, VulnerabilityType, FindingStatus
)


# 演示数据配置
DEMO_PROJECT_NAME = "VulnWebApp - 安全演示项目"
DEMO_TASK_NAME = "智能漏洞挖掘审计 - 完整示例"


async def get_or_create_demo_project(db: AsyncSession, user_id: str) -> Project:
    """获取或创建演示项目"""
    result = await db.execute(
        select(Project).where(Project.name == DEMO_PROJECT_NAME)
    )
    project = result.scalars().first()

    if not project:
        project = Project(
            name=DEMO_PROJECT_NAME,
            description="用于演示 Agent 智能审计功能的示例 Web 应用项目，包含多种常见安全漏洞",
            source_type="zip",
            owner_id=user_id,
            is_active=True,
            default_branch="main",
            programming_languages=json.dumps(["Python", "JavaScript", "SQL"]),
            created_at=datetime.now(timezone.utc) - timedelta(days=7),
        )
        db.add(project)
        await db.flush()
        print(f"✓ 创建演示项目: {project.name}")
    else:
        print(f"演示项目已存在: {project.name}")

    return project


async def create_agent_demo_task(db: AsyncSession, project: Project, user_id: str) -> AgentTask:
    """创建 Agent 审计任务演示数据"""

    # 检查是否已存在
    result = await db.execute(
        select(AgentTask).where(AgentTask.name == DEMO_TASK_NAME)
    )
    existing = result.scalars().first()
    if existing:
        print(f"删除已存在的演示任务: {existing.id}")
        await db.delete(existing)
        await db.flush()

    now = datetime.now(timezone.utc)
    task_start = now - timedelta(minutes=15)
    task_end = now - timedelta(minutes=2)

    # 创建 Agent 任务
    task = AgentTask(
        id=str(uuid.uuid4()),
        project_id=project.id,
        created_by=user_id,
        name=DEMO_TASK_NAME,
        description="对 VulnWebApp 进行全面的安全漏洞扫描，包括 SQL 注入、XSS、命令注入等常见漏洞类型的检测与验证",
        task_type="agent_audit",

        # 配置
        audit_scope={"include": ["**/*.py", "**/*.js", "**/*.html"], "exclude": ["tests/*", "node_modules/*"]},
        target_vulnerabilities=["sql_injection", "xss", "command_injection", "path_traversal", "ssrf", "hardcoded_secret"],
        verification_level="sandbox",
        branch_name="main",
        exclude_patterns=["*.test.py", "*.spec.js", "__pycache__/*"],

        # LLM 配置
        llm_config={"provider": "openai", "model": "gpt-4", "temperature": 0.1},
        agent_config={"max_depth": 3, "enable_verification": True, "enable_poc_generation": True},
        max_iterations=50,
        token_budget=100000,
        timeout_seconds=1800,

        # 状态
        status=AgentTaskStatus.COMPLETED,
        current_phase=AgentTaskPhase.REPORTING,
        current_step="报告生成完成",

        # 进度统计
        total_files=48,
        indexed_files=48,
        analyzed_files=48,
        total_chunks=156,

        # Agent 统计
        total_iterations=32,
        tool_calls_count=87,
        tokens_used=45680,

        # 发现统计
        findings_count=8,
        verified_count=6,
        false_positive_count=1,

        # 严重程度统计
        critical_count=2,
        high_count=3,
        medium_count=2,
        low_count=1,

        # 评分
        quality_score=72.5,
        security_score=35.8,

        # 审计计划
        audit_plan={
            "phases": [
                {"name": "代码索引", "description": "建立代码向量索引，支持语义检索"},
                {"name": "入口点识别", "description": "识别用户输入入口点和敏感API"},
                {"name": "漏洞模式匹配", "description": "基于已知漏洞模式进行检测"},
                {"name": "数据流分析", "description": "追踪污点数据流，验证漏洞可达性"},
                {"name": "沙箱验证", "description": "在隔离环境中验证漏洞可利用性"},
                {"name": "PoC 生成", "description": "为已验证漏洞生成概念验证代码"},
            ],
            "focus_areas": ["用户认证模块", "数据库查询接口", "文件上传功能", "API 端点"],
        },

        # 时间戳
        created_at=task_start - timedelta(minutes=1),
        started_at=task_start,
        completed_at=task_end,
    )

    db.add(task)
    await db.flush()
    print(f"✓ 创建 Agent 任务: {task.id}")

    return task


async def create_agent_events(db: AsyncSession, task: AgentTask) -> list:
    """创建 Agent 事件流"""

    events = []
    base_time = task.started_at
    sequence = 0

    def add_event(event_type: str, message: str, phase: str = None,
                  tool_name: str = None, tool_input: dict = None,
                  tool_output: dict = None, tool_duration_ms: int = None,
                  finding_id: str = None, tokens_used: int = 0,
                  metadata: dict = None, time_offset_seconds: int = 0):
        nonlocal sequence
        sequence += 1
        event = AgentEvent(
            id=str(uuid.uuid4()),
            task_id=task.id,
            event_type=event_type,
            phase=phase,
            message=message,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            tool_duration_ms=tool_duration_ms,
            finding_id=finding_id,
            tokens_used=tokens_used,
            event_metadata=metadata,
            sequence=sequence,
            created_at=base_time + timedelta(seconds=time_offset_seconds),
        )
        events.append(event)
        return event

    # ========== 任务启动 ==========
    add_event(
        AgentEventType.TASK_START,
        "Agent 审计任务启动，开始智能漏洞挖掘",
        metadata={"target_vulnerabilities": task.target_vulnerabilities},
        time_offset_seconds=0
    )

    # ========== 规划阶段 ==========
    add_event(
        AgentEventType.PHASE_START,
        "进入规划阶段 - 分析项目结构，制定审计策略",
        phase=AgentTaskPhase.PLANNING,
        time_offset_seconds=5
    )

    add_event(
        AgentEventType.THINKING,
        "分析项目结构：检测到 Flask Web 应用框架，包含用户认证、数据库操作、文件处理等模块。重点关注 SQL 注入、XSS、命令注入等高危漏洞。",
        phase=AgentTaskPhase.PLANNING,
        tokens_used=450,
        time_offset_seconds=10
    )

    add_event(
        AgentEventType.PLANNING,
        "制定审计计划：1) 索引代码库 2) 识别入口点 3) 模式匹配检测 4) 数据流分析 5) 沙箱验证 6) 生成报告",
        phase=AgentTaskPhase.PLANNING,
        tokens_used=380,
        time_offset_seconds=15
    )

    add_event(
        AgentEventType.PHASE_COMPLETE,
        "规划阶段完成，识别出 12 个高优先级检查点",
        phase=AgentTaskPhase.PLANNING,
        time_offset_seconds=20
    )

    # ========== 索引阶段 ==========
    add_event(
        AgentEventType.PHASE_START,
        "进入索引阶段 - 构建代码向量索引",
        phase=AgentTaskPhase.INDEXING,
        time_offset_seconds=25
    )

    add_event(
        AgentEventType.TOOL_CALL,
        "调用 RAG 索引工具，处理源代码文件",
        phase=AgentTaskPhase.INDEXING,
        tool_name="rag_index",
        tool_input={"paths": ["app/", "routes/", "models/", "utils/"], "chunk_size": 1500},
        time_offset_seconds=30
    )

    add_event(
        AgentEventType.RAG_RESULT,
        "代码索引完成：48 个文件，156 个代码块，向量维度 1536",
        phase=AgentTaskPhase.INDEXING,
        tool_name="rag_index",
        tool_output={"files_indexed": 48, "chunks_created": 156, "vector_dim": 1536},
        tool_duration_ms=8500,
        time_offset_seconds=45
    )

    add_event(
        AgentEventType.PHASE_COMPLETE,
        "索引阶段完成",
        phase=AgentTaskPhase.INDEXING,
        time_offset_seconds=50
    )

    # ========== 分析阶段 ==========
    add_event(
        AgentEventType.PHASE_START,
        "进入分析阶段 - 执行漏洞检测",
        phase=AgentTaskPhase.ANALYSIS,
        time_offset_seconds=55
    )

    # SQL 注入检测
    add_event(
        AgentEventType.THINKING,
        "开始检测 SQL 注入漏洞：搜索数据库查询相关代码，识别用户输入拼接到 SQL 语句的模式",
        phase=AgentTaskPhase.ANALYSIS,
        tokens_used=320,
        time_offset_seconds=60
    )

    add_event(
        AgentEventType.RAG_QUERY,
        "语义检索：查找 SQL 查询和用户输入处理代码",
        phase=AgentTaskPhase.ANALYSIS,
        tool_name="rag_search",
        tool_input={"query": "SQL query user input parameter database execute", "top_k": 10},
        time_offset_seconds=65
    )

    add_event(
        AgentEventType.TOOL_CALL,
        "读取文件: app/routes/user.py",
        phase=AgentTaskPhase.ANALYSIS,
        tool_name="read_file",
        tool_input={"path": "app/routes/user.py", "start_line": 45, "end_line": 80},
        time_offset_seconds=70
    )

    add_event(
        AgentEventType.FINDING_NEW,
        "发现 SQL 注入漏洞 [Critical]",
        phase=AgentTaskPhase.ANALYSIS,
        metadata={"vulnerability_type": "sql_injection", "severity": "critical", "file": "app/routes/user.py", "line": 52},
        time_offset_seconds=80
    )

    # XSS 检测
    add_event(
        AgentEventType.THINKING,
        "开始检测 XSS 漏洞：搜索 HTML 渲染和用户输入输出相关代码",
        phase=AgentTaskPhase.ANALYSIS,
        tokens_used=280,
        time_offset_seconds=120
    )

    add_event(
        AgentEventType.TOOL_CALL,
        "读取文件: app/templates/comment.html",
        phase=AgentTaskPhase.ANALYSIS,
        tool_name="read_file",
        tool_input={"path": "app/templates/comment.html"},
        time_offset_seconds=130
    )

    add_event(
        AgentEventType.FINDING_NEW,
        "发现存储型 XSS 漏洞 [High]",
        phase=AgentTaskPhase.ANALYSIS,
        metadata={"vulnerability_type": "xss", "severity": "high", "file": "app/templates/comment.html", "line": 28},
        time_offset_seconds=145
    )

    # 命令注入检测
    add_event(
        AgentEventType.RAG_QUERY,
        "语义检索：查找系统命令执行相关代码",
        phase=AgentTaskPhase.ANALYSIS,
        tool_name="rag_search",
        tool_input={"query": "os.system subprocess shell command execute", "top_k": 10},
        time_offset_seconds=180
    )

    add_event(
        AgentEventType.FINDING_NEW,
        "发现命令注入漏洞 [Critical]",
        phase=AgentTaskPhase.ANALYSIS,
        metadata={"vulnerability_type": "command_injection", "severity": "critical", "file": "app/utils/backup.py", "line": 34},
        time_offset_seconds=210
    )

    # 路径遍历检测
    add_event(
        AgentEventType.TOOL_CALL,
        "分析文件操作代码",
        phase=AgentTaskPhase.ANALYSIS,
        tool_name="analyze_code",
        tool_input={"pattern": "file path user input", "scope": "app/routes/"},
        time_offset_seconds=250
    )

    add_event(
        AgentEventType.FINDING_NEW,
        "发现路径遍历漏洞 [High]",
        phase=AgentTaskPhase.ANALYSIS,
        metadata={"vulnerability_type": "path_traversal", "severity": "high", "file": "app/routes/download.py", "line": 18},
        time_offset_seconds=280
    )

    # SSRF 检测
    add_event(
        AgentEventType.FINDING_NEW,
        "发现 SSRF 漏洞 [High]",
        phase=AgentTaskPhase.ANALYSIS,
        metadata={"vulnerability_type": "ssrf", "severity": "high", "file": "app/routes/proxy.py", "line": 42},
        time_offset_seconds=320
    )

    # 硬编码密钥检测
    add_event(
        AgentEventType.TOOL_CALL,
        "扫描硬编码密钥和敏感信息",
        phase=AgentTaskPhase.ANALYSIS,
        tool_name="secret_scan",
        tool_input={"patterns": ["api_key", "password", "secret", "token"]},
        time_offset_seconds=360
    )

    add_event(
        AgentEventType.FINDING_NEW,
        "发现硬编码 API 密钥 [Medium]",
        phase=AgentTaskPhase.ANALYSIS,
        metadata={"vulnerability_type": "hardcoded_secret", "severity": "medium", "file": "app/config.py", "line": 15},
        time_offset_seconds=380
    )

    add_event(
        AgentEventType.FINDING_NEW,
        "发现弱加密配置 [Medium]",
        phase=AgentTaskPhase.ANALYSIS,
        metadata={"vulnerability_type": "weak_crypto", "severity": "medium", "file": "app/utils/crypto.py", "line": 8},
        time_offset_seconds=400
    )

    add_event(
        AgentEventType.FINDING_NEW,
        "发现调试模式未关闭 [Low]",
        phase=AgentTaskPhase.ANALYSIS,
        metadata={"vulnerability_type": "security_misconfiguration", "severity": "low", "file": "app/__init__.py", "line": 25},
        time_offset_seconds=420
    )

    add_event(
        AgentEventType.PHASE_COMPLETE,
        "分析阶段完成，发现 8 个潜在漏洞",
        phase=AgentTaskPhase.ANALYSIS,
        time_offset_seconds=450
    )

    # ========== 验证阶段 ==========
    add_event(
        AgentEventType.PHASE_START,
        "进入验证阶段 - 在沙箱环境中验证漏洞",
        phase=AgentTaskPhase.VERIFICATION,
        time_offset_seconds=460
    )

    # SQL 注入验证
    add_event(
        AgentEventType.SANDBOX_START,
        "启动沙箱环境验证 SQL 注入漏洞",
        phase=AgentTaskPhase.VERIFICATION,
        tool_name="sandbox",
        time_offset_seconds=470
    )

    add_event(
        AgentEventType.SANDBOX_EXEC,
        "执行 SQL 注入 PoC：' OR '1'='1' --",
        phase=AgentTaskPhase.VERIFICATION,
        tool_name="sandbox",
        tool_input={"payload": "' OR '1'='1' --", "target": "/api/user/search?name="},
        time_offset_seconds=480
    )

    add_event(
        AgentEventType.SANDBOX_RESULT,
        "SQL 注入验证成功 - 成功绕过认证获取所有用户数据",
        phase=AgentTaskPhase.VERIFICATION,
        tool_name="sandbox",
        tool_output={"success": True, "response_code": 200, "data_leaked": True},
        tool_duration_ms=1200,
        time_offset_seconds=490
    )

    add_event(
        AgentEventType.FINDING_VERIFIED,
        "SQL 注入漏洞已验证 [Critical]",
        phase=AgentTaskPhase.VERIFICATION,
        time_offset_seconds=495
    )

    # 命令注入验证
    add_event(
        AgentEventType.SANDBOX_EXEC,
        "执行命令注入 PoC：; id; whoami",
        phase=AgentTaskPhase.VERIFICATION,
        tool_name="sandbox",
        tool_input={"payload": "; id; whoami", "target": "/api/backup?filename="},
        time_offset_seconds=520
    )

    add_event(
        AgentEventType.SANDBOX_RESULT,
        "命令注入验证成功 - 成功执行任意系统命令",
        phase=AgentTaskPhase.VERIFICATION,
        tool_name="sandbox",
        tool_output={"success": True, "output": "uid=1000(www-data) gid=1000(www-data)"},
        tool_duration_ms=800,
        time_offset_seconds=535
    )

    add_event(
        AgentEventType.FINDING_VERIFIED,
        "命令注入漏洞已验证 [Critical]",
        phase=AgentTaskPhase.VERIFICATION,
        time_offset_seconds=540
    )

    # XSS 验证
    add_event(
        AgentEventType.SANDBOX_EXEC,
        "执行 XSS PoC：<script>alert('XSS')</script>",
        phase=AgentTaskPhase.VERIFICATION,
        tool_name="sandbox",
        tool_input={"payload": "<script>alert('XSS')</script>", "target": "/api/comment"},
        time_offset_seconds=560
    )

    add_event(
        AgentEventType.FINDING_VERIFIED,
        "存储型 XSS 漏洞已验证 [High]",
        phase=AgentTaskPhase.VERIFICATION,
        time_offset_seconds=580
    )

    # 路径遍历验证
    add_event(
        AgentEventType.SANDBOX_EXEC,
        "执行路径遍历 PoC：../../../etc/passwd",
        phase=AgentTaskPhase.VERIFICATION,
        tool_name="sandbox",
        tool_input={"payload": "../../../etc/passwd", "target": "/api/download?file="},
        time_offset_seconds=600
    )

    add_event(
        AgentEventType.FINDING_VERIFIED,
        "路径遍历漏洞已验证 [High]",
        phase=AgentTaskPhase.VERIFICATION,
        time_offset_seconds=620
    )

    # SSRF 验证
    add_event(
        AgentEventType.SANDBOX_EXEC,
        "执行 SSRF PoC：http://169.254.169.254/latest/meta-data/",
        phase=AgentTaskPhase.VERIFICATION,
        tool_name="sandbox",
        tool_input={"payload": "http://169.254.169.254/latest/meta-data/", "target": "/api/proxy?url="},
        time_offset_seconds=640
    )

    add_event(
        AgentEventType.FINDING_VERIFIED,
        "SSRF 漏洞已验证 [High]",
        phase=AgentTaskPhase.VERIFICATION,
        time_offset_seconds=660
    )

    # 误报排除
    add_event(
        AgentEventType.THINKING,
        "验证硬编码密钥：检查是否为测试/示例配置",
        phase=AgentTaskPhase.VERIFICATION,
        tokens_used=180,
        time_offset_seconds=680
    )

    add_event(
        AgentEventType.FINDING_FALSE_POSITIVE,
        "硬编码密钥为误报 - 该文件为示例配置模板",
        phase=AgentTaskPhase.VERIFICATION,
        metadata={"reason": "File is example configuration template, not production code"},
        time_offset_seconds=700
    )

    add_event(
        AgentEventType.PHASE_COMPLETE,
        "验证阶段完成：6 个漏洞已验证，1 个误报已排除",
        phase=AgentTaskPhase.VERIFICATION,
        time_offset_seconds=720
    )

    # ========== 报告阶段 ==========
    add_event(
        AgentEventType.PHASE_START,
        "进入报告阶段 - 生成安全审计报告",
        phase=AgentTaskPhase.REPORTING,
        time_offset_seconds=730
    )

    add_event(
        AgentEventType.TOOL_CALL,
        "生成漏洞详情和修复建议",
        phase=AgentTaskPhase.REPORTING,
        tool_name="generate_report",
        tool_input={"format": "html", "include_poc": True, "include_fix": True},
        time_offset_seconds=740
    )

    add_event(
        AgentEventType.INFO,
        "报告生成完成：包含 8 个发现、6 个已验证漏洞、详细修复建议和 PoC 代码",
        phase=AgentTaskPhase.REPORTING,
        time_offset_seconds=760
    )

    add_event(
        AgentEventType.PHASE_COMPLETE,
        "报告阶段完成",
        phase=AgentTaskPhase.REPORTING,
        time_offset_seconds=770
    )

    # ========== 任务完成 ==========
    add_event(
        AgentEventType.TASK_COMPLETE,
        "Agent 审计任务完成！发现 8 个安全问题，其中 2 个严重、3 个高危、2 个中危、1 个低危",
        metadata={
            "total_findings": 8,
            "verified": 6,
            "false_positives": 1,
            "severity_distribution": {"critical": 2, "high": 3, "medium": 2, "low": 1},
            "duration_seconds": 780,
            "tokens_used": 45680,
        },
        time_offset_seconds=780
    )

    # 批量保存事件
    for event in events:
        db.add(event)

    await db.flush()
    print(f"✓ 创建了 {len(events)} 个 Agent 事件")

    return events


async def create_agent_findings(db: AsyncSession, task: AgentTask) -> list:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'backend/scripts/create_agent_demo_data.py','step':'create_agent_findings','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


async def create_agent_tree_nodes(db: AsyncSession, task: AgentTask) -> list:
    """创建 Agent 树节点"""

    nodes_data = [
        {
            "agent_id": "orchestrator-001",
            "agent_name": "主控 Agent",
            "agent_type": "orchestrator",
            "parent_agent_id": None,
            "depth": 0,
            "task_description": "协调整体审计流程，分发子任务",
            "knowledge_modules": ["security_patterns", "vulnerability_db"],
            "status": "completed",
            "result_summary": "成功协调完成安全审计，发现 8 个漏洞",
            "findings_count": 8,
            "iterations": 15,
            "tokens_used": 12500,
            "tool_calls": 25,
            "duration_ms": 780000,
        },
        {
            "agent_id": "analyzer-sql-001",
            "agent_name": "SQL 注入分析 Agent",
            "agent_type": "analyzer",
            "parent_agent_id": "orchestrator-001",
            "depth": 1,
            "task_description": "检测和验证 SQL 注入漏洞",
            "knowledge_modules": ["sql_injection_patterns", "database_security"],
            "status": "completed",
            "result_summary": "发现 1 个严重 SQL 注入漏洞并验证成功",
            "findings_count": 1,
            "iterations": 5,
            "tokens_used": 8200,
            "tool_calls": 18,
            "duration_ms": 120000,
        },
        {
            "agent_id": "analyzer-xss-001",
            "agent_name": "XSS 分析 Agent",
            "agent_type": "analyzer",
            "parent_agent_id": "orchestrator-001",
            "depth": 1,
            "task_description": "检测和验证跨站脚本漏洞",
            "knowledge_modules": ["xss_patterns", "frontend_security"],
            "status": "completed",
            "result_summary": "发现 1 个高危存储型 XSS 漏洞",
            "findings_count": 1,
            "iterations": 4,
            "tokens_used": 6800,
            "tool_calls": 12,
            "duration_ms": 95000,
        },
        {
            "agent_id": "analyzer-cmd-001",
            "agent_name": "命令注入分析 Agent",
            "agent_type": "analyzer",
            "parent_agent_id": "orchestrator-001",
            "depth": 1,
            "task_description": "检测操作系统命令注入漏洞",
            "knowledge_modules": ["command_injection_patterns", "shell_security"],
            "status": "completed",
            "result_summary": "发现 1 个严重命令注入漏洞",
            "findings_count": 1,
            "iterations": 4,
            "tokens_used": 7100,
            "tool_calls": 15,
            "duration_ms": 110000,
        },
        {
            "agent_id": "verifier-001",
            "agent_name": "沙箱验证 Agent",
            "agent_type": "verifier",
            "parent_agent_id": "orchestrator-001",
            "depth": 1,
            "task_description": "在隔离沙箱中验证漏洞可利用性",
            "knowledge_modules": ["exploitation_techniques", "poc_generation"],
            "status": "completed",
            "result_summary": "验证 6 个漏洞，排除 1 个误报",
            "findings_count": 6,
            "iterations": 8,
            "tokens_used": 11080,
            "tool_calls": 17,
            "duration_ms": 180000,
        },
    ]

    nodes = []
    for ndata in nodes_data:
        node = AgentTreeNode(
            id=str(uuid.uuid4()),
            task_id=task.id,
            agent_id=ndata["agent_id"],
            agent_name=ndata["agent_name"],
            agent_type=ndata["agent_type"],
            parent_agent_id=ndata["parent_agent_id"],
            depth=ndata["depth"],
            task_description=ndata["task_description"],
            knowledge_modules=ndata["knowledge_modules"],
            status=ndata["status"],
            result_summary=ndata["result_summary"],
            findings_count=ndata["findings_count"],
            iterations=ndata["iterations"],
            tokens_used=ndata["tokens_used"],
            tool_calls=ndata["tool_calls"],
            duration_ms=ndata["duration_ms"],
            created_at=task.started_at,
            started_at=task.started_at + timedelta(seconds=10),
            finished_at=task.completed_at,
        )
        nodes.append(node)
        db.add(node)

    await db.flush()
    print(f"✓ 创建了 {len(nodes)} 个 Agent 树节点")

    return nodes


async def main():
    """主函数"""
    print("=" * 60)
    print("创建 Agent 审计任务演示数据")
    print("=" * 60)

    # 创建数据库连接
    engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            # 获取演示用户
            result = await db.execute(select(User).where(User.email == "demo@example.com"))
            demo_user = result.scalars().first()

            if not demo_user:
                print("❌ 未找到演示用户 (demo@example.com)")
                print("请先运行应用初始化数据库")
                return

            print(f"使用演示用户: {demo_user.email}")

            # 创建或获取演示项目
            project = await get_or_create_demo_project(db, demo_user.id)

            # 创建 Agent 任务
            task = await create_agent_demo_task(db, project, demo_user.id)

            # 创建事件流
            await create_agent_events(db, task)

            # 创建漏洞发现
            await create_agent_findings(db, task)

            # 创建 Agent 树节点
            await create_agent_tree_nodes(db, task)

            # 提交事务
            await db.commit()

            print("=" * 60)
            print("✅ Agent 演示数据创建完成！")
            print(f"   任务 ID: {task.id}")
            print(f"   项目: {project.name}")
            print(f"   发现漏洞: {task.findings_count} 个")
            print(f"   严重程度分布:")
            print(f"     - Critical: {task.critical_count}")
            print(f"     - High: {task.high_count}")
            print(f"     - Medium: {task.medium_count}")
            print(f"     - Low: {task.low_count}")
            print("=" * 60)

        except Exception as e:
            await db.rollback()
            print(f"❌ 创建失败: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    asyncio.run(main())
