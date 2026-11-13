from __future__ import annotations
import importlib.util, json, tempfile
from pathlib import Path
from typing import Any
PLUGIN_ID='yaiwes.agent_fleet.ai_scientist_v2'
TARGET_RELATIVE='Agente Yaiwes principal/agent-fleet-parallelism/ai-scientist-v2'
def descriptor()->dict[str,str]: return {'plugin_id':PLUGIN_ID,'role':'autonomous_scientific_research_agent','target_path':TARGET_RELATIVE,'microtest':'upstream_bfts_idea_pipeline'}
def _load(path:Path):
    spec=importlib.util.spec_from_file_location('yaiwes_ai_scientist_bfts_utils',path)
    if spec is None or spec.loader is None: raise RuntimeError(f'BFTS_UTILS_LOAD_FAILED:{path}')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def run_microtest(repo_root:str|Path)->dict[str,Any]:
    root=Path(repo_root).resolve(); target=root/TARGET_RELATIVE
    if not (target/'launch_scientist_bfts.py').is_file(): raise RuntimeError('AI_SCIENTIST_ENTRYPOINT_MISSING')
    if not (target/'bfts_config.yaml').is_file(): raise RuntimeError('AI_SCIENTIST_BFTS_CONFIG_MISSING')
    mod=_load(target/'ai_scientist'/'treesearch'/'bfts_utils.py')
    idea={'Name':'yaiwes_microtest','Title':'Deterministic YAIWES integration test','Experiment':'Verify real upstream BFTS idea/config preparation'}
    with tempfile.TemporaryDirectory(prefix='yaiwes_ai_scientist_') as td:
        work=Path(td); idea_md=work/'idea.md'; mod.idea_to_markdown(idea,str(idea_md),None)
        config=Path(mod.edit_bfts_config_file(str(target/'bfts_config.yaml'),str(work),str(idea_md)))
        text=config.read_text(encoding='utf-8')
        if 'YAIWES integration test' not in idea_md.read_text(encoding='utf-8'): raise RuntimeError('IDEA_TO_MARKDOWN_FEATURE_FAILED')
        if str(idea_md) not in text or str(work) not in text: raise RuntimeError('BFTS_CONFIG_FEATURE_FAILED')
        if not (work/'data').is_dir() or not (work/'logs').is_dir(): raise RuntimeError('BFTS_WORKSPACE_FEATURE_FAILED')
        return {'status':'PASS','capability':'ai_scientist_v2_bfts_idea_pipeline','idea_md':idea_md.name,'config':config.name,'data_dir':True,'logs_dir':True}
