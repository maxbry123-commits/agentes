"""
Main orchestrator — drives the kill chain state machine
and coordinates all phase agents.
"""

import logging
import time
from typing import Optional
from anthropic import Anthropic
from src.state import AgentState, Phase
from src.tools.executor import ToolExecutor
from src.memory.findings import FindingsStore
from src.agents.recon import ReconAgent
from src.agents.enumeration import EnumerationAgent
from src.agents.exploit import ExploitAgent
from src.agents.privesc import PrivescAgent
from src.reporting.reporter import Reporter
from src.validation.validator import Validator, ValidationResult

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Top-level controller that drives the autonomous pentest workflow.
    
    Manages:
    - Kill chain phase transitions
    - Agent instantiation and execution
    - State persistence between phases
    - Final reporting and validation
    """

    def __init__(
        self,
        target_ip: str,
        machine_name: str,
        anthropic_api_key: str,
        attacker_ip: str = "10.10.14.1",
        model: str = "claude-sonnet-4-20250514",
        machine_config_path: Optional[str] = None,
        require_confirmation: bool = True,
        dry_run: bool = False,
        command_timeout: int = 120,
        max_total_commands: int = 50,
    ):
        self.target_ip = target_ip
        self.machine_name = machine_name
        self.attacker_ip = attacker_ip
        self.model = model
        self.machine_config_path = machine_config_path
        self.max_total_commands = max_total_commands

        # Initialize core components
        self.client = Anthropic(api_key=anthropic_api_key)
        self.executor = ToolExecutor(
            timeout=command_timeout,
            require_confirmation=require_confirmation,
            dry_run=dry_run,
        )
        self.findings = FindingsStore()
        self.state = AgentState(
            target_ip=target_ip,
            machine_name=machine_name,
        )

        # Initialize phase agents
        self.agents = {
            Phase.RECON: ReconAgent(
                client=self.client,
                executor=self.executor,
                findings=self.findings,
                model=self.model,
                max_commands=8,
            ),
            Phase.ENUMERATION: EnumerationAgent(
                client=self.client,
                executor=self.executor,
                findings=self.findings,
                model=self.model,
                max_commands=12,
            ),
            Phase.EXPLOIT: ExploitAgent(
                client=self.client,
                executor=self.executor,
                findings=self.findings,
                model=self.model,
                max_commands=15,
                attacker_ip=attacker_ip,
            ),
            Phase.PRIVESC: PrivescAgent(
                client=self.client,
                executor=self.executor,
                findings=self.findings,
                model=self.model,
                max_commands=12,
                attacker_ip=attacker_ip,
            ),
        }

        logger.info(f"Orchestrator initialized for {machine_name} ({target_ip})")

    def run(self) -> AgentState:
        """
        Execute the full autonomous pentest workflow.
        
        Returns the final AgentState with all results.
        """
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        console = Console()

        console.print(Panel(
            f"[bold red]AUTONOMOUS PENTEST AGENT[/bold red]\n"
            f"Target: [bold]{self.target_ip}[/bold] ({self.machine_name})\n"
            f"Model: {self.model}\n"
            f"Attacker IP: {self.attacker_ip}",
            title="🔴 Initializing",
            border_style="red",
        ))

        # Advance from INIT to RECON
        self.state.current_phase = Phase.RECON

        # Run each phase in sequence
        phase_order = [Phase.RECON, Phase.ENUMERATION, Phase.EXPLOIT, Phase.PRIVESC]

        for phase in phase_order:
            if self.state.total_commands >= self.max_total_commands:
                console.print(f"\n[yellow]⚠️  Maximum command limit ({self.max_total_commands}) reached. Stopping.[/yellow]")
                break

            console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
            console.print(f"[bold cyan]  PHASE: {phase.value.upper()}[/bold cyan]")
            console.print(f"[bold cyan]{'='*60}[/bold cyan]")

            agent = self.agents.get(phase)
            if not agent:
                logger.warning(f"No agent for phase {phase.value}, skipping.")
                continue

            self.state.current_phase = phase
            start_time = time.time()

            try:
                result = agent.run(self.state)
                result.duration_seconds = time.time() - start_time
                self.state.advance_phase(result)

                # Display phase result
                status = "[green]SUCCESS[/green]" if result.success else "[red]FAILED[/red]"
                console.print(f"\n  Phase Result: {status}")
                console.print(f"  Commands Run: {len(result.commands_run)}")
                console.print(f"  Duration: {result.duration_seconds:.1f}s")
                if result.findings:
                    console.print(f"  Key Findings:")
                    for finding in result.findings[:5]:  # Show top 5
                        console.print(f"    • {finding}")

                # Check if we should skip privesc (e.g., Lame gives root directly)
                if phase == Phase.EXPLOIT and self.state.flags.get("root"):
                    console.print("\n[green]🏆 Root flag already captured! Skipping privesc.[/green]")
                    break

                if not result.success and phase in (Phase.EXPLOIT,):
                    console.print(f"\n[yellow]⚠️  {phase.value} failed. Attempting to continue...[/yellow]")
                    # Could implement retry logic or phase fallback here

            except Exception as e:
                logger.error(f"Phase {phase.value} crashed: {e}", exc_info=True)
                console.print(f"\n[red]💥 Phase {phase.value} crashed: {e}[/red]")
                continue

        # Final summary
        self._print_final_summary(console)

        return self.state

    def _print_final_summary(self, console) -> None:
        """Print the final engagement summary."""
        from rich.table import Table

        console.print(f"\n\n{'='*60}")
        console.print("[bold]ENGAGEMENT COMPLETE[/bold]")
        console.print(f"{'='*60}\n")

        table = Table(title="Results Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Total Commands", str(self.state.total_commands))
        table.add_row("Phases Completed", str(len(self.state.phases_completed)))
        table.add_row("Open Ports", str(len(self.state.open_ports)))
        table.add_row("Vulnerabilities", str(len(self.state.vulnerabilities)))
        table.add_row("Shells", str(len(self.state.shells)))
        table.add_row(
            "User Flag",
            f"[green]✅ {self.state.flags['user']}[/green]" if self.state.flags.get("user")
            else "[red]❌ Not captured[/red]"
        )
        table.add_row(
            "Root Flag",
            f"[green]✅ {self.state.flags['root']}[/green]" if self.state.flags.get("root")
            else "[red]❌ Not captured[/red]"
        )

        console.print(table)

    def generate_report(self, output_dir: str = "output") -> str:
        """Generate and save all reports."""
        import os
        os.makedirs(output_dir, exist_ok=True)

        reporter = Reporter(self.state, self.findings)

        # Run validation if machine config is available
        validation = None
        if self.machine_config_path:
            try:
                validator = Validator(self.machine_config_path)
                validation = validator.validate(self.state, self.findings)
                logger.info(f"Validation score: {validation.percentage:.1f}%")
            except Exception as e:
                logger.error(f"Validation failed: {e}")

        # Save text report
        report_path = os.path.join(output_dir, f"{self.machine_name.lower()}_report.txt")
        reporter.save_report(report_path, validation)

        # Save JSON data
        json_path = os.path.join(output_dir, f"{self.machine_name.lower()}_data.json")
        reporter.save_json(json_path)

        # Print validation results
        if validation:
            from rich.console import Console
            Console().print(validation.generate_report())

        return report_path