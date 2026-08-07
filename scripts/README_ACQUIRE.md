# Deterministic Agent Acquisition

Protocol TEAM SEALS §1-15.

```bash
python scripts/acquire_agent.py \
  --id OpenCode \
  --repo https://github.com/anomalyco/opencode \
  --ref v1.18.15 \
  --commit d7b115f
```

Output layout:

```
agents/<id>/
  source/repository/   # full tree at pin
  source/commit.txt
  source/release.txt
  source/source.sha256
  binaries/official/
  binaries/rebuilt/
  dependencies/
  build/
  hashes/SHA256SUMS
  manifests/snapshot.json
```

Never use main/master/latest/HEAD.
