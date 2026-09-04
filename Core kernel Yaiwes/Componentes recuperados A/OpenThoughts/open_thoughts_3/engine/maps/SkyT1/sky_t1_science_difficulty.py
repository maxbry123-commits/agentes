from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap

GRADING_PROMPT = " \
  You will be given a science problem. Your job is to grade the difficulty level from 1-10 according to the international science olympiad standard. \
  Here is the standard: \
  {science_criteria} \
  Problem to be labeled: {problem}."

SCIENCE_CRITERIA = """
    A 10-point scale for international science olympiad problems could be structured as follows, where level 1 represents the easiest problems and level 10 represents the most challenging:
    Level 1: Basic Knowledge Application - Straightforward recall of fundamental scientific facts and principles. Simple calculations requiring only basic formulas. Direct application of a single scientific concept. Problems typically solvable in 1-2 steps. Content typically covered in standard high school curriculum. Examples include identifying simple chemical compounds, basic circuit calculations, or classifying organisms.
    Level 2: Multi-Step Basic Applications - Problems requiring 2-3 distinct steps to solve. Application of multiple basic concepts within a single field. Basic data interpretation from graphs or tables. Simple laboratory techniques and measurements. Content typically found in advanced high school courses. Examples include stoichiometry calculations, basic kinematics problems, or analyzing simple biological processes.
    Level 3: Advanced Application of Standard Concepts - Integration of multiple scientific concepts. Moderate quantitative reasoning with multi-step calculations. Interpretation of experimental data requiring analytical thinking. Problems requiring deeper understanding beyond memorization. Typical of challenging high school science competition questions. Examples include problems combining thermodynamics and kinetics, multi-step mechanics problems, or ecological relationship analysis.
    Level 4: Early National Olympiad Level - Problems requiring specialized knowledge in specific scientific domains. Application of advanced concepts not typically covered in regular curriculum. Moderate laboratory techniques and experimental design understanding. Analytical thinking with non-obvious solution paths. Typical of early rounds in national science olympiads. Examples include chemical equilibrium problems with multiple variables, circuit analysis with non-ideal components, or molecular biology mechanisms.
    Level 5: National Olympiad Standard - Problems integrating concepts across multiple scientific domains. Creative application of standard principles in non-standard contexts. Analysis of complex experimental setups and data. Multiple conceptual hurdles requiring insight. Typical of national olympiad final rounds. Examples include complex organic synthesis pathways, non-ideal thermodynamic systems, or advanced genetics problems.
    Level 6: Advanced National/Early International Level - Problems requiring deep conceptual understanding beyond standard curriculum. Integration of theoretical knowledge with practical laboratory techniques. Creative problem-solving with multiple possible approaches. Application of mathematical models to complex scientific phenomena. Typical of international olympiad preparation camps. Examples include quantum mechanical models, complex biochemical pathways, or statistical analysis of biological systems.
    Level 7: International Olympiad Standard - Problems at the level of IChO, IPhO, or IBO theoretical examinations. Requires specialized knowledge combined with creative insight. Complex quantitative modeling of scientific phenomena. Integration of concepts across scientific disciplines. Multiple conceptual layers requiring systematic analysis. Examples include advanced spectroscopy interpretation, complex physical systems with multiple forces, or detailed biochemical mechanism analysis.
    Level 8: Advanced International Olympiad - Problems requiring both breadth and depth of scientific knowledge. Novel applications of scientific principles not typically taught. Sophisticated experimental design and analysis. Multiple solution pathways requiring evaluation and selection. Typical of challenging international olympiad problems. Examples include challenging quantum chemistry problems, advanced laboratory protocols with multiple variables, or complex evolutionary or ecological models.
    Level 9: Elite International Olympiad - Problems requiring exceptional scientific insight and creativity. Integration of cutting-edge scientific knowledge. Multiple conceptual breakthroughs needed for solution. Problems that challenge even the most talented students. Reserved for the most difficult questions in international competitions. Examples include novel applications of physical principles, complex multi-step synthesis with stereochemical considerations, or systems biology analysis.
    Level 10: Historically Challenging Problems - Problems of legendary difficulty in science competitions. Requires innovative approaches beyond standard methodologies. May integrate advanced university-level concepts. Problems that very few competitors worldwide can solve completely. Often remembered as particularly challenging in olympiad history. Examples include problems that required creation of new approaches or that stumped almost all participants in a given year.
    
    This scale corresponds roughly to the difficulty progression you might see from school science competitions (levels 1-3) through national selection rounds (levels 4-5) to international olympiad problems (levels 6-10).
    
    Subject-Specific Notes:
    Physics (IPhO): Levels 1-3 cover standard high school physics content (mechanics, electricity, thermodynamics); Levels 4-6 include advanced topics like wave optics, basic quantum physics, and non-ideal systems; Levels 7-10 incorporate university-level content including quantum mechanics, statistical physics, and relativity.
    
    Chemistry (IChO): Levels 1-3 cover basic inorganic, organic, and analytical chemistry concepts; Levels 4-6 include complex reaction mechanisms, advanced analytical methods, physical chemistry; Levels 7-10 incorporate sophisticated laboratory methods, quantum chemistry, and cutting-edge chemical concepts.
    
    Biology (IBO): Levels 1-3 cover basic cellular, molecular, and organismal biology; Levels 4-6 include advanced cellular processes, genetics, evolutionary biology, and ecology; Levels 7-10 incorporate complex experimental design, advanced biochemistry, systems biology, and bioinformatics.
"""

class DifficultyResult(BaseModel):
    """Result of the judge's evaluation."""

    difficulty: int
    reasoning: str


class SkyT1ScienceDifficultyMapConfig(BaseModel):
    problem_column: str
    output_difficulty_column: str
    output_reasoning_column: str


class SkyT1ScienceDifficultyMap(CompletionsMap):
    """Curator class for processing Numina dataset."""

    def __init__(self, config: dict):
        config = SkyT1ScienceDifficultyMapConfig(**config)
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

        prompt = {GRADING_PROMPT.format(science_criteria=SCIENCE_CRITERIA, problem=input[self.config.problem_column])}

        return [
            {"role": "system", "content": "You are a science problem difficulty labeler."},
            {"role": "user", "content": prompt},
        ]

    def parse(self, input, response):
        """Parse the judge's response to extract correctness and reasoning."""
        return {
            **input,
            self.config.output_difficulty_column: response.difficulty,
            self.config.output_reasoning_column: response.reasoning,
        }
