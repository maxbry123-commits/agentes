"""Shared low-level bits for the publish pipeline (scan / build / cloud). Kept
tiny and dependency-light so scan, build, and cloud_client can all lean on it
without reaching sideways into each other."""
from __future__ import annotations

import os
import re

from backend.apps.outputs.models import Output
from backend.config.paths import OUTPUTS_WORKSPACE_DIR


class PublishError(Exception):
    """User-facing publish failure; message is safe to show in a toast."""


def slugify(name: str) -> str:
    """A url-safe slug hint from the app name; the cloud guarantees uniqueness."""
    s = re.sub(r"[^a-z0-9]+", "-", (name or "app").lower()).strip("-")
    s = s[:32].strip("-")
    return s or "app"


def is_webapp(output: Output) -> bool:
    return bool(output.workspace_id)


def workspace_dir(output: Output) -> str:
    return os.path.join(OUTPUTS_WORKSPACE_DIR, output.workspace_id or "")
