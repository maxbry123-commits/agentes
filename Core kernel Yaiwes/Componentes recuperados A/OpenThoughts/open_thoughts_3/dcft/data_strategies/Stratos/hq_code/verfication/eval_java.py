import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from generic_eval import main
from safe_subprocess import run

LANG_NAME = "Java"
LANG_EXT = ".java"

# Following files have problems:
# 137,
# 22: Any
# 148: Elipsis


def eval_script(
    path: Path, test_inputs: List[str], test_outputs: List[str], main_class: str
) -> Dict[str, Any]:
    sys_env = os.environ.copy()
    javatuples_path = Path("/usr/multiple/javatuples-1.2.jar")

    sys_env["CLASSPATH"] = f"{javatuples_path}"

    with tempfile.TemporaryDirectory() as outdir:
        # Each Java file contains the class with same name `JAVA_CLASS_NAME`
        # Hence, javac will same JAVA_CLASS_NAME.class file for each problem
        # Write class for each problem to a different temp dir
        # Use UTF8 encoding with javac
        test_id = 0
        test_results = []
        for test_input, test_output in zip(test_inputs, test_outputs):
            test_id += 1
            result = run(
                ["javac", "-encoding", "UTF8", "-d", outdir, path],
                env=sys_env,
                input_str="",
            )

            if result.exit_code != 0:
                # Well, it's a compile error. May be a type error or
                # something. But, why break the set convention
                status = "SyntaxError"
            else:
                result = run(
                    ["java", "-ea", "-cp", f"{outdir}:{javatuples_path}", main_class],
                    env=sys_env,
                    input_str=test_input,
                )
                if result.timeout:
                    status = "Timeout"
                elif result.exit_code == 0:
                    output = result.stdout.decode().strip()
                    if output == test_output.strip():
                        status = "OK"
                    else:
                        status = "Wrong Answer"
                else:
                    status = "Exception"

            test_results.append(
                {
                    "test_id": test_id,
                    "status": status,
                    "exit_code": result.exit_code,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )

    return test_results


if __name__ == "__main__":
    main(eval_script, LANG_NAME, LANG_EXT)
