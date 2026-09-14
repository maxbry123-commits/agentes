"""Autonomous Evolution Engine — self-improving idle-time learning."""

from cognithor.evolution.autonomous_learner import AutonomousLearner
from cognithor.evolution.cron_scheduler import EvolutionScheduler
from cognithor.evolution.deep_learner import DeepLearner
from cognithor.evolution.goal_index import GoalScopedIndex
from cognithor.evolution.idle_detector import IdleDetector
from cognithor.evolution.loop import EvolutionLoop
from cognithor.evolution.meta_learner import MetaLearner
from cognithor.evolution.models import LearningPlan, SubGoal
from cognithor.evolution.rag_pipeline import EvolutionRAG
from cognithor.evolution.resume import EvolutionResumer, ResumeState
from cognithor.evolution.strategy_planner import StrategyPlanner

__all__ = [
    "AutonomousLearner",
    "DeepLearner",
    "EvolutionLoop",
    "EvolutionRAG",
    "EvolutionResumer",
    "EvolutionScheduler",
    "GoalScopedIndex",
    "IdleDetector",
    "LearningPlan",
    "MetaLearner",
    "ResumeState",
    "StrategyPlanner",
    "SubGoal",
]
