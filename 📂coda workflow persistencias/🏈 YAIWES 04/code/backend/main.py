#!/usr/bin/env python3
"""
AI-Pentest: 基于大模型的自动化渗透测试系统
主入口程序
"""
import argparse
import sys
import os
import json
from typing import List, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import (
    load_config, setup_logging, print_banner,
    validate_target, check_dependencies, ensure_dir
)
from utils.logger import get_logger
from core.orchestrator import Orchestrator
from core.decision_engine import DecisionEngine
from core.report_generator import ReportGenerator


console = Console()
logger = None


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="AI-Pentest: 基于大模型的自动化渗透测试系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 自动模式测试单个目标
  python main.py --target 192.168.1.1 --mode auto

  # 指定LLM提供商
  python main.py --target example.com --model deepseek

  # 交互模式
  python main.py --interactive

  # 仅执行信息收集阶段
  python main.py --target 192.168.1.1 --phases recon

  # 生成HTML报告
  python main.py --target 192.168.1.1 --report html
        """
    )

    # 目标参数
    parser.add_argument(
        "-t", "--target",
        type=str,
        help="目标IP、域名或URL"
    )

    # 运行模式
    parser.add_argument(
        "-m", "--mode",
        type=str,
        choices=["auto", "semi", "manual"],
        default="auto",
        help="运行模式: auto(自动), semi(半自动), manual(手动)"
    )

    # LLM配置
    parser.add_argument(
        "--model",
        type=str,
        choices=["deepseek", "glm", "qwen", "openai"],
        default="deepseek",
        help="LLM提供商"
    )

    parser.add_argument(
        "--api-key",
        type=str,
        help="API密钥（或通过环境变量设置）"
    )

    # 测试阶段
    parser.add_argument(
        "--phases",
        type=str,
        nargs="+",
        choices=["recon", "vuln", "exploit", "report"],
        default=["recon", "vuln", "exploit", "report"],
        help="要执行的测试阶段"
    )

    # 报告格式
    parser.add_argument(
        "--report",
        type=str,
        choices=["json", "html", "markdown"],
        default="json",
        help="报告输出格式"
    )

    # 输出目录
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="./results",
        help="结果输出目录"
    )

    # 配置文件
    parser.add_argument(
        "-c", "--config",
        type=str,
        default="config.yaml",
        help="配置文件路径"
    )

    # 交互模式
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="启动交互模式"
    )

    # 详细输出
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出模式"
    )

    # 检查依赖
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="检查依赖工具"
    )

    return parser.parse_args()


def check_environment():
    """检查运行环境"""
    console.print("\n[bold]检查运行环境...[/bold]\n")

    # 检查Python版本
    py_version = sys.version_info
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 8):
        console.print("[red]错误: 需要Python 3.8或更高版本[/red]")
        return False

    console.print(f"[green]✓[/green] Python版本: {py_version.major}.{py_version.minor}")

    # 检查依赖工具
    deps = check_dependencies()
    table = Table(title="工具依赖检查")
    table.add_column("工具", style="cyan")
    table.add_column("状态", style="magenta")

    for tool, available in deps.items():
        status = "[green]已安装[/green]" if available else "[yellow]未安装[/yellow]"
        table.add_row(tool, status)

    console.print(table)

    # 检查配置文件
    if not os.path.exists("config.yaml"):
        console.print("[yellow]⚠ 警告: config.yaml 不存在，将使用默认配置[/yellow]")

    return True


def run_auto_mode(
    target: str,
    orchestrator: Orchestrator,
    phases: List[str],
    report_format: str
):
    """
    运行自动模式

    Args:
        target: 目标
        orchestrator: 编排器实例
        phases: 执行阶段
        report_format: 报告格式
    """
    console.print(f"\n[bold cyan]开始自动渗透测试[/bold cyan]")
    console.print(f"[dim]目标: {target}[/dim]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # 执行测试
        task = progress.add_task("执行渗透测试...", total=None)

        result = orchestrator.run_test(
            target=target,
            mode="auto",
            phases=phases
        )

        progress.remove_task(task)

    # 显示结果
    display_results(result)

    # 生成报告
    if "report" in phases:
        save_report(result, report_format)


def display_results(result: dict):
    """显示测试结果"""
    console.print("\n" + "="*60)
    console.print("[bold green]测试完成[/bold green]")
    console.print("="*60 + "\n")

    # 基本信息
    console.print(Panel(
        f"目标: {result.get('target', 'Unknown')}\n"
        f"状态: {result.get('status', 'Unknown')}\n"
        f"开始时间: {result.get('start_time', 'Unknown')}\n"
        f"结束时间: {result.get('end_time', 'Unknown')}",
        title="测试概览",
        border_style="blue"
    ))

    # 信息收集结果
    recon_data = result.get("results", {}).get("recon", {}).get("data", {})
    if recon_data:
        console.print("\n[bold]📡 信息收集结果[/bold]")

        # 开放端口
        ports = recon_data.get("results", {}).get("open_ports", [])
        if ports:
            table = Table(title="开放端口")
            table.add_column("端口", style="cyan")
            table.add_column("服务", style="green")
            table.add_column("版本", style="yellow")

            for port in ports[:15]:
                table.add_row(
                    str(port.get("port", "N/A")),
                    port.get("service", "unknown"),
                    port.get("version", "N/A")
                )

            console.print(table)

    # 漏洞发现
    vuln_data = result.get("results", {}).get("vuln", {}).get("data", {})
    if vuln_data:
        vulns = vuln_data.get("vulnerabilities", [])
        if vulns:
            console.print(f"\n[bold red]🚨 发现 {len(vulns)} 个漏洞[/bold red]")

            table = Table(title="漏洞列表")
            table.add_column("漏洞名称", style="red")
            table.add_column("严重程度", style="yellow")
            table.add_column("CVE", style="cyan")

            for vuln in vulns[:10]:
                severity = vuln.get("severity", "low").lower()
                severity_color = {
                    "critical": "bold red",
                    "high": "red",
                    "medium": "yellow",
                    "low": "blue"
                }.get(severity, "white")

                table.add_row(
                    vuln.get("name", "Unknown")[:40],
                    f"[{severity_color}]{severity.upper()}[/{severity_color}]",
                    vuln.get("cve", "N/A")
                )

            console.print(table)

    # 利用结果
    exploit_data = result.get("results", {}).get("exploit", {}).get("data", {})
    if exploit_data:
        successful = exploit_data.get("results", {}).get("successful", [])
        if successful:
            console.print(f"\n[bold green]⚡ 成功利用 {len(successful)} 个漏洞[/bold green]")

            for exp in successful:
                console.print(f"  ✓ {exp.get('step', 'Unknown')}")

    # 错误信息
    errors = result.get("errors", [])
    if errors:
        console.print(f"\n[bold red]错误信息:[/bold red]")
        for error in errors:
            console.print(f"  ✗ {error}")


def save_report(result: dict, format: str):
    """保存报告"""
    console.print(f"\n[bold]📄 生成报告 ({format})...[/bold]")

    generator = ReportGenerator({"results_dir": "./results"})
    content = generator.generate(result, format)

    filename = f"pentest_report_{result.get('session_id', 'unknown')}"
    filepath = generator.save_report(content, filename, format)

    console.print(f"[green]✓ 报告已保存: {filepath}[/green]")


def interactive_mode(config: dict):
    """
    交互模式

    Args:
        config: 配置字典
    """
    console.clear()
    print_banner()

    console.print("\n[bold cyan]欢迎使用 AI-Pentest 交互模式[/bold cyan]")
    console.print("[dim]输入 'help' 查看可用命令[/dim]\n")

    # 初始化模型配置管理器
    from core.model_config import get_model_config_manager
    results_dir = config.get("system", {}).get("results_dir", "./results")
    model_config_file = os.path.join(results_dir, "model_config.json")
    model_config_manager = get_model_config_manager(model_config_file)
    
    orchestrator = Orchestrator(config, model_config_manager)

    while True:
        try:
            command = Prompt.ask("\n[bold blue]AI-Pentest[/bold blue]").strip().lower()

            if not command:
                continue

            # 退出
            if command in ["exit", "quit", "q"]:
                console.print("\n[yellow]再见！[/yellow]")
                break

            # 帮助
            elif command == "help":
                show_help()

            # 检查环境
            elif command == "check":
                check_environment()

            # 设置目标
            elif command.startswith("target "):
                target = command[7:].strip()
                if validate_target(target)["valid"]:
                    console.print(f"[green]目标已设置: {target}[/green]")
                else:
                    console.print("[red]无效的目标格式[/red]")

            # 运行测试
            elif command.startswith("run "):
                target = command[4:].strip()
                if validate_target(target)["valid"]:
                    run_auto_mode(target, orchestrator, ["recon", "vuln", "exploit", "report"], "json")
                else:
                    console.print("[red]请先设置有效目标[/red]")

            # 信息收集
            elif command.startswith("recon "):
                target = command[6:].strip()
                if validate_target(target)["valid"]:
                    result = orchestrator.run_phase("recon", target)
                    console.print(f"\n[green]信息收集完成[/green]")
                    console.print_json(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
                else:
                    console.print("[red]无效的目标[/red]")

            # 漏洞扫描
            elif command.startswith("vuln "):
                target = command[5:].strip()
                if validate_target(target)["valid"]:
                    result = orchestrator.run_phase("vuln", target)
                    console.print(f"\n[green]漏洞分析完成[/green]")
                    console.print_json(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
                else:
                    console.print("[red]无效的目标[/red]")

            # 查看会话
            elif command == "sessions":
                sessions = orchestrator.list_sessions()
                if sessions:
                    table = Table(title="测试会话")
                    table.add_column("会话ID", style="cyan")
                    table.add_column("目标", style="green")
                    table.add_column("状态", style="yellow")

                    for session in sessions:
                        table.add_row(
                            session["session_id"],
                            session["target"],
                            session["status"]
                        )

                    console.print(table)
                else:
                    console.print("[yellow]暂无测试会话[/yellow]")

            # 查看工具
            elif command == "tools":
                tools = orchestrator.tool_manager.list_available_tools()
                table = Table(title="可用工具")
                table.add_column("工具名称", style="cyan")
                table.add_column("状态", style="green")
                table.add_column("版本", style="yellow")

                for tool in tools:
                    status = "[green]可用[/green]" if tool["status"] == "available" else "[red]不可用[/red]"
                    table.add_row(tool["name"], status, tool.get("version", "N/A"))

                console.print(table)

            # 清屏
            elif command == "clear":
                console.clear()

            else:
                console.print(f"[red]未知命令: {command}[/red]")
                console.print("[dim]输入 'help' 查看可用命令[/dim]")

        except KeyboardInterrupt:
            console.print("\n[yellow]使用 'exit' 退出[/yellow]")
        except Exception as e:
            console.print(f"[red]错误: {str(e)}[/red]")


def show_help():
    """显示帮助信息"""
    help_text = """
