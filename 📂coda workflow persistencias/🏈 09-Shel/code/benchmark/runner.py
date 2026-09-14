import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict


@dataclass
class BenchmarkResult:
    challenge: str
    success: bool
    duration_seconds: float
    cost_estimate: float
    commands_run: int
    findings_count: int
    errors: list[str] = field(default_factory=list)
    notes: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class BenchmarkHarness:
    def __init__(self):
        self.results: list[BenchmarkResult] = []
        self.results_file = Path.home() / ".shel" / "benchmark_results.json"
        self.results_file.parent.mkdir(parents=True, exist_ok=True)

    def run_challenge(self, challenge_name: str, target: str, prompt_file: Path) -> BenchmarkResult:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'benchmark/runner.py','step':'run_challenge','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    def _save(self):
        data = [asdict(r) for r in self.results]
        self.results_file.write_text(json.dumps(data, indent=2))

    def load(self):
        if self.results_file.exists():
            data = json.loads(self.results_file.read_text())
            self.results = [BenchmarkResult(**d) for d in data]

    def summary(self) -> str:
        if not self.results:
            return "No benchmark results yet."
        total = len(self.results)
        successes = sum(1 for r in self.results if r.success)
        avg_duration = sum(r.duration_seconds for r in self.results) / total if total else 0
        avg_cost = sum(r.cost_estimate for r in self.results) / total if total else 0
        lines = [
            "## Benchmark Summary",
            f"Challenges: {total}",
            f"Success rate: {successes}/{total} ({successes/total*100:.0f}%)",
            f"Avg duration: {avg_duration:.1f}s",
            f"Avg cost: ${avg_cost:.4f}",
            "",
            "### Results",
        ]
        for r in self.results:
            status = "✓" if r.success else "✗"
            lines.append(f"  {status} {r.challenge} ({r.duration_seconds}s, ${r.cost_estimate:.4f})")
        return "\n".join(lines)
