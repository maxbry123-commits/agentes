# G2 · RESEARCH ENGINE — Documento 2/4
**Bloques B3 (Fuentes/Contratos) + B4 (Resolver/Mirror/Contexto) · UOOS Parte 1**
Fuente: `arquitectura_Wordflow.md`, Salida 6/13, líneas 3986-4278, literal

---

## B3 · Fuentes de investigación + Skills

El motor tiene adaptadores separados — no se confía en una sola fuente:

```
Research Providers
├── GitHub
├── GitLab
├── Codeberg
├── Hugging Face
├── PyPI
├── npm
├── crates.io
├── Docker/OCI
├── documentación oficial
└── referencias técnicas/papers
```

Prioridad de las fuentes: 1) código oficial, 2) documentación oficial, 3) releases/tags, 4) issues/PRs, 5) implementaciones relacionadas, 6) documentación comunitaria.

Regla dura del Sheriff (no interpretativa): `minimum_sources >= 20`. Con 13 resultados válidos, por ejemplo, el estado es `RESEARCH_INCOMPLETE` y el Workflow no permite pasar a construcción.

Skill Registry — cada tarea declara sus skills obligatorios:

```python
@dataclass(frozen=True)
class SkillRequirement:
    skill_id: str
    required: bool
```

```
Skill Registry
├── frontend      ├── security      ├── GitHub
├── backend       ├── databases     ├── Docker
├── testing       ├── deployment    ├── AI agents
└── project-specific
```

Si falta un skill obligatorio: `SKILL_MISSING → Research → Skill acquisition → Validation → continue`.

Regla importante de la fuente: el agente recibe *existing source + requirements + architecture + skills* — nunca simplemente "construye X desde cero". Puede crear código nuevo cuando haga falta, pero primero debe haber pasado por Research.

---

## B4 · Repository Resolver, descarga determinista, Mirror, Context Builder

Una investigación puede encontrar un paquete en PyPI que apunta a un GitHub oficial, que apunta a un release, que apunta a un commit — el sistema resuelve el repositorio fuente antes de descargar:

```python
class RepositoryResolver:

    def resolve(
        self,
        finding: ResearchFinding,
    ) -> str:
        ...
```

Descarga determinista — nunca `git clone main` como mecanismo de reproducción. Se registra: repository, branch, tag, commit SHA, download timestamp, content hash.

```
Repository → commit SHA → Mirror → SHA-256 → Research Evidence
```

Así el agente sabe exactamente qué código estudió.

Repository Mirror:
```
workspace/repository-mirrors/
├── frontend/  (repo-001, repo-002, ...)
├── backend/
├── workflow/
├── sandbox/
├── memory/
└── infrastructure/
```
Los mirrors son fuentes de estudio y trabajo — no automáticamente repositorios de producción.

Context Builder — no se envía todo el repositorio al agente, se construye un contexto acotado:
```
Context
├── objective            ├── selected repositories
├── relevant documents   ├── relevant files
├── architecture decision├── required skills
├── previous failures    ├── checkpoints
└── constraints
```

Ask Preview — antes de entregar el contexto completo: `Research → Preview → relevant files → relevant symbols → relevant dependencies → final context`. El sistema evita cargar 10.000 archivos si realmente solo necesita 47.

---

*Siguiente: Documento 3/4 — B5 (Skills como mecanismo de soporte) + B6 (Contrato Sheriff de Research: ALLOW/DENY).*
