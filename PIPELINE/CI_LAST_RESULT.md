# CI LAST RESULT

Commit: `a3a5e0dbf351f28e89db43eb652b63f1420bf896`

| Probe | Status | Error |
|---|---|---|
| T01 | **PASS** |  |
| T02 | **PASS** |  |
| T03 | **FAIL** | ImportError: cannot import name 'validate_against_lock' from 'extensions.wordflow.engine.goal_lock' (/home/runner/work/agentes/agentes/extensions/wordflow/engine/goal_lock.py) |

## T03 traceback

```text
Traceback (most recent call last):
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 21, in probe
    value = fn()
            ^^^^
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 50, in t03
    from extensions.wordflow.engine.code_path_runner import consult_path_gateway
  File "/home/runner/work/agentes/agentes/extensions/wordflow/engine/__init__.py", line 14, in <module>
    from .entrypoint_v1 import run_v1, get_orchestrator, reset_default
  File "/home/runner/work/agentes/agentes/extensions/wordflow/engine/entrypoint_v1.py", line 7, in <module>
    from .orchestrator_v1 import OrchestratorV1
  File "/home/runner/work/agentes/agentes/extensions/wordflow/engine/orchestrator_v1.py", line 11, in <module>
    from .bootstrap import WordflowKernel
  File "/home/runner/work/agentes/agentes/extensions/wordflow/engine/bootstrap.py", line 14, in <module>
    from .runtime_bus import RuntimeBus
  File "/home/runner/work/agentes/agentes/extensions/wordflow/engine/runtime_bus.py", line 7, in <module>
    from .engine_abi import Engine, apply_goal_filter, make_result
  File "/home/runner/work/agentes/agentes/extensions/wordflow/engine/engine_abi.py", line 10, in <module>
    from .goal_lock import validate_against_lock
ImportError: cannot import name 'validate_against_lock' from 'extensions.wordflow.engine.goal_lock' (/home/runner/work/agentes/agentes/extensions/wordflow/engine/goal_lock.py)

```
| T04 | **PASS** |  |
| T05 | **PASS** |  |
| T06 | **FAIL** | AssertionError: {'ok': False, 'converted': {'ok': True, 'normalized': {'text': 'pytest reception wiring deterministic', 'keys': ['raw_text'], 'source': None}, 'use_sdpa': False, 'branch': 'default', 'max_context': 20000000, 'sdpa_stub': False, 'mcr_stub': False}, 'contract': {'ok': False, 'error': 'INPUT_COMPILER_MISSING', 'invoked': False}, 'classification': {'ok': False, 'error': 'TASK_CLASSIFIER_MISSING', 'invoked': False}, 'phase': {'ok': True, 'phase': 'inbox', 'path': 'extensions/wordflow/ |

## T06 traceback

```text
Traceback (most recent call last):
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 21, in probe
    value = fn()
            ^^^^
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 81, in t06
    assert result["ok"] is True and result["hops_ok"] is True, result
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'ok': False, 'converted': {'ok': True, 'normalized': {'text': 'pytest reception wiring deterministic', 'keys': ['raw_text'], 'source': None}, 'use_sdpa': False, 'branch': 'default', 'max_context': 20000000, 'sdpa_stub': False, 'mcr_stub': False}, 'contract': {'ok': False, 'error': 'INPUT_COMPILER_MISSING', 'invoked': False}, 'classification': {'ok': False, 'error': 'TASK_CLASSIFIER_MISSING', 'invoked': False}, 'phase': {'ok': True, 'phase': 'inbox', 'path': 'extensions/wordflow/reception/', 'wrote': False, 'apply': 'external', 'contract': 'LOCATE_ONLY'}, 'plugin': {'ok': False, 'error': 'ENCHUFE_MISSING', 'invoked': False}, 'context_pack': {'ok': True, 'invoked': False, 'skipped': True, 'reason': 'NO_INSTANCE_OFFLINE_PROBE'}, 'locate': {'ok': True, 'kind': 'inbox', 'path': 'extensions/wordflow/reception/RECEPTION_agentes.md', 'catalog': {'inbox': 'extensions/wordflow/reception/RECEPTION_agentes.md', 'template': 'extensions/wordflow/reception/RECEPTION_TEMPLATE.md', 'links': 'extensions/wordflow/reception/KNOWLEDGE_RECEPTION_LINKS.md', 'guide': 'extensions/wordflow/reception/advanced_engineering_code_standard_guia_maestra.md', 'convert': 'extensions/wordflow/reception/convert.py', 'kernel': 'extensions/wordflow_kernel/reception', 'motor': 'extensions/wordflow/motors/kernel_ext/motor.py', 'phase_inbox': 'extensions/wordflow/reception/', 'phase_kernel': 'extensions/wordflow_kernel/', 'phase_engine': 'extensions/wordflow/engine/', 'phase_standards': 'extensions/wordflow/standards/', 'phase_loop': 'extensions/maxbry_loop/', 'phase_deploy': 'extensions/github_deploy/', 'phase_pipeline': 'PIPELINE/', 'phase_plugin': 'extensions/wordflow_kernel/ficha.v2.json'}, 'url_inbox': 'https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow/reception', 'url_kernel': 'https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow_kernel/reception'}, 'phase_plan': {'ok': False, 'wrote': False, 'reason': 'locate_only', 'git_apply': False}, 'git': {'ok': False, 'skipped': True, 'reason': 'locate_only', 'git_apply': False}, 'invoked': {'input_compiler': False, 'task_classifier': False, 'locate_phase': True, 'enchufe_plugin': False, 'context_pack': False, 'apply_push': False}, 'connectivity': {'required': {'convert': {'ok': True, 'normalized': {'text': 'pytest reception wiring deterministic', 'keys': ['raw_text'], 'source': None}, 'use_sdpa': False, 'branch': 'default', 'max_context': 20000000, 'sdpa_stub': False, 'mcr_stub': False}, 'input_compiler': {'ok': False, 'error': 'INPUT_COMPILER_MISSING', 'invoked': False}, 'classifier': {'ok': False, 'error': 'TASK_CLASSIFIER_MISSING', 'invoked': False}, 'locate': {'ok': True, 'phase': 'inbox', 'path': 'extensions/wordflow/reception/', 'wrote': False, 'apply': 'external', 'contract': 'LOCATE_ONLY'}, 'plugin': {'ok': False, 'error': 'ENCHUFE_MISSING', 'invoked': False}}, 'optional': {'context_pack': {'ok': True, 'invoked': False, 'skipped': True, 'reason': 'NO_INSTANCE_OFFLINE_PROBE'}, 'git_hook': {'ok': False, 'skipped': True, 'reason': 'locate_only', 'git_apply': False}}, 'required_ok': False, 'optional_safe': True}, 'wrote': False, 'git_apply': False, 'hops_ok': False}

```
| T07 | **FAIL** | ImportError: cannot import name 'validate_against_lock' from 'extensions.wordflow.engine.goal_lock' (/home/runner/work/agentes/agentes/extensions/wordflow/engine/goal_lock.py) |

## T07 traceback

```text
Traceback (most recent call last):
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 21, in probe
    value = fn()
            ^^^^
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 91, in t07
    from extensions.wordflow.engine.evidence_packet import build_evidence_packet, chain_packets, verify_packet_chain, EvidencePacketError
  File "/home/runner/work/agentes/agentes/extensions/wordflow/engine/__init__.py", line 14, in <module>
    from .entrypoint_v1 import run_v1, get_orchestrator, reset_default
  File "/home/runner/work/agentes/agentes/extensions/wordflow/engine/entrypoint_v1.py", line 7, in <module>
    from .orchestrator_v1 import OrchestratorV1
  File "/home/runner/work/agentes/agentes/extensions/wordflow/engine/orchestrator_v1.py", line 11, in <module>
    from .bootstrap import WordflowKernel
  File "/home/runner/work/agentes/agentes/extensions/wordflow/engine/bootstrap.py", line 14, in <module>
    from .runtime_bus import RuntimeBus
  File "/home/runner/work/agentes/agentes/extensions/wordflow/engine/runtime_bus.py", line 7, in <module>
    from .engine_abi import Engine, apply_goal_filter, make_result
  File "/home/runner/work/agentes/agentes/extensions/wordflow/engine/engine_abi.py", line 10, in <module>
    from .goal_lock import validate_against_lock
ImportError: cannot import name 'validate_against_lock' from 'extensions.wordflow.engine.goal_lock' (/home/runner/work/agentes/agentes/extensions/wordflow/engine/goal_lock.py)

```
| T08 | **PASS** |  |
| T09 | **PASS** |  |
| T10A | **PASS** |  |
| T10B | **FAIL** | AssertionError: pytest regression exit code=2 |

## T10B traceback

```text
Traceback (most recent call last):
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 21, in probe
    value = fn()
            ^^^^
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 141, in t10b
    raise AssertionError(f"pytest regression exit code={code}")
AssertionError: pytest regression exit code=2

```
