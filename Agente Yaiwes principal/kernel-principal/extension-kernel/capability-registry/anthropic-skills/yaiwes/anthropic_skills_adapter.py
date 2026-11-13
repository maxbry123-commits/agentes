"""YAIWES Anthropic-Skills adapter: real Agent Skills discovery and upstream validation."""
from __future__ import annotations
import importlib.util, json
from pathlib import Path
from typing import Any

PLUGIN_ID='yaiwes.capability.anthropic_skills'
TARGET_RELATIVE='Agente Yaiwes principal/kernel-principal/extension-kernel/capability-registry/anthropic-skills'

def _load_validator(target: Path):
    p=target/'skills'/'skill-creator'/'scripts'/'quick_validate.py'
    spec=importlib.util.spec_from_file_location('anthropic_quick_validate',p)
    if not spec or not spec.loader: raise RuntimeError('VALIDATOR_LOAD_FAILED')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod.validate_skill

def run_microtest(repo_root: str|Path)->dict[str,Any]:
    target=Path(repo_root).resolve()/TARGET_RELATIVE
    skills_root=target/'skills'
    validator=_load_validator(target)
    skill_dirs=sorted({p.parent for p in skills_root.glob('*/SKILL.md')})
    if len(skill_dirs)<2: raise RuntimeError(f'SKILL_DISCOVERY_TOO_SMALL:{len(skill_dirs)}')
    chosen=['mcp-builder','skill-creator']
    results={}
    for name in chosen:
        ok,msg=validator(skills_root/name)
        if not ok: raise RuntimeError(f'SKILL_VALIDATION_FAILED:{name}:{msg}')
        results[name]=msg
    sample=(skills_root/'mcp-builder'/'SKILL.md').read_text(encoding='utf-8')
    if 'name: mcp-builder' not in sample or 'description:' not in sample:
        raise RuntimeError('MCP_BUILDER_FRONTMATTER_MISSING')
    return {'status':'PASS','capability':'dynamic_agent_skill_registry','discovered_top_level_skills':len(skill_dirs),'validated':chosen,'validator_results':results}

if __name__=='__main__':
    import sys
    print('YAIWES_ANTHROPIC_SKILLS_RESULT='+json.dumps(run_microtest(sys.argv[1]),separators=(',',':')))
