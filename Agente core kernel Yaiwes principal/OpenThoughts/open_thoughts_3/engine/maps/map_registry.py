from engine.maps.Airoboros.contextual_instructions_map import ContextualInstructionsMap
from engine.maps.Airoboros.counterfactual_contextual_instructions_map import (
    CounterfactualContextualInstructionsMap,
)
from engine.maps.Airoboros.experience_map import ExperienceMap
from engine.maps.Airoboros.list_qa_map import ListQAMap
from engine.maps.alpaca_map import AlpacaMap
from engine.maps.alpaca_seed_task_map import AlpacaSeedTaskMap
from engine.maps.AutoEvolInstruct.evol_llm_prompt import AutoEvolLLMMap
from engine.maps.AutoEvolInstruct.evol_prompt_evolver import EvolPromptEvolverMap
from engine.maps.AutoEvolInstruct.evol_trajectory_analysis import (
    AutoTrajectoryAnalysisLLMMap,
)
from engine.maps.Claude.claude_reasoner import ClaudeReasonerMap
from engine.maps.Grok.grok_reasoner import GrokReasonerMap
from engine.maps.TogetherQwen.together_qwen import TogetherQwenMap
from engine.maps.AutoVerification.code_verification import CodeSameMap
from engine.maps.AutoVerification.math_verification import MathSameMap
from engine.maps.AutoVerification.science_verification import ScienceSameMap
from engine.maps.binary_classifier_map import BinaryClassifierMap
from engine.maps.chat_map import ChatMap
from engine.maps.critic_map import CriticMap
from engine.maps.DeepSeekR1.code_golf_extractor import CodeGolfExtractorMap
from engine.maps.DeepSeekR1.deepseek_judge import DeepSeekJudgeMap
from engine.maps.DeepSeekR1.deepseek_reasoner import (
    DeepSeekReasonerMap,
    KlusterDeepSeekReasonerMap,
)
from engine.maps.fuser_map import FuserMap
from engine.maps.GeminiOCR.gemini_ocr import GeminiOCRMap
from engine.maps.generator_map import GeneratorMap
from engine.maps.judge_map import JudgeMap
from engine.maps.list_map import ListMap
from engine.maps.Metamath.extract_math_answer_map import ExtractMathAnswerMap
from engine.maps.Metamath.inverse_question_map import InverseQuestionMap
from engine.maps.Metamath.metamath_problem_generator import GenerateMathProblemMap
from engine.maps.Metamath.rephrase_question_map import RephraseQuestionMap
from engine.maps.Metamath.self_vertification_map import SelfVerificationMap
from engine.maps.Metamath.solve_inverse_map import SolveInverseMap
from engine.maps.Metamath.solve_rephrased_map import SolveRephraseMap
from engine.maps.open_gpt_map import OpenGPTMap
from engine.maps.ranker_map import RankerMap
from engine.maps.scorer_map import ScorerMap
from engine.maps.SkyT1.sky_t1_ICPC_difficulty import SkyT1ICPCDifficultyMap
from engine.maps.SkyT1.sky_t1_math_difficulty import SkyT1MathDifficultyMap
from engine.maps.SkyT1.sky_t1_science_difficulty import SkyT1ScienceDifficultyMap
from engine.maps.test_case_map import TestCaseMap
from engine.maps.unnatural_instructions_map import UnnaturalInstructionsMap
from engine.maps.WebInstruct.classify_educational_domain_map import (
    ClassifyEducationalDomainMap,
)
from engine.maps.WebInstruct.extract_qa_map import ExtractQAMap
from engine.maps.WebInstruct.revise_qa_map import ReviseQAMap
from engine.maps.WebInstruct.url_classify_map import URLClassifyMap

# from engine.maps.AutoEvolInstruct.evol
COMPLETIONS_MAPS = {
    "chat": ChatMap,
    "alpaca_seed": AlpacaSeedTaskMap,
    "list": ListMap,
    "auto_evol_llm": AutoEvolLLMMap,
    "auto_evol_prompt_evolver": EvolPromptEvolverMap,
    "auto_evol_trajectory_analysis": AutoTrajectoryAnalysisLLMMap,
    "sky_t1_math_difficulty": SkyT1MathDifficultyMap,
    "deepseek_judge": DeepSeekJudgeMap,
    "deepseek_reasoner": DeepSeekReasonerMap,
    "sky_t1_math_difficulty": SkyT1MathDifficultyMap,
    "test_cases": TestCaseMap,
    "code_golf_extractor": CodeGolfExtractorMap,
    "generator": GeneratorMap,
    "ranker": RankerMap,
    "code_same": CodeSameMap,
    "math_same": MathSameMap,
    "science_same": ScienceSameMap,
    "scorer": ScorerMap,
    "binary_classifier": BinaryClassifierMap,
    "fuser": FuserMap,
    "auto_evol_llm": AutoEvolLLMMap,
    "deepseek_reasoner": DeepSeekReasonerMap,
    "kluster_deepseek_reasoner": KlusterDeepSeekReasonerMap,
    "auto_evol_prompt_evolver": EvolPromptEvolverMap,
    "auto_evol_trajectory_analysis": AutoTrajectoryAnalysisLLMMap,
    "deepseek_judge": DeepSeekJudgeMap,
    "deepseek_reasoner": DeepSeekReasonerMap,
    "claude_reasoner": ClaudeReasonerMap,
    "grok_reasoner": GrokReasonerMap,
    "together_qwen": TogetherQwenMap,
    "sky_t1_math_difficulty": SkyT1MathDifficultyMap,
    "sky_t1_ICPC_difficulty": SkyT1ICPCDifficultyMap,
    "sky_t1_science_difficulty": SkyT1ScienceDifficultyMap,
    "url_classify": URLClassifyMap,
    "gemini_ocr": GeminiOCRMap,
    "judge": JudgeMap,
    "alpaca": AlpacaMap,
    "critic": CriticMap,
    "unnatural_instructions": UnnaturalInstructionsMap,
    "open_gpt": OpenGPTMap,
    "metamath_inverse_question": InverseQuestionMap,
    "metamath_extract_math_answer": ExtractMathAnswerMap,
    "metamath_problem_clone": GenerateMathProblemMap,
    "metamath_self_verification": SelfVerificationMap,
    "metamath_solve_inverse": SolveInverseMap,
    "metamath_rephrase_question": RephraseQuestionMap,
    "metamath_solve_rephrased": SolveRephraseMap,
    "counterfactual_contextual_instructions": CounterfactualContextualInstructionsMap,
    "contextual_instructions": ContextualInstructionsMap,
    "list_qa": ListQAMap,
    "experience": ExperienceMap,
    "webinstruct_classify_educational_domain": ClassifyEducationalDomainMap,
    "webinstruct_extract_qa": ExtractQAMap,
    "webinstruct_revise_qa": ReviseQAMap,
}
