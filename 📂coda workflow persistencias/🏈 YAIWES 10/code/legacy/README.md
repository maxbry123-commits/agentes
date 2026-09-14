# Legacy Prototype

This directory contains the original Python prototype of Auto-Pentest-GPT-AI.

## Original Approach

- **Model**: OpenHermes-2.5-Mistral-7B, fine-tuned on Kali Linux commands
- **Format**: GGUF quantized model (`Pentest_LLM.gguf` — not included in repo due to size)
- **Published**: [ArmurAI/Pentest_AI on HuggingFace](https://huggingface.co/ArmurAI/Pentest_AI)
- **Runtime**: Python with ctransformers for local inference

## Why This Was Replaced

The Python prototype demonstrated the concept but had limitations:

- Single model for all tasks (recon, classification, exploitation, reporting)
- No structured output — free-text responses parsed with string matching
- Sequential tool execution — no concurrency
- No persistent state — each session starts from scratch
- Python dependency overhead — ctransformers, torch, transformers

The new Go-based platform addresses all of these with a multi-agent architecture,
native tool integration, and structured campaign state management.
