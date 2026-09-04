"""Shared RL conversion infrastructure.

Provides parameterized verifier templates, oracle-gate validation, and a
unified upload pipeline for converting SFT-only datasets to RL format.

Architecture: each source gets a thin `verifier.py` that selects a template
+ language; this module handles the Docker oracle gate and HF/TaskTrove upload.
"""
