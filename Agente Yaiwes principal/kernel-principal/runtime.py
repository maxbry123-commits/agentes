from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass


@dataclass
class JobResult:
    task_id: str
    status: str
    output: object = None
    error: str | None = None


class ParallelRuntime:
    def __init__(self, workers: int = 4):
        self.workers = workers

    def run(self, tasks, fn):
        results = []
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futures = {pool.submit(fn, t): t for t in tasks}
            for future in as_completed(futures):
                task = futures[future]
                try:
                    results.append(JobResult(task.task_id, "COMPLETED", future.result()))
                except Exception as e:
                    results.append(JobResult(task.task_id, "FAILED", error=repr(e)))
        return results
