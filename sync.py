#!/usr/bin/env python3
"""
sync.py — motor de sincronización desde 5 fuentes externas a nuestro 02-skill registry.

Fuentes:
  1. agentregistry-dev/agentregistry (aregistry.ai)
  2. agent-skills-hub/agent-skills-hub (790+ skills, OpenClaw-ready)
  3. skillhub-club/skillhub-desktop
  4. openagentskill.com (API JSON)
  5. hol.org/registry (Universal Agentic Registry)

Reglas:
  - Solo dropeamos skills que cumplan agentskills.io (SKILL.md + frontmatter válido).
  - Dedupe por hash(name + first 200 chars de description).
  - Scoring: trust_tier (official > community), votes, last_release.
  - Output: JSON Lines en registries/02-skill/incoming/<source>/<date>.jsonl
"""
import json, sys, os, hashlib, urllib.request, urllib.parse, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent
INCOMING = REPO / "registries" / "02-skill" / "incoming"
INCOMING.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "agentregistry_dev":  {"url":"https://api.aregistry.ai/v1/skills?limit=500","format":"json"},
    "agent_skills_hub":   {"url":"https://raw.githubusercontent.com/agent-skills-hub/agent-skills-hub/main/registry.json","format":"json"},
    "skillhub_club":      {"url":"https://www.skillhub.club/api/v1/skills?limit=500","format":"json"},
    "openagentskill":     {"url":"https://www.openagentskill.com/api/registry/skills?format=json&limit=500","format":"json"},
    "hol_registry":       {"url":"https://hol.org/registry/api/v1/skills?limit=500","format":"json"},
}

def fetch(url, fmt):
    req = urllib.request.Request(url, headers={"User-Agent":"M3-sync/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
            return json.loads(data) if fmt == "json" else data.decode("utf-8","replace")
    except Exception as e:
        return {"_error": str(e), "_url": url}

def parse_agentregistry_dev(raw):
    """aregistry.ai: array de {id,name,version,description,type}"""
    if not isinstance(raw, list): return []
    return [
        {
            "id": s.get("id") or s.get("name"),
            "name": s.get("name"),
            "version": s.get("version","0.0.0"),
            "description": s.get("description",""),
            "tags": s.get("tags", []),
            "trust_tier": "official",
            "source": "agentregistry_dev",
        }
        for s in raw
        if s.get("name")
    ]

def parse_agent_skills_hub(raw):
    """registry.json: {skills: [{id,name,description,version,tier,votes,author,...}]}"""
    if not isinstance(raw, dict): return []
    skills = raw.get("skills") or raw.get("items") or []
    return [
        {
            "id": s.get("id") or s.get("name"),
            "name": s.get("name"),
            "version": s.get("version","0.0.0"),
            "description": s.get("description",""),
            "tags": s.get("tags", []),
            "trust_tier": s.get("tier","community"),
            "votes": s.get("votes", 0),
            "source": "agent_skills_hub",
        }
        for s in skills
        if s.get("name")
    ]

def parse_skillhub_club(raw):
    """skillhub.club: {data: [{...}]} o array"""
    items = raw if isinstance(raw, list) else raw.get("data", raw.get("items", []))
    return [
        {
            "id": s.get("slug") or s.get("name"),
            "name": s.get("name"),
            "version": s.get("version","0.0.0"),
            "description": s.get("description",""),
            "tags": s.get("tags", []),
            "trust_tier": "curated",
            "source": "skillhub_club",
        }
        for s in items
        if s.get("name")
    ]

def parse_openagentskill(raw):
    """/api/registry/skills: array o {skills:[]}"""
    items = raw if isinstance(raw, list) else raw.get("skills", [])
    return [
        {
            "id": s.get("slug") or s.get("id") or s.get("name"),
            "name": s.get("name"),
            "version": s.get("version","0.0.0"),
            "description": s.get("description",""),
            "tags": s.get("tags", []),
            "trust_tier": s.get("trust","community"),
            "source": "openagentskill",
        }
        for s in items
        if s.get("name")
    ]

def parse_hol_registry(raw):
    """hol.org/registry: {skills:[{slug,name,description,tags,trust,version}]}"""
    if not isinstance(raw, dict): return []
    skills = raw.get("skills") or raw.get("items") or []
    return [
        {
            "id": s.get("slug") or s.get("id") or s.get("name"),
            "name": s.get("name"),
            "version": s.get("version","0.0.0"),
            "description": s.get("description",""),
            "tags": s.get("tags", []),
            "trust_tier": s.get("trust","community"),
            "source": "hol_registry",
        }
        for s in skills
        if s.get("name")
    ]

PARSERS = {
    "agentregistry_dev": parse_agentregistry_dev,
    "agent_skills_hub":  parse_agent_skills_hub,
    "skillhub_club":     parse_skillhub_club,
    "openagentskill":    parse_openagentskill,
    "hol_registry":      parse_hol_registry,
}

def dedupe_key(skill):
    """Hash de (name normalizado + primeros 200 chars de desc)."""
    name = (skill.get("name") or "").lower().strip()
    desc = (skill.get("description") or "")[:200]
    return hashlib.sha256(f"{name}|{desc}".encode()).hexdigest()[:16]

def score(skill):
    """Score 0..1: trust_tier + votes + version + freshness."""
    tier = {"official":0.5, "curated":0.4, "community":0.2, "unknown":0.1}.get(skill.get("trust_tier","unknown"), 0.1)
    votes = min((skill.get("votes",0) or 0) / 1000, 0.3)  # cap 0.3
    return round(tier + votes, 3)

def validate_agentskills_io(skill):
    """Reglas mínimas del spec agentskills.io v0.2.0."""
    name = skill.get("name","")
    desc = skill.get("description","")
    if not (1 <= len(name) <= 64): return False, "name length"
    if not name.replace("-","").replace("_","").isalnum(): return False, "name charset"
    if not name.islower(): return False, "name not lowercase"
    if name.startswith("-") or name.endswith("-"): return False, "name leading/trailing hyphen"
    if not (1 <= len(desc) <= 1024): return False, "description length"
    return True, "ok"

def sync(source_name):
    src = SOURCES[source_name]
    raw = fetch(src["url"], src["format"])
    if isinstance(raw, dict) and "_error" in raw:
        print(f"[{source_name}] ERROR: {raw['_error']}")
        return 0
    parse_fn = PARSERS[source_name]
    skills = parse_fn(raw)
    kept = []
    for s in skills:
        ok, why = validate_agentskills_io(s)
        if not ok:
            continue
        s["_dedupe_key"] = dedupe_key(s)
        s["_score"] = score(s)
        s["_validated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
        kept.append(s)
    out_dir = INCOMING / source_name
    out_dir.mkdir(exist_ok=True)
    fname = out_dir / f"{datetime.date.today().isoformat()}.jsonl"
    with open(fname, "w") as f:
        for s in kept:
            f.write(json.dumps(s) + "\n")
    print(f"[{source_name}] {len(kept)} skills → {fname}")
    return len(kept)

def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    total = 0
    for name in SOURCES:
        if only and only != name: continue
        total += sync(name)
    print(f"TOTAL: {total} skills ingestadas")

if __name__ == "__main__":
    main()
