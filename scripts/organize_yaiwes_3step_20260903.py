#!/usr/bin/env python3
"""Three-step Yaiwes repository organizer. Fail-closed: ambiguous/code files are never deleted."""
from __future__ import annotations
import hashlib, json, os, shutil, sys
from pathlib import Path

ROOT=Path('.')
CORE=Path('Core kernel Yaiwes')
COMP=Path('Componentes open source Yaiwes')
DOCS=Path('Documentos proyectos Yaiwes')
AGENT=Path('Agente Yaiwes principal')
DOWNLOAD=Path('Download & desplegar code Yaiwes')
INDEX=Path('INDICE-COMPONENTES-OPEN-SOURCE-YAIWES.md')
KEEP_TOP={'.git','.github','.cursor','skills','scripts',CORE.name,COMP.name,DOCS.name,AGENT.name,DOWNLOAD.name,INDEX.name}
CODE_EXT={'.py','.js','.jsx','.ts','.tsx','.go','.rs','.java','.kt','.kts','.c','.h','.cc','.cpp','.hpp','.cs','.rb','.php','.swift','.scala','.sh','.bash','.zsh','.fish','.ps1','.sql','.proto','.sol','.vue','.svelte','.dart','.ex','.exs','.erl','.hrl','.fs','.fsx','.clj','.cljs','.lua','.r','.m','.mm','.gradle','.cmake'}
DOC_EXT={'.md','.txt','.rst','.adoc','.pdf','.doc','.docx','.odt','.rtf'}
CORE_WORDS=('core','kernel','control','capa-control','capa_de_control','yaiwes-core')

def sha(p:Path):
    h=hashlib.sha256();
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def is_code_file(p:Path):
    if p.suffix.lower() in CODE_EXT: return True
    if p.name in {'Dockerfile','Makefile','CMakeLists.txt','package.json','pyproject.toml','go.mod','Cargo.toml','requirements.txt'}: return True
    return False

def tree_has_code(p:Path): return p.is_dir() and any(is_code_file(x) for x in p.rglob('*') if x.is_file())
def coreish(p:Path):
    s=p.name.lower().replace(' ','-')
    return any(w in s for w in CORE_WORDS)

def unique_dest(base:Path,name:str):
    d=base/name
    if not d.exists(): return d
    i=2
    while (base/f'{name}-{i}').exists(): i+=1
    return base/f'{name}-{i}'

def audit():
    rows=[]
    for p in sorted(ROOT.iterdir(),key=lambda x:x.name.lower()):
        if p.name in KEEP_TOP: continue
        if p.is_dir() and tree_has_code(p): action='MOVE_CORE' if coreish(p) else 'MOVE_DOWNLOAD_CODE'
        elif p.is_file() and is_code_file(p): action='MOVE_DOWNLOAD_CODE'
        elif p.is_file() and p.suffix.lower() in DOC_EXT: action='MOVE_DOCS'
        elif p.is_dir(): action='DELETE_NONCODE_TREE'
        else: action='DELETE_NONCODE'
        rows.append({'path':str(p),'action':action})
    Path('organize-yaiwes-audit.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(rows,indent=2,ensure_ascii=False))

def move(p:Path,base:Path):
    base.mkdir(parents=True,exist_ok=True)
    d=unique_dest(base,p.name)
    shutil.move(str(p),str(d)); print('MOVE',p,'->',d)

def apply():
    if not Path('organize-yaiwes-audit.json').exists(): audit()
    rows=json.loads(Path('organize-yaiwes-audit.json').read_text())
    CORE.mkdir(exist_ok=True); COMP.mkdir(exist_ok=True); DOCS.mkdir(exist_ok=True); AGENT.mkdir(exist_ok=True); DOWNLOAD.mkdir(exist_ok=True)
    for r in rows:
        p=Path(r['path'])
        if not p.exists(): continue
        a=r['action']
        if a=='MOVE_CORE': move(p,CORE)
        elif a=='MOVE_DOWNLOAD_CODE': move(p,DOWNLOAD)
        elif a=='MOVE_DOCS': move(p,DOCS)
        elif a.startswith('DELETE_'):
            # fail closed: never delete a tree that contains recognized code
            if p.is_dir() and tree_has_code(p): move(p,DOWNLOAD); continue
            if p.is_file() and is_code_file(p): move(p,DOWNLOAD); continue
            shutil.rmtree(p) if p.is_dir() else p.unlink(); print('DELETE',p)
    # Deduplicate identical files outside operational metadata; preserve first canonical copy.
    seen={}
    for base in (CORE,DOCS,DOWNLOAD):
        for p in sorted(base.rglob('*')):
            if not p.is_file(): continue
            key=(p.stat().st_size,sha(p))
            if key in seen:
                p.unlink(); print('DELETE_DUPLICATE',p,'same-as',seen[key])
            else: seen[key]=p
    Path('organize-yaiwes-audit.json').unlink(missing_ok=True)

def components():
    # Existing selected components belong to Core Kernel. The open-source folder is intentionally reserved for future arrivals.
    out=[]
    if CORE.exists():
        for p in sorted((x for x in CORE.iterdir() if x.is_dir()),key=lambda x:x.name.lower()):
            files=[x for x in p.rglob('*') if x.is_file()]
            exts=sorted({x.suffix.lower() for x in files if x.suffix})[:8]
            out.append((p.name,len(files),exts))
    return out

def index():
    cs=components()
    lines=['# Índice de componentes Yaiwes','','## Parte 1 — Lista simple','']
    lines += [f'{i}. **{n}**' for i,(n,_,_) in enumerate(cs,1)] or ['_Sin componentes clasificados._']
    lines += ['','## Parte 2 — Índice detallado','']
    for i,(n,count,exts) in enumerate(cs,1):
        tech=', '.join(exts) if exts else 'sin extensiones de código detectadas'
        lines += [f'### {i}. {n}',f'- **Ubicación:** `{CORE}/{n}/`',f'- **Contenido:** {count} archivos.',f'- **Función inferida:** componente seleccionado de Core/Kernel Yaiwes; tecnologías detectadas: {tech}.','']
    INDEX.write_text('\n'.join(lines).rstrip()+'\n')

def verify():
    # No recognized code may remain loose at top level.
    bad=[]
    for p in ROOT.iterdir():
        if p.name in KEEP_TOP or p.name.startswith('.git'): continue
        if (p.is_file() and is_code_file(p)) or (p.is_dir() and tree_has_code(p)): bad.append(str(p))
    if bad:
        print('CODE_OUTSIDE_CANONICAL_ROOT',*bad,sep='\n'); raise SystemExit(73)
    # Future component intake directory must be empty.
    if COMP.exists() and any(COMP.iterdir()):
        print('COMPONENTS_FUTURE_ROOT_NOT_EMPTY'); raise SystemExit(73)
    if not INDEX.exists(): raise SystemExit('INDEX_GAP')
    print('ORGANIZATION_VERIFIED')

if __name__=='__main__':
    cmd=sys.argv[1] if len(sys.argv)>1 else ''
    {'audit':audit,'apply':apply,'index':index,'verify':verify}.get(cmd,lambda:sys.exit('use audit|apply|index|verify'))()
