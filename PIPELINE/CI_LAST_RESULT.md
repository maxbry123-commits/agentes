# CI LAST RESULT

Commit: `d8117467a0f55e62852c4f9c9c9734cd30afd801`

| Probe | Status | Error |
|---|---|---|
| T01 | **PASS** |  |
| T02 | **FAIL** | ModuleNotFoundError: No module named 'extensions' |

## T02 traceback

```text
Traceback (most recent call last):
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 14, in probe
    value = fn()
            ^^^^
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 33, in t02
    from extensions.wordflow_kernel.gateway.intelligence import make_request
ModuleNotFoundError: No module named 'extensions'

```
| T03 | **FAIL** | ModuleNotFoundError: No module named 'extensions' |

## T03 traceback

```text
Traceback (most recent call last):
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 14, in probe
    value = fn()
            ^^^^
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 43, in t03
    from extensions.wordflow.engine.code_path_runner import consult_path_gateway
ModuleNotFoundError: No module named 'extensions'

```
| T04 | **FAIL** | ModuleNotFoundError: No module named 'extensions' |

## T04 traceback

```text
Traceback (most recent call last):
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 14, in probe
    value = fn()
            ^^^^
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 51, in t04
    from extensions.wordflow.standards.gap_registry import Gap, GapRegistry
ModuleNotFoundError: No module named 'extensions'

```
| T05 | **FAIL** | ModuleNotFoundError: No module named 'extensions' |

## T05 traceback

```text
Traceback (most recent call last):
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 14, in probe
    value = fn()
            ^^^^
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 64, in t05
    from extensions.wordflow.standards.forensic_core import (
ModuleNotFoundError: No module named 'extensions'

```
| T06 | **FAIL** | ModuleNotFoundError: No module named 'extensions' |

## T06 traceback

```text
Traceback (most recent call last):
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 14, in probe
    value = fn()
            ^^^^
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 80, in t06
    from extensions.wordflow_kernel.reception.convert import ingest
ModuleNotFoundError: No module named 'extensions'

```
| T07 | **FAIL** | ModuleNotFoundError: No module named 'extensions' |

## T07 traceback

```text
Traceback (most recent call last):
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 14, in probe
    value = fn()
            ^^^^
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 92, in t07
    from extensions.wordflow.engine.evidence_packet import (
ModuleNotFoundError: No module named 'extensions'

```
| T08 | **FAIL** | ModuleNotFoundError: No module named 'extensions' |

## T08 traceback

```text
Traceback (most recent call last):
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 14, in probe
    value = fn()
            ^^^^
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 112, in t08
    from extensions.wordflow.standards.verdict_authority import VerdictAuthority
ModuleNotFoundError: No module named 'extensions'

```
| T09 | **FAIL** | ModuleNotFoundError: No module named 'extensions' |

## T09 traceback

```text
Traceback (most recent call last):
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 14, in probe
    value = fn()
            ^^^^
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 119, in t09
    from extensions.wordflow.standards.quality_dag import QualityDAG, GateStatus, GateResult
ModuleNotFoundError: No module named 'extensions'

```
| T10A | **PASS** |  |
| T10B | **FAIL** | AssertionError: pytest regression exit code=2 |

## T10B traceback

```text
Traceback (most recent call last):
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 14, in probe
    value = fn()
            ^^^^
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 160, in t10b
    raise AssertionError(f"pytest regression exit code={code}")
AssertionError: pytest regression exit code=2

```
