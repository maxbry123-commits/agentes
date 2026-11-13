from pathlib import Path
from typing import Any, Dict, List

from safe_subprocess import run


def eval_script(
    path: Path, test_inputs: List[str], test_outputs: List[str]
) -> Dict[str, Any]:
    test_id = 0
    test_results = []
    for test_input, test_output in zip(test_inputs, test_outputs):
        test_id += 1
        r = run(["python3", str(path)], input_str=test_input)
        if r.timeout:
            status = "Timeout"
        elif r.exit_code == 0:
            output = r.stdout.decode().strip()
            print("output:", output, "test_output:", test_output)
            if output == test_output.strip():
                status = "OK"
            else:
                status = "Wrong Answer"
        elif "SyntaxError" in r.stderr:
            status = "SyntaxError"
        else:
            status = "Exception"

        test_results.append(
            {
                "test_id": test_id,
                "status": status,
                "exit_code": r.exit_code,
                "stdout": r.stdout,
                "stderr": r.stderr,
            }
        )
    return test_results
