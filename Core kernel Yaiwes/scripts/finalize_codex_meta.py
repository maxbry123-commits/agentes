#!/usr/bin/env python3
import json
from pathlib import Path

tag = "agent-Codex-rust-v0.147.0"
rel = json.load(open("/tmp/rel.json"))
off = Path("agents/Codex/distribution/official")
off.mkdir(parents=True, exist_ok=True)
assets = []
for a in rel.get("assets") or []:
    name = a["name"]
    url = a["browser_download_url"]
    size = a.get("size")
    cons = f"https://github.com/maxbry123-commits/agentes/releases/download/{tag}/{name}"
    assets.append({
        "name": name,
        "url": url,
        "size": size,
        "conserved_url": cons,
        "status": "ON_AGENTES_RELEASE",
    })
    (off / f"{name}.PIN.json").write_text(
        json.dumps(
            {
                "name": name,
                "url": url,
                "size": size,
                "conserved_url": cons,
                "release_tag": tag,
            },
            indent=2,
        )
        + "\n"
    )
(off / "assets.json").write_text(json.dumps(assets, indent=2) + "\n")
(off / "SHA256SUMS").write_text(f"# binaries on Release {tag}\n")
sha = open("agents/Codex/source/archive.sha256").read().strip()
url = open("agents/Codex/source/archive.url").read().strip()
m = {
    "protocol": "TEAM-SEALS-ACQUIRE-v2.1",
    "agent": "Codex",
    "identity": {
        "repository": "https://github.com/openai/codex",
        "ref": "rust-v0.147.0",
        "commit": "be6e8eac029b183056b7e4402879f15d2c85f61b",
    },
    "source": {
        "available": True,
        "storage": "github_release",
        "release_tag": tag,
        "asset": "codex-src.tar.gz",
        "upstream_url": url,
        "archive_sha256": sha,
        "conserved_url": f"https://github.com/maxbry123-commits/agentes/releases/download/{tag}/codex-src.tar.gz",
    },
    "distribution": {"official": assets, "release_tag": tag},
    "layers": {"source": "CAPTURED", "distribution": "CAPTURED"},
}
Path("agents/Codex/manifest.json").write_text(json.dumps(m, indent=2) + "\n")
Path("agents/Codex/hashes").mkdir(parents=True, exist_ok=True)
Path("agents/Codex/hashes/SHA256SUMS").write_text(f"{sha}  source/codex-src.tar.gz\n")
print("ok", len(assets), sha)
