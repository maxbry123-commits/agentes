"""Kernel reception surface.

Inbox docs live in extensions/wordflow/reception/ (Wordflow product).
This package is the kernel LINK: convert + locate + dispatch.
"""
from .convert import convert, run_mcr, DEFAULT_MAX_CONTEXT, locate, ingest

__all__ = [
    "convert",
    "run_mcr",
    "DEFAULT_MAX_CONTEXT",
    "locate",
    "ingest",
]
