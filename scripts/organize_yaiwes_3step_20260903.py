#!/usr/bin/env python3
"""Yaiwes organizer: preserve code, consolidate existing components in Core kernel, clean docs conservatively."""
from __future__ import annotations
import json, shutil, sys
from pathlib import Path

ROOT=Path('.')
CORE=Path('Core kernel Yaiwes')
COMP=Path('Componentes open source Yaiwes')
DOCS=Path('Documentos proyectos Yaiwes')
AGENT=Path('Agente Yaiwes principal')
INDEX=Path('INDICE-COMPONENTES-OPEN-SOURCE-YAIWES.md')
KEEP={'.git','.github','.cursor','skills','scripts',CORE.name,COMP.name,DOCS.name,AGENT.name,INDEX.name}
CODE_EXT={'.py','.js','.jsx','.ts','.tsx','.go','.rs','.java','.kt','.kts','.c','.h','.cc','.cpp','.hpp','.cs','.rb','.php','.swift','.scala','.sh','.bash','.zsh','.fish','.ps1','.sql','.proto','.sol','.vue','.svelte','.dart','.ex','.exs','.erl','.hrl','.fs','.fsx','.clj','.cljs','.lua','.r','.m','.mm','.gradle','.cmake'}
DOC_EXT={'.md','.txt','.rst','.adoc','.pdf','.doc','.docx','.odt','.rtf'}

def is_code(p:Path):
    return p.suffix.lower() in CODE_EXT or p.name in {'Dockerfile','Makefile','CMakeLists.txt','package.json','pyproject.toml','go.mod','Cargo.toml','requirements.txt'}

def has_code(p:Path):
    return p.is_dir() and any(is_code(x) for x in p.rglob('*') if x.is_file())

def dest(base:Path,name:str):
    d=base/name
    if not d.exists(): return d
    i=2
    while (base/f'{name}-{i}').exists(): i+=1
    return base/f'{name}-{i}'

def move(p:Path,base:Path):
    base.mkdir(parents=True,exist_ok=True); d=dest(base,p.name); shutil.move(str(p),str(d)); print('MOVE',p,'->',d)

def audit():
    rows=[]
    for p in sorted(ROOT.iterdir(),key=lambda x:x.name.lower()):
        if p.name in KEEP: continue
        if (p.is_file() and is_code(p)) or has_code(p): a='MOVE_CORE'
        elif p.is_file() and p.suffix.lower() in DOC_EXT: a='MOVE_DOCS'
        else: a='GAP_REVIEW'
        rows.append({'path':str(p),'action':a})
    Path('organize-yaiwes-audit.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(rows,indent=2,ensure_ascii=False))

def apply():
    audit(); rows=json.loads(Path('organize-yaiwes-audit.json').read_text())
    CORE.mkdir(exist_ok=True); DOCS.mkdir(exist_ok=True); AGENT.mkdir(exist_ok=True)
    # Componentes open source is future intake: move any current content to Core, never delete it.
    if COMP.exists():
        for p in list(COMP.iterdir()): move(p,CORE)
    for r in rows:
        p=Path(r['path'])
        if not p.exists(): continue
        if r['action']=='MOVE_CORE': move(p,CORE)
        elif r['action']=='MOVE_DOCS': move(p,DOCS)
        else: print('GAP_PRESERVED',p)
    Path('organize-yaiwes-audit.json').unlink(missing_ok=True)

def components():
    if not CORE.exists(): return []
    return sorted([p for p in CORE.iterdir() if p.is_dir()],key=lambda p:p.name.lower())

def index():
    cs=components(); lines=['# Índice de componentes open source Yaiwes','','## Parte 1 — Índice lista Simple enumerado','']
    lines += [f'{i}. **{p.name}**' for i,p in enumerate(cs,1)] or ['_Sin componentes clasificados._']
    lines += ['','## Parte 2 — Índice enumerado detallado de cada componente','']
    for i,p in enumerate(cs,1):
        files=[x for x in p.rglob('*') if x.is_file()]; manifests=[x.name for x in files if x.name.lower() in {'readme.md','package.json','pyproject.toml','go.mod','cargo.toml'}]
        evidence=', '.join(sorted(set(manifests))) if manifests else 'sin manifiesto/README detectado; detalle no inventado'
        lines += [f'### {i}. {p.name}',f'- **Ubicación:** `{CORE}/{p.name}/`',f'- **Archivos:** {len(files)}',f'- **Evidencia disponible:** {evidence}',f'- **Función:** componente existente consolidado en Core/Kernel Yaiwes; revisar su documentación interna para semántica adicional.','']
    INDEX.write_text('\n'.join(lines).rstrip()+'\n')

def verify():
    bad=[]
    for p in ROOT.iterdir():
        if p.name in KEEP or p.name.startswith('.git'): continue
        if (p.is_file() and is_code(p)) or has_code(p): bad.append(str(p))
    if bad: print('CODE_OUTSIDE_CORE',*bad,sep='\n'); raise SystemExit(73)
    if COMP.exists() and any(COMP.iterdir()): raise SystemExit('FUTURE_COMPONENT_ROOT_NOT_EMPTY')
    if not INDEX.exists(): raise SystemExit('INDEX_GAP')
    print('ORGANIZATION_VERIFIED')

if __name__=='__main__':
    cmd=sys.argv[1] if len(sys.argv)>1 else ''
    {'audit':audit,'apply':apply,'index':index,'verify':verify}.get(cmd,lambda:sys.exit('use audit|apply|index|verify'))()
