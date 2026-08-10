# PIPELINE 24 — GitHub Publisher Status (Objetivo 4)

**llm_control:** DENY  
**Extensión:** `extensions/github_publisher/`

## Entregado A-DEP-01 … A-DEP-02

| ID | Entrega | Estado |
|----|---------|--------|
| A-DEP-01 | Publisher + token_ref + FakeGitHubPort | DONE |
| A-DEP-02 | BUILD bridge + manifest + CI | DONE |

## Contrato

```
github_publish:
  token_ref: github_token   # NUNCA token literal
  repository: user/repo
  branch: main
  files: [{source, destination, content?}]
  commit_message: "..."
```

## Flujo

```
Wordflow BUILD/
    → build_publish_request
    → resolve token_ref (Credential Store)
    → GitHubPort.create_commit
    → commit_sha (sin token en output)
```

## Tests: 9/9 PASSED offline

## Pendiente

- Real GitHub Contents/Git Data API adapter (runtime)
