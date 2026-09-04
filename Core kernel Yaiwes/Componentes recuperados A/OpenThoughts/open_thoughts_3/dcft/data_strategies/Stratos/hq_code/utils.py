import ast
import json
import urllib
from typing import List


def get_domain(url):
    return urllib.parse.urlparse(url).netloc


def parse_input_output(x):
    try:
        return json.loads(x)
    except:
        return {}


def parse_solutions(x):
    try:
        return len(json.loads(x))
    except:
        return 0


def apps_process_solutions(solutions: str) -> List[str]:
    # print(type(solutions))

    if isinstance(solutions, str):
        try:
            solutions = json.loads(solutions)
        except:
            # print(solutions)
            try:
                solutions = ast.literal_eval(solutions)
            except:
                solutions = []

    return solutions
