# wordflow.engine — public API (legacy + V1)
from .input_normalizer import normalize_input_block, InputBlockError
from .goals_extractor import extract_goals_in, load_goals_catalog, empty_goals_out
from .refute_repair import refute_block, propose_repairs, apply_auto_repairs
from .sentinel import run_sentinel
from .council import run_council, load_roles
from .main_loop import run_main_12, load_main_12
from .entrypoint import run_wordflow
from .evidence_bridge import goals_out_to_evidence_packet
from .watchdog import check_watchdog, scan_state_for_secrets
from .supervisor import make_checkpoint, is_expired, validate_checkpoint, refresh_ttl

# V1 stable surface
from .entrypoint_v1 import run_v1, get_orchestrator, reset_default
from .orchestrator_v1 import OrchestratorV1
from .mission import mission_from_raw, enforce_mission
from .control_sheriff_bridge import gate_c00
from .contract_router import ContractRouter
from .workflow_dna import compile_dna, verify_dna
from .bitacora import BitacoraStore
from .recovery import RecoveryEngine

__all__ = [
    # legacy
    "normalize_input_block",
    "InputBlockError",
    "extract_goals_in",
    "load_goals_catalog",
    "empty_goals_out",
    "refute_block",
    "propose_repairs",
    "apply_auto_repairs",
    "run_sentinel",
    "run_council",
    "load_roles",
    "run_main_12",
    "load_main_12",
    "run_wordflow",
    "goals_out_to_evidence_packet",
    "check_watchdog",
    "scan_state_for_secrets",
    "make_checkpoint",
    "is_expired",
    "validate_checkpoint",
    "refresh_ttl",
    # V1
    "run_v1",
    "get_orchestrator",
    "reset_default",
    "OrchestratorV1",
    "mission_from_raw",
    "enforce_mission",
    "gate_c00",
    "ContractRouter",
    "compile_dna",
    "verify_dna",
    "BitacoraStore",
    "RecoveryEngine",
]
