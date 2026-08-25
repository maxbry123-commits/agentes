# -*- coding: utf-8 -*-
"""Wordflow Programming path — modular process tree (C-19).

Each stage is one file. Orchestrator: runner.run_code_path / pipeline.run_unified.
"""
from __future__ import annotations

from .runner import run_code_path, CodePathError, consult_path_gateway
from .pipeline import ProgrammingPipeline, default_pipeline
from .kwargs import full_pass_kwargs, minimal_block_kwargs
from .quality_bar import admit_or_reject, evaluate_input_quality, QualityBarError, MIN_CHARS_DEFAULT
from .skill_compiler import compile_skill_to_code, compile_and_promote_skill, SkillNativeError

__all__ = [
    "run_code_path",
    "CodePathError",
    "consult_path_gateway",
    "ProgrammingPipeline",
    "default_pipeline",
    "full_pass_kwargs",
    "minimal_block_kwargs",
    "admit_or_reject",
    "evaluate_input_quality",
    "QualityBarError",
    "MIN_CHARS_DEFAULT",
    "compile_skill_to_code",
    "compile_and_promote_skill",
    "SkillNativeError",
]
