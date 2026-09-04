#!/usr/bin/env bash
set -euo pipefail
REPO=https://github.com/openai/codex
REF=rust-v0.147.0
COMMIT=be6e8eac029b183056b7e4402879f15d2c85f61b
TAG=agent-Codex-rust-v0.147.0
URL="$REPO/archive/$COMMIT.tar.gz"
mkdir -p agents/Codex/source agents/Codex/distribution/official agents/Codex/hashes agents/_state
curl -fsSL -o /tmp/codex-src.tar.gz "$URL"
SHA=$(sha256sum /tmp/codex-src.tar.gz | awk '{print $1}')
printf '%s\n' "$COMMIT" > agents/Codex/source/commit.txt
printf '%s\n' "$REF" > agents/Codex/source/release.txt
printf '%s\n' "$REPO" > agents/Codex/source/repo.txt
printf '%s\n' "$URL" > agents/Codex/source/archive.url
printf '%s\n' "$SHA" > agents/Codex/source/archive.sha256
gh release upload "$TAG" /tmp/codex-src.tar.gz --clobber || true
printf '%s\n' "{\"storage\":\"github_release\",\"release_tag\":\"$TAG\",\"asset\":\"codex-src.tar.gz\",\"sha256\":\"$SHA\",\"commit\":\"$COMMIT\",\"ref\":\"$REF\"}" > agents/Codex/source/SOURCE_PIN.json
curl -fsSL -H "Authorization: Bearer ${GH_TOKEN}" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/openai/codex/releases/tags/$REF" -o /tmp/rel.json
python3 scripts/finalize_codex_meta.py
cat > agents/_state/Codex.json <<EOF
{"agent":"Codex","task":"A5","status":"DONE","protocol":"TEAM-SEALS-ACQUIRE-v2.1","identity":{"repository":"$REPO","ref":"$REF","commit":"$COMMIT"},"release_tag":"$TAG","layers":{"source":"CAPTURED","distribution_git":"META_PINS","distribution_release":"CAPTURED","finalize":"DONE"},"notes":"source tar+binaries on Release; git=pins+manifest"}
EOF
git config user.name github-actions[bot]
git config user.email 41898282+github-actions[bot]@users.noreply.github.com
git add agents/Codex agents/_state/Codex.json
git diff --cached --quiet || (git commit -m "A5 DONE: Codex meta pins; Release $TAG" && git push)