[bold]可用命令:[/bold]

[cyan]目标设置[/cyan]
  target <ip/domain>    设置测试目标
  run <target>          对指定目标运行完整测试

[cyan]测试阶段[/cyan]
  recon <target>        执行信息收集
  vuln <target>         执行漏洞分析

[cyan]信息查看[/cyan]
  sessions              查看所有测试会话
  tools                 查看可用工具
  check                 检查运行环境

[cyan]其他[/cyan]
  clear                 清屏
  help                  显示此帮助
  exit/quit             退出程序

[bold]示例:[/bold]
  target 192.168.1.1
  run 192.168.1.1
  recon example.com
"""
    console.print(Panel(help_text, title="帮助", border_style="blue"))


def main():
    """主函数"""
    args = parse_args()

    # 检查依赖模式
    if args.check_deps:
        check_environment()
        return

    # 初始化配置
    config = load_config(args.config)

    # 覆盖配置
    if args.api_key:
        llm_provider = args.model
        if "api_keys" not in config.get("llm", {}):
            config["llm"]["api_keys"] = {}
        config["llm"]["api_keys"][llm_provider] = args.api_key

    if args.model:
        config["llm"]["provider"] = args.model

    if args.output:
        config["system"]["results_dir"] = args.output

    # 初始化日志
    global logger
    logger = get_logger(
        level="DEBUG" if args.verbose else "INFO",
        log_file=config.get("system", {}).get("log_file")
    )

    # 交互模式
    if args.interactive:
        interactive_mode(config)
        return

    # 命令行模式
    if not args.target:
        console.print("[red]错误: 请指定目标 (-t/--target)[/red]")
        console.print("[dim]使用 --help 查看帮助[/dim]")
        sys.exit(1)

    # 验证目标
    validation = validate_target(args.target)
    if not validation["valid"]:
        console.print(f"[red]错误: 无效的目标格式 '{args.target}'[/red]")
        sys.exit(1)

    # 打印Banner
    print_banner()

    # 检查环境
    if not check_environment():
        sys.exit(1)

    # 初始化模型配置管理器
    from core.model_config import get_model_config_manager
    results_dir = config.get("system", {}).get("results_dir", "./results")
    model_config_file = os.path.join(results_dir, "model_config.json")
    model_config_manager = get_model_config_manager(model_config_file)

    # 初始化编排器
    orchestrator = Orchestrator(config, model_config_manager)

    # 运行测试
    run_auto_mode(
        args.target,
        orchestrator,
        args.phases,
        args.report
    )


if __name__ == "__main__":
    main()
