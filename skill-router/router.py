#!/usr/bin/env python3
"""Skill router - descrubridor de skills desde BIBLIOTECA"""
import os, json, requests
from pathlib import Path

BIBLIOTECA = Path("/opt/nct/foundation/BIBLIOTECA/BIBLIOTECA")
SKILL_REGISTRY = "/opt/nct/skills/registry/skill_registry.json"

def list_skills():
    """Lista skills disponibles en BIBLIOTECA"""
    skills = []
    if BIBLIOTECA.exists():
        for md in BIBLIOTECA.rglob("*.md"):
            if md.name == "README.md":
                continue
            skills.append({
                "name": md.stem,
                "path": str(md),
                "category": md.parent.name
            })
    return skills

def search_skill(query):
    """Busca una skill por nombre o contenido"""
    results = []
    for skill in list_skills():
        if query.lower() in skill["name"].lower():
            results.append(skill)
    return results

def add_to_registry(skill_id, name, version, autor, sha256, categoria):
    """Agrega una skill aprobada al registry"""
    with open(SKILL_REGISTRY) as f:
        reg = json.load(f)
    skill = {
        "id": skill_id,
        "nombre": name,
        "version": version,
        "autor": autor,
        "hash": f"sha256:{sha256}",
        "categoria": categoria,
        "estado": "approved",
        "nivel_confianza": "high"
    }
    reg["skills"].append(skill)
    reg["total_skills"] = len(reg["skills"])
    with open(SKILL_REGISTRY, "w") as f:
        json.dump(reg, f, indent=2)
    return skill

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        print(json.dumps(list_skills(), indent=2))
    elif len(sys.argv) > 2 and sys.argv[1] == "search":
        print(json.dumps(search_skill(sys.argv[2]), indent=2))
    else:
        print("uso: router.py list | router.py search <query>")
