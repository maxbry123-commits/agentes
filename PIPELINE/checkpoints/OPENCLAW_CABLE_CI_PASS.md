# OpenClaw → Wordflow cable CI evidence

- workflow: verify-openclaw-cable
- commit: 94bddab5dd438f1270d4186fa48fe8873440f8ee
- result: PASS
- test: extensions/wordflow_kernel/tests/test_openclaw_http.py
- execution: GitHub Actions runner
- source: OpenClaw Gateway OpenAI-compatible /v1/chat/completions
- security: fail-closed; token supplied only by runtime secret
