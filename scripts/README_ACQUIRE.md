# Deterministic Agent Acquisition v2

**Goal:** DOWNLOAD → CONSERVE → PIN → VERIFY → REPRODUCE

## Two layers

1. **SOURCE** — full tree at fixed commit/tag → `source/complete-source/`
2. **DISTRIBUTION** — official executable package(s) → `distribution/official/`

Searches automatically:
- GitHub release assets
- npm registry tarball (from package.json)
- PyPI wheels/sdists (from pyproject)
- Docker image refs (recorded; pull optional)

## Usage

```bash
python scripts/acquire_agent.py \
  --id Hermes \
  --repo https://github.com/NousResearch/hermes-agent \
  --ref v2026.8.3 \
  --commit 3c27eb6234bf91b8ceee9e9071591b31e9b148cb
```

Never use main/master/latest/HEAD.

## Layout

```
agents/<id>/
  source/complete-source/
  distribution/official/
  distribution/rebuilt/
  models/ dependencies/ runtime/ tools/ plugins/
  build/ provenance/ hashes/
  manifest.json
```
