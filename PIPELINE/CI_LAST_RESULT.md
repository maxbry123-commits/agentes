# CI LAST RESULT

Commit: `6faf44fddae43301adf16c66245779de046d7e3e`

| Probe | Status | Error |
|---|---|---|
| T01 | **FAIL** | PyCompileError: Sorry: IndentationError: unexpected indent (test_w_gaps.py, line 1) |

## T01 traceback

```text
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.12.14/x64/lib/python3.12/py_compile.py", line 144, in compile
    code = loader.source_to_code(source_bytes, dfile or file,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap_external>", line 1063, in source_to_code
  File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
  File "/home/runner/work/agentes/agentes/extensions/wordflow/tests/test_w_gaps.py", line 1
    def test_main_loop_checkpoint(self):
IndentationError: unexpected indent

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 21, in probe
    value = fn()
            ^^^^
  File "/home/runner/work/agentes/agentes/tools/wordflow_verification.py", line 35, in t01
    py_compile.compile(str(path), doraise=True)
  File "/opt/hostedtoolcache/Python/3.12.14/x64/lib/python3.12/py_compile.py", line 150, in compile
    raise py_exc
py_compile.PyCompileError: Sorry: IndentationError: unexpected indent (test_w_gaps.py, line 1)

```
| T02 | **PASS** |  |
| T03 | **PASS** |  |
| T04 | **PASS** |  |
| T05 | **PASS** |  |
| T06 | **PASS** |  |
| T07 | **PASS** |  |
| T08 | **PASS** |  |
| T09 | **PASS** |  |
| T10A | **PASS** |  |
| T10B | **PASS** |  |
