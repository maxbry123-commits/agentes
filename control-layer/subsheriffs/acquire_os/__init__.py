"""Acquire Engine — recipe-driven acquisition (not a separate OS product).

OpenClaw-40 is a Recipe instance, not the loop motor.
"""
__version__ = "1.0.0"

from .core import AcquireEngine, AcquireContext, StepResult

__all__ = ["AcquireEngine", "AcquireContext", "StepResult"]
