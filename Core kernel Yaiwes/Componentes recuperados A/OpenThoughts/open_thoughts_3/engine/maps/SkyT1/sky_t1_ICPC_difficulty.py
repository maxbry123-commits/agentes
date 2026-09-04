from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap

GRADING_PROMPT = " \
  You will be given a code problem. Your job is to grade the difficulty level from 1-10 according to the ICPC standard. \
  Here is the standard: \
  {criteria} \
  Problem to be labeled: {problem}."

ICPC_CRITERIA = """
    A 10-point scale for ICPC problems could be structured as follows, where level 1 represents the easiest problems and level 10 represents the most challenging:
    Level 1: Basic implementation problems requiring simple input/output handling and straightforward calculations. Typically solvable with a single loop or basic conditional statements. Examples include summing numbers or finding the maximum in an array.
    Level 2: Problems involving basic data structures like arrays and strings, requiring simple algorithms like linear search or basic sorting. May include simple mathematical concepts like prime numbers or basic geometry.
    Level 3: Problems requiring knowledge of standard algorithms like binary search, complete sorting algorithms, or basic graph traversal (DFS/BFS). May include simple dynamic programming problems with clear state transitions.
    Level 4: Problems combining multiple basic concepts, requiring careful implementation and moderate optimization. Includes medium-difficulty dynamic programming problems and basic graph algorithms like shortest paths.
    Level 5: Problems requiring solid understanding of data structures like segment trees, binary indexed trees, or disjoint set unions. May include more complex graph algorithms like minimum spanning trees or network flow basics.
    Level 6: Advanced dynamic programming problems with non-obvious state representations. Problems requiring combination of multiple algorithms or data structures. May include basic game theory or basic number theory concepts.
    Level 7: Problems requiring advanced algorithmic knowledge like heavy-light decomposition, suffix arrays, or advanced geometric algorithms. Includes complex optimization problems and harder network flow applications.
    Level 8: Problems requiring deep mathematical insights combined with complex algorithmic implementations. May include advanced number theory, complex geometric algorithms, or problems requiring multiple non-obvious observations.
    Level 9: Problems requiring extensive knowledge of advanced algorithms and mathematical concepts, often needing multiple key insights to solve. May include advanced string algorithms like suffix automata, or complex mathematical optimizations.
    Level 10: The most challenging problems, often requiring novel approaches or insights not covered in standard competitive programming material. These problems might combine multiple advanced concepts in non-obvious ways, require complex proofs for correctness, or need highly optimized implementations to meet strict time limits.
    This scale corresponds roughly to the difficulty progression you might see from early regional contests (levels 1-4) through regional finals (levels 4-7) to world finals problems (levels 7-10).
"""

class DifficultyResult(BaseModel):
    """Result of the judge's evaluation."""

    difficulty: int
    reasoning: str


class SkyT1ICPCDifficultyMapConfig(BaseModel):
    problem_column: str
    output_difficulty_column: str
    output_reasoning_column: str


class SkyT1ICPCDifficultyMap(CompletionsMap):
    """Curator class for processing Numina dataset."""

    def __init__(self, config: dict):
        config = SkyT1ICPCDifficultyMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A string that describes the format of the response from the completions model via Pydantic
        """
        return DifficultyResult

    def prompt(self, input):
        """Create a prompt for the LLM to estimate the difficulty of a problem."""

        prompt = {
            GRADING_PROMPT.format(
                criteria=ICPC_CRITERIA, problem=input[self.config.problem_column]
            )
        }

        return [
            {"role": "system", "content": "You are a code problem difficulty labeler."},
            {"role": "user", "content": prompt},
        ]

    def parse(self, input, response):
        """Parse the judge's response to extract correctness and reasoning."""
        return {
            **input,
            self.config.output_difficulty_column: response.difficulty,
            self.config.output_reasoning_column: response.reasoning,
        }