from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap

GRADING_PROMPT = " \
  You will be given a math problem. Your job is to grade the difficulty level from 1-10 according to the AoPS standard. \
  Here is the standard: \
  {aops_criteria} \
  Problem to be labeled: {problem}."

AOPS_CRITERIA = " \
  All levels are estimated and refer to averages. The following is a rough standard based on the USA tier system AMC 8 - AMC 10 - AMC 12 - AIME - USAMO/USAJMO - IMO, \
  representing Middle School - Junior High - High School - Challenging High School - Olympiad levels. Other contests can be interpolated against this. \
  Notes: \
  Multiple choice tests like AMC are rated as though they are free-response. Test-takers can use the answer choices as hints, and so correctly answer more AMC questions than Mathcounts or AIME problems of similar difficulty. \
  Some Olympiads are taken in 2 sessions, with 2 similarly difficult sets of questions, numbered as one set. For these the first half of the test (questions 1-3) is similar difficulty to the second half (questions 4-6). \
  Scale \
  1: Problems strictly for beginner, on the easiest elementary school or middle school levels (MOEMS, MATHCOUNTS Chapter, AMC 8 1-20, AMC 10 1-10, AMC 12 1-5, and others that involve standard techniques introduced up to the middle school level), most traditional middle/high school word problems. \
  2: For motivated beginners, harder questions from the previous categories (AMC 8 21-25, harder MATHCOUNTS States questions, AMC 10 11-20, AMC 12 5-15, AIME 1-3), traditional middle/high school word problems with extremely complex problem solving. \
  3: Advanced Beginner problems that require more creative thinking (harder MATHCOUNTS National questions, AMC 10 21-25, AMC 12 15-20, AIME 4-6). \
  4: Intermediate-level problems (AMC 12 21-25, AIME 7-9). \
  5: More difficult AIME problems (10-12), simple proof-based Olympiad-style problems (early JBMO questions, easiest USAJMO 1/4). \
  6: High-leveled AIME-styled questions (13-15). Introductory-leveled Olympiad-level questions (harder USAJMO 1/4 and easier USAJMO 2/5, easier USAMO and IMO 1/4). \
  7: Tougher Olympiad-level questions, may require more technical knowledge (harder USAJMO 2/5 and most USAJMO 3/6, extremely hard USAMO and IMO 1/4, easy-medium USAMO and IMO 2/5). \
  8: High-level Olympiad-level questions (medium-hard USAMO and IMO 2/5, easiest USAMO and IMO 3/6). \
  9: Expert Olympiad-level questions (average USAMO and IMO 3/6). \
  10: Historically hard problems, generally unsuitable for very hard competitions (such as the IMO) due to being exceedingly tedious, long, and difficult (e.g. very few students are capable of solving on a worldwide basis). \
  Examples \
  For reference, here are problems from each of the difficulty levels 1-10: \
  <1: Jamie counted the number of edges of a cube, Jimmy counted the numbers of corners, and Judy counted the number of faces. They then added the three numbers. What was the resulting sum? (2003 AMC 8, Problem 1) \
  1: How many integer values of $x$ satisfy $|x| < 3\pi$? (2021 Spring AMC 10B, Problem 1) \
  2: A fair $6$-sided die is repeatedly rolled until an odd number appears. What is the probability that every even number appears at least once before the first occurrence of an odd number? (2021 Spring AMC 10B, Problem 18) \
  3: Triangle $ABC$ with $AB=50$ and $AC=10$ has area $120$. Let $D$ be the midpoint of $\overline{AB}$, and let $E$ be the midpoint of $\overline{AC}$. The angle bisector of $\angle BAC$ intersects $\overline{DE}$ and $\overline{BC}$ at $F$ and $G$, respectively. What is the area of quadrilateral $FDBG$? (2018 AMC 10A, Problem 24) \
  4: Define a sequence recursively by $x_0=5$ and\[x_{n+1}=\frac{x_n^2+5x_n+4}{x_n+6}\]for all nonnegative integers $n.$ Let $m$ be the least positive integer such that\[x_m\leq 4+\frac{1}{2^{20}}.\]In which of the following intervals does $m$ lie? \
  $\textbf{(A) } [9,26] \qquad\textbf{(B) } [27,80] \qquad\textbf{(C) } [81,242]\qquad\textbf{(D) } [243,728] \qquad\textbf{(E) } [729,\infty)$ \
  (2019 AMC 10B, Problem 24 and 2019 AMC 12B, Problem 22) \
  5: Find all triples $(a, b, c)$ of real numbers such that the following system holds:\[a+b+c=\frac{1}{a}+\frac{1}{b}+\frac{1}{c},\]\[a^2+b^2+c^2=\frac{1}{a^2}+\frac{1}{b^2}+\frac{1}{c^2}.\](JBMO 2020/1) \
  6: Let $\triangle ABC$ be an acute triangle with circumcircle $\omega,$ and let $H$ be the intersection of the altitudes of $\triangle ABC.$ Suppose the tangent to the circumcircle of $\triangle HBC$ at $H$ intersects $\omega$ at points $X$ and $Y$ with $HA=3,HX=2,$ and $HY=6.$ The area of $\triangle ABC$ can be written in the form $m\sqrt{n},$ where $m$ and $n$ are positive integers, and $n$ is not divisible by the square of any prime. Find $m+n.$ (2020 AIME I, Problem 15) \
  7: We say that a finite set $\mathcal{S}$ in the plane is balanced if, for any two different points $A$, $B$ in $\mathcal{S}$, there is a point $C$ in $\mathcal{S}$ such that $AC=BC$. We say that $\mathcal{S}$ is centre-free if for any three points $A$, $B$, $C$ in $\mathcal{S}$, there is no point $P$ in $\mathcal{S}$ such that $PA=PB=PC$. \
  Show that for all integers $n\geq 3$, there exists a balanced set consisting of $n$ points. \
  Determine all integers $n\geq 3$ for which there exists a balanced centre-free set consisting of $n$ points. \
  (IMO 2015/1) \
  8: For each positive integer $n$, the Bank of Cape Town issues coins of denomination $\frac1n$. Given a finite collection of such coins (of not necessarily different denominations) with total value at most most $99+\frac{1}{2}$, prove that it is possible to split this collection into $100$ or fewer groups, such that each group has total value at most $1$. (IMO 2014/5) \
  9: Let $k$ be a positive integer and let $S$ be a finite set of odd prime numbers. Prove that there is at most one way (up to rotation and reflection) to place the elements of $S$ around the circle such that the product of any two neighbors is of the form $x^2+x+k$ for some positive integer $x$. (IMO 2022/3) \
  10: Prove that there exists a positive constant $c$ such that the following statement is true: Consider an integer $n > 1$, and a set $\mathcal S$ of $n$ points in the plane such that the distance between any two different points in $\mathcal S$ is at least 1. It follows that there is a line $\ell$ separating $\mathcal S$ such that the distance from any point of $\mathcal S$ to $\ell$ is at least $cn^{-1/3}$. \
  (A line $\ell$ separates a set of points S if some segment joining two points in $\mathcal S$ crosses $\ell$.) (IMO 2020/6)"


class DifficultyResult(BaseModel):
    """Result of the judge's evaluation."""

    difficulty: int
    reasoning: str


class SkyT1MathDifficultyMapConfig(BaseModel):
    problem_column: str
    output_difficulty_column: str
    output_reasoning_column: str


class SkyT1MathDifficultyMap(CompletionsMap):
    """Curator class for processing Numina dataset."""

    def __init__(self, config: dict):
        config = SkyT1MathDifficultyMapConfig(**config)
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
                aops_criteria=AOPS_CRITERIA, problem=input[self.config.problem_column]
            )
        }

        return [
            {"role": "system", "content": "You are a math problem difficulty labeler."},
            {"role": "user", "content": prompt},
        ]

    def parse(self, input, response):
        """Parse the judge's response to extract correctness and reasoning."""
        return {
            **input,
            self.config.output_difficulty_column: response.difficulty,
            self.config.output_reasoning_column: response.reasoning,
        }
