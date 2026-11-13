from typing import Dict

from constants import COLUMNS, code_contests_languages_map, code_contests_sources_map


def map_languages(solutions: Dict[str, list]) -> dict:
    solutions_out = {"language": [], "solution": []}
    for language, solution in zip(solutions["language"], solutions["solution"]):
        language = code_contests_languages_map.get(str(language))
        solutions_out["language"].append(language)
        solutions_out["solution"].append(solution)

    return solutions_out


def codecontests_map_sources(source: str) -> str:
    return code_contests_sources_map.get(str(source))


def codecontests_map_languages(language: str) -> str:
    return code_contests_languages_map.get(str(language))
