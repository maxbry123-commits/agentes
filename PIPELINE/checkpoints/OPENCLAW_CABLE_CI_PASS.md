# OpenClaw → Wordflow cable CI evidence

- workflow: verify-openclaw-cable
- commit: a9cebda182d17e91fd2417200db609ee55df5813
- result: PASS
- test: extensions/wordflow_kernel/tests/test_openclaw_http.py
- execution: GitHub Actions runner
- source: OpenClaw Gateway OpenAI-compatible /v1/chat/completions
- security: fail-closed; token supplied only by runtime secret
