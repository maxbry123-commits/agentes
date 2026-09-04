from pathlib import Path
from typing import Any, Dict, List

from generic_eval import main
from safe_subprocess import run

LANG_NAME = "C++"
LANG_EXT = ".cpp"


def eval_script(
    path: Path, test_inputs: List[str], test_outputs: List[str]
) -> Dict[str, Any]:
    test_id = 0
    test_results = []
    for test_input, test_output in zip(test_inputs, test_outputs):
        test_id += 1
        basename = ".".join(str(path).split(".")[:-1])
        build_result = run(["g++", path, "-o", basename, "-std=c++17"], input_str="")
        if build_result.exit_code != 0:
            return {
                "status": "SyntaxError",
                "exit_code": build_result.exit_code,
                "stdout": build_result.stdout,
                "stderr": build_result.stderr,
            }

        run_result = run([basename], input_str=test_input)
        stderr = run_result.stderr.decode()

        if "In file included from /shared/centos7/gcc/9.2.0-skylake/" in stderr:
            raise Exception("Skylake bug encountered")
        if "/4.8.2" in stderr:
            raise Exception("Ancient compiler encountered")
        if run_result.timeout:
            status = "Timeout"
        elif run_result.exit_code != 0:
            status = "Exception"
        else:
            output = run_result.stdout.decode().strip()
            if output == test_output.strip():
                status = "OK"
            else:
                status = "Wrong Answer"

        test_results.append(
            {
                "test_id": test_id,
                "status": status,
                "exit_code": run_result.exit_code,
                "stdout": run_result.stdout,
                "stderr": run_result.stderr,
            }
        )
    return test_results


if __name__ == "__main__":
    main(eval_script, LANG_NAME, LANG_EXT)
