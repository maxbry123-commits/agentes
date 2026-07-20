# 09 · Workflow Registry

## Propósito
Catálogo de **flujos completos pre-armados** (un workflow = secuencia de skills + tools + agents, con DAG). Cubre casos como "Deploy → Git → Docker → Railway".

## Schema (v0.1)
```json
{
  "title": "Workflow",
  "type": "object",
  "required": ["id", "name", "version", "dag"],
  "properties": {
    "id":          { "type": "string" },
    "name":        { "type": "string" },
    "version":     { "type": "string" },
    "dag":         { "type": "object", "description": "nodos + edges" },
    "inputs":      { "type": "object" },
    "outputs":     { "type": "object" },
    "tags":        { "type": "array", "items": { "type": "string" } },
    "owner":       { "type": "string" }
  }
}
```

## Catálogo (5 workflows — seed)

| id | nombre | descripción | skills |
|----|--------|-------------|--------|
| `wf.deploy.docker`      | Deploy Docker local | test → build → restart | `test-runner`, `terminal` |
| `wf.git.pr`             | PR a GitHub | branch → commit → push → PR | `git` |
| `wf.railway.up`         | Deploy Railway | railway up → domain | `terminal` |
| `wf.openapi.skill-audit`| Auditar skill OpenClaw | fetch → static check → run → report | `url-reader`, `terminal`, `test-runner` |
| `wf.harness-failover`   | Failover de harness | ping primario → si falla → secundario | `terminal` |

---

## wf.deploy.docker (v0.1)

```json
{
  "id": "wf.deploy.docker",
  "name": "Deploy Docker local",
  "version": "0.1.0",
  "owner": "M3",
  "inputs": { "service": "string", "image_tag": "string" },
  "outputs": { "container_id": "string", "status": "enum[ok,fail]" },
  "tags": ["deploy","docker","vps"],
  "dag": {
    "nodes": [
      {"id":"n1","skill":"test-runner","action":"auto","params":{"path":"."}},
      {"id":"n2","skill":"terminal","action":"docker_build","params":{"tag":"$inputs.image_tag"}},
      {"id":"n3","skill":"terminal","action":"docker_stop","params":{"service":"$inputs.service"}},
      {"id":"n4","skill":"terminal","action":"docker_run","params":{"tag":"$inputs.image_tag"}},
      {"id":"n5","skill":"terminal","action":"healthcheck","params":{"path":"/health"}}
    ],
    "edges": [
      {"from":"n1","to":"n2","on":"ok"},
      {"from":"n2","to":"n3","on":"ok"},
      {"from":"n3","to":"n4","on":"ok"},
      {"from":"n4","to":"n5","on":"ok"}
    ]
  }
}
```

## wf.git.pr (v0.1)

```json
{
  "id": "wf.git.pr",
  "name": "PR a GitHub",
  "version": "0.1.0",
  "owner": "M3",
  "inputs": { "branch": "string", "title": "string", "body": "string" },
  "outputs": { "pr_number": "integer", "pr_url": "string" },
  "tags": ["git","github","pr"],
  "dag": {
    "nodes": [
      {"id":"n1","skill":"git","action":"branch","params":{"name":"$inputs.branch"}},
      {"id":"n2","skill":"git","action":"commit","params":{"message":"wip"}},
      {"id":"n3","skill":"git","action":"push","params":{"branch":"$inputs.branch"}},
      {"id":"n4","skill":"git","action":"pr","params":{"title":"$inputs.title","body":"$inputs.body"}}
    ],
    "edges": [
      {"from":"n1","to":"n2","on":"ok"},
      {"from":"n2","to":"n3","on":"ok"},
      {"from":"n3","to":"n4","on":"ok"}
    ]
  }
}
```

## wf.railway.up (v0.1)

```json
{
  "id": "wf.railway.up",
  "name": "Deploy Railway",
  "version": "0.1.0",
  "owner": "M3",
  "inputs": { "service_dir": "string" },
  "outputs": { "deploy_id": "string", "domain": "string" },
  "tags": ["deploy","railway"],
  "dag": {
    "nodes": [
      {"id":"n1","skill":"terminal","action":"railway_up","params":{"cwd":"$inputs.service_dir"}},
      {"id":"n2","skill":"url-reader","action":"fetch","params":{"url":"https://$n1.domain/health"}}
    ],
    "edges": [{"from":"n1","to":"n2","on":"ok"}]
  }
}
```

## wf.openapi.skill-audit (v0.1)

```json
{
  "id": "wf.openapi.skill-audit",
  "name": "Auditar skill contra agentskills.io",
  "version": "0.1.0",
  "owner": "M3",
  "inputs": { "repo": "string", "skill_path": "string" },
  "outputs": { "verdict": "enum[pass,warn,fail]", "report_url": "string" },
  "tags": ["audit","skill","compliance"],
  "dag": {
    "nodes": [
      {"id":"n1","skill":"url-reader","action":"fetch","params":{"url":"https://raw.githubusercontent.com/$inputs.repo/main/$inputs.skill_path/SKILL.md"}},
      {"id":"n2","skill":"terminal","action":"validate_yaml_frontmatter","params":{"content":"$n1.markdown"}},
      {"id":"n3","skill":"test-runner","action":"pytest","params":{"path":"$inputs.skill_path/scripts"}},
      {"id":"n4","skill":"terminal","action":"render_report","params":{"inputs":["$n1","$n2","$n3"]}}
    ],
    "edges": [
      {"from":"n1","to":"n2","on":"ok"},
      {"from":"n2","to":"n3","on":"ok"},
      {"from":"n3","to":"n4","on":"ok"}
    ]
  }
}
```

## wf.harness-failover (v0.1)

```json
{
  "id": "wf.harness-failover",
  "name": "Failover entre harnesses",
  "version": "0.1.0",
  "owner": "M3",
  "inputs": { "task": "object" },
  "outputs": { "harness_used": "string", "result": "object" },
  "tags": ["failover","harness","resilience"],
  "dag": {
    "nodes": [
      {"id":"n1","skill":"terminal","action":"ping","params":{"host":"daytona.app"}},
      {"id":"n2","skill":"terminal","action":"ping","params":{"host":"api.e2b.dev"}},
      {"id":"n3","skill":"terminal","action":"ping","params":{"host":"api.sandbank.dev"}},
      {"id":"n4","skill":"terminal","action":"run","params":{"harness":"$route","task":"$inputs.task"}}
    ],
    "edges": [
      {"from":"n1","to":"n4","condition":"n1.ok==true","priority":1},
      {"from":"n2","to":"n4","condition":"n1.ok==false AND n2.ok==true","priority":2},
      {"from":"n3","to":"n4","condition":"n1.ok==false AND n2.ok==false AND n3.ok==true","priority":3}
    ]
  }
}
```

## Validador estático de DAG (pendiente)

```python
# spec, NO instalable
def validate_dag(dag):
    # - no ciclos (DFS con memo)
    # - todos los nodos son alcanzables
    # - cada 'from' apunta a un nodo existente
    # - cada 'on' es un valor conocido (ok, fail, ...)
    pass
```

## Tareas pendientes
- [ ] Implementar `validate_dag` con tests.
- [ ] Migrar workflows del repo `osquestador-auditor` a este registry.
- [ ] Versionar cada cambio de un workflow (mantener historial).
- [ ] Render visual del DAG (mermaid) en `validation.html`.
