#!/usr/bin/env python3
"""
Autonomous Pentest Agent — Main Entry Point

Usage:
    # Against HTB Shocker (with confirmation prompts):
    python -m src.main --target 10.10.10.56 --machine shocker --attacker-ip 10.10.14.X

    # Against HTB Lame (dry run — no commands executed):
    python -m src.main --target 10.10.10.3 --machine lame --attacker-ip 10.10.14.X --dry-run

    # Full auto (no confirmation prompts — use with caution):
    python -m src.main --target 10.10.10.56 --machine shocker --attacker-ip 10.10.14.X --no-confirm
"""

import argparse
import logging
import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler

from src.orchestrator import Orchestrator


def setup_logging(level: str = "INFO") -> None:
    """Configure rich logging."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Autonomous Pentest Agent — Claude-powered penetration testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --target 10.10.10.56 --machine shocker --attacker-ip 10.10.14.5
  %(prog)s --target 10.10.10.3 --machine lame --attacker-ip 10.10.14.5 --dry-run
  %(prog)s --target 10.10.10.56 --machine shocker --attacker-ip 10.10.14.5 --no-confirm
        """,
    )

    parser.add_argument(
        "--target", "-t",
        required=True,
        help="Target IP address",
    )
    parser.add_argument(
        "--machine", "-m",
        required=True,
        choices=["shocker", "lame"],
        help="Machine profile to load (for validation)",
    )
    parser.add_argument(
        "--attacker-ip", "-a",
        required=True,
        help="Your attacker IP (tun0 interface on VPN)",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Anthropic model to use (default: claude-sonnet-4-20250514)",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Disable command confirmation prompts (full auto mode)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't execute any commands — just show what would run",
    )
    parser.add_argument(
        "--max-commands",
        type=int,
        default=50,
        help="Maximum total commands to execute (default: 50)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Per-command timeout in seconds (default: 120)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="output",
        help="Directory for reports and logs (default: output/)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    return parser.parse_args()


def main():
    load_dotenv()
    args = parse_args()
    setup_logging(args.log_level)
    console = Console()

    # Validate API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]❌ ANTHROPIC_API_KEY not set. Add it to .env or environment.[/red]")
        sys.exit(1)

    # Resolve machine config path
    machine_config = os.path.join("config", "machines", f"{args.machine}.yaml")
    if not os.path.exists(machine_config):
        console.print(f"[red]❌ Machine config not found: {machine_config}[/red]")
        sys.exit(1)

    # Safety warning for non-dry-run, no-confirm mode
    if args.no_confirm and not args.dry_run:
        console.print("\n[bold red]⚠️  FULL AUTO MODE — Commands will execute WITHOUT confirmation![/bold red]")
        console.print("[yellow]Make sure you are on the HTB VPN and targeting the correct machine.[/yellow]")
        confirm = input("Type 'YES' to continue: ").strip()
        if confirm != "YES":
            console.print("Aborted.")
            sys.exit(0)

    # Initialize and run
    orchestrator = Orchestrator(
        target_ip=args.target,
        machine_name=args.machine.capitalize(),
        anthropic_api_key=api_key,
        attacker_ip=args.attacker_ip,
        model=args.model,
        machine_config_path=machine_config,
        require_confirmation=not args.no_confirm,
        dry_run=args.dry_run,
        command_timeout=args.timeout,
        max_total_commands=args.max_commands,
    )

    try:
        state = orchestrator.run()
        report_path = orchestrator.generate_report(args.output_dir)
        console.print(f"\n[green]📄 Report saved to: {report_path}[/green]")
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Interrupted by user. Generating partial report...[/yellow]")
        report_path = orchestrator.generate_report(args.output_dir)
        console.print(f"\n[green]📄 Partial report saved to: {report_path}[/green]")
    except Exception as e:
        console.print(f"\n[red]💥 Fatal error: {e}[/red]")
        logging.exception("Fatal error")
        # Still try to save what we have
        try:
            report_path = orchestrator.generate_report(args.output_dir)
            console.print(f"\n[green]📄 Crash report saved to: {report_path}[/green]")
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()