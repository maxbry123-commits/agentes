# source_evolution.engine
from .version_pin import normalize_pin, VersionPinError, pin_hash
from .registry import SourceRegistry
from .fetch_planner import build_fetch_plan, FakeFetcher
from .license_gate import check_license
from .install_planner import build_install_plan
from .entrypoint import run_acquire

__all__ = [
    "normalize_pin",
    "VersionPinError",
    "pin_hash",
    "SourceRegistry",
    "build_fetch_plan",
    "FakeFetcher",
    "check_license",
    "build_install_plan",
    "run_acquire",
]
