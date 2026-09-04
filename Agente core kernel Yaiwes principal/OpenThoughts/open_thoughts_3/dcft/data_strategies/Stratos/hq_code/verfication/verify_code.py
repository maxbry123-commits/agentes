import json
import os
import re
import tempfile
from pathlib import Path
from typing import Dict

from datasets import load_dataset
from eval_cpp import eval_script as eval_cpp
from eval_java import eval_script as eval_java
from eval_python import eval_script as eval_python
from eval_python2 import eval_script as eval_python2

EVAL_FUNCTIONS = {
    "CPP": eval_cpp,
    "JAVA": eval_java,
    "PYTHON3": eval_python,
    "PYTHON": eval_python2,
}

EXT = {
    "CPP": ".cpp",
    "JAVA": ".java",
    "PYTHON3": ".py",
    "PYTHON": ".py",
}


def map_languages(solutions: Dict[str, list]) -> dict:
    solutions_out = {"language": [], "solution": []}
    for language, solution in zip(solutions["language"], solutions["solution"]):
        language = code_contests_languages_map.get(str(language))
        solutions_out["language"].append(language)
        solutions_out["solution"].append(solution)
    return solutions_out


def create_temp_file(code: str, ext: str, filename: str = None) -> Path:
    if filename:
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, filename + ext)
        with open(temp_file, "wb") as f:
            f.write(code)
        temp_file_path = Path(temp_file)
    else:
        temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        temp_file.write(code)
        temp_file.close()
        temp_file_path = Path(temp_file.name)
    return temp_file_path


def extract_piublic_class(code: str) -> str:
    public_class = re.search(r"public class (\w+)", code)
    if public_class:
        return public_class.group(1)
    return None


def eval_script(row):
    results = []

    for solution, lang in zip(row["solutions"], row["language"]):
        if lang == "UNKNOWN_LANGUAGE":
            continue
        eval_func = EVAL_FUNCTIONS[lang]
        starter_code = row["starter_code"]
        test_code = starter_code + "\n" + solution
        ext = EXT[lang]
        filename = None
        if lang == "JAVA":
            public_class = extract_piublic_class(test_code)
            if public_class:
                filename = public_class
        temp_file = create_temp_file(test_code.encode(), ext, filename)
        test_inputs = row["test_cases"]["inputs"]
        test_outputs = row["test_cases"]["outputs"]
        if lang == "JAVA":
            result = eval_func(temp_file, test_inputs, test_outputs, public_class)
        else:
            result = eval_func(temp_file, test_inputs, test_outputs)
        try:
            os.remove(temp_file)
        except:
            pass
        results.append(result)
    return result


languges = ["UNKNOWN_LANGUAGE", "PYTHON", "CPP", "PYTHON3", "JAVA"]

code_contests_languages_map = {str(i): language for i, language in enumerate(languges)}

if __name__ == "__main__":
    dataset = load_dataset("mlfoundations-dev/code_contests_processed", split="all")
    dataset = dataset.take(10)
    dataset = dataset.map(
        lambda x: {
            "solutions_mapped": map_languages(x["solutions"]),
        },
        num_proc=8,
        remove_columns=["solutions"],
    )
    dataset = dataset.map(
        lambda x: {
            "language": x["solutions_mapped"]["language"],
            "solutions": x["solutions_mapped"]["solution"],
            "test_cases": json.loads(x["test_cases"]),
        },
        num_proc=8,
    )

    dataset = dataset.map(
        lambda x: {
            "results": eval_script(x),
        }
    )
