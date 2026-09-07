# Claude Chat ↔ GitHub — handoff de instalación

Estado: preparación automatizada terminada hasta el primer punto que requiere aprobación humana.

## Vía A — GitHub MCP oficial (sin PAT manual)

1. Instala `Claude Github MCP Connector` en la cuenta GitHub `maxbry123-commits`.
2. En Repository access elige **All repositories**.
3. En Claude Chat → Configuración → Conectores → Agregar conector personalizado:
   - Nombre: `GitHub Official`
   - URL: `https://api.githubcopilot.com/mcp/`
   - Requiere inicio de sesión: **Sí**
   - OAuth Client ID: vacío
   - OAuth Client Secret: vacío
4. Autoriza la cuenta GitHub `maxbry123-commits`.
5. Prueba únicamente en rama `claude-mcp-write-test` hasta certificar lectura + escritura + edición + borrado.

## Vía B — MCP propio en Hugging Face (PAT dedicado)

### GitHub PAT

Crea un fine-grained PAT nuevo y exclusivo para este MCP:

- Resource owner: `maxbry123-commits`
- Repository access: **All repositories**
- Administration: Read and write
- Contents: Read and write
- Workflows: Read and write
- Actions: Read and write
- Issues: Read and write
- Pull requests: Read and write
- Commit statuses: Read and write

No reutilizar el token de GPT/otras automatizaciones.

### Hugging Face Space

Crea exactamente este Space bajo la cuenta `COMAND-CENTER-1`:

- Nombre: `claude-github-mcp-backup`
- SDK: Docker
- Visibilidad: Public (el protocolo debe ser alcanzable desde Claude; el MCP exige OAuth antes de ejecutar herramientas)

Después, en Settings → Variables and secrets:

- Secret: `GITHUB_PERSONAL_ACCESS_TOKEN` = el PAT nuevo de GitHub
- Variable opcional: `GITHUB_DEFAULT_OWNER=maxbry123-commits`
- Variable opcional: `MCP_ALLOWED_HF_USERS=COMAND-CENTER-1`

### Trusted Publisher (sin guardar token de Hugging Face en GitHub)

En Settings del Space → Trusted Publishers → Add:

- Provider: GitHub Actions
- repository: `maxbry123-commits/agentes`
- branch: `claude-mcp-write-test`
- workflow: `deploy-claude-mcp-b.yml`

El workflow ya existe y usa OIDC; no necesita `HF_TOKEN` permanente.

### Claude custom connector B

Después del despliegue verificado:

- Nombre: `GitHub Backup HF`
- URL esperada: `https://comand-center-1-claude-github-mcp-backup.hf.space/mcp`
- Requiere inicio de sesión: **Sí**
- OAuth Client ID: vacío
- OAuth Client Secret: vacío

No usar la URL como certificada hasta comprobar el hostname real del Space desplegado.

## Prueba de aceptación

En ambas vías, antes de tocar trabajo real:

1. listar repositorios;
2. leer `CLAUDE_MCP_WRITE_TEST.md` desde `agentes@claude-mcp-write-test`;
3. editar `claude-mcp-tests/EDIT_ME.md`;
4. crear un archivo nuevo bajo `claude-mcp-tests/`;
5. borrar exclusivamente `claude-mcp-tests/DELETE_ME.md`;
6. verificar físicamente los SHA/commits en GitHub.

`main` queda fuera de estas pruebas.
