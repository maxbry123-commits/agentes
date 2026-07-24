# OpenClaw API — Documentación

**Versión instalada**: 2026.7.1-2 (0790d9f593ad)
**Path**: /usr/lib/node_modules/openclaw/
**PID activo**: 452428
**Puerto**: 18789
**Token actual**: <REDACTED> (rotado FASE 26)

---

## 🌐 Endpoints HTTP (OpenAI-compat)

| Endpoint | Método | Función |
|---|---|---|
| `/v1/chat/completions` | POST | Chat completions (OpenAI compatible) |
| `/v1/models` | GET | Lista modelos disponibles |
| `/v1/models/:model` | GET | Detalle de modelo |
| `/v1/embeddings` | POST | Genera embeddings |
| `/v1/responses` | POST | Responses API |
| `/v1/foreigns` | GET | Foreign models |
| `/v1/native` | GET | Native models |
| `/v1/news` | GET | News del gateway |
| `/v1/token` | GET | Token info |
| `/v1/token_plan/remains` | GET | Token plan remaining |
| `/v1/coding_plan/vlm` | POST | Coding plan VLM |
| `/v1/image_to_video` | POST | Image to video generation |
| `/v1/text_to_video` | POST | Text to video generation |
| `/v1/video_to_video` | POST | Video to video transformation |
| `/chat` | POST | Chat (legacy) |

## 🌐 Endpoints Web (Browser automation)

| Endpoint | Método | Función |
|---|---|---|
| `/` | GET | Index |
| `/console` | GET | Console |
| `/cookies` | GET/POST | Cookies management |
| `/cookies/clear` | POST | Clear cookies |
| `/cookies/set` | POST | Set cookies |
| `/dialogs` | GET | Browser dialogs |
| `/doctor` | GET | Health check |
| `/errors` | GET | Errors |
| `/profiles` | GET | Browser profiles |
| `/profiles/:name` | DELETE | Delete profile |
| `/profiles/create` | POST | Create profile |
| `/requests` | GET | Pending requests |
| `/sandbox` | GET | Sandbox info |
| `/screenshot` | POST | Take screenshot |
| `/snapshot` | GET | Snapshot |
| `/storage/:kind` | GET | Storage access |
| `/tabs` | GET | Open tabs |
| `/tabs/:targetId` | DELETE | Close tab |
| `/navigate` | POST | Navigate browser |
| `/pdf` | POST | PDF generation |
| `/act` | POST | Browser action |
| `/download` | POST | Download file |
| `/highlight` | POST | Highlight element |
| `/hooks/dialog` | POST | Dialog hook |
| `/hooks/file-chooser` | POST | File chooser hook |
| `/response/body` | POST | Response body |
| `/permissions/grant` | POST | Grant permission |
| `/set/credentials` | POST | Set credentials |
| `/set/device` | POST | Set device |
| `/set/geolocation` | POST | Set geolocation |

## 🔌 MCP (Model Context Protocol)

OpenClaw incluye soporte MCP nativo. Archivos clave:
- `agent-bundle-mcp-filter-DA8pW_vZ.js`
- `agent-bundle-mcp-materialize-D9l-gQ5S.js`
- `agent-bundle-mcp-names-B9PLR-i_.js`

Configuración en `openclaw.json` bajo `mcp.servers`.

## 📚 Skills (integradas)

Directorio `/usr/lib/node_modules/openclaw/skills/`
- 100+ skills bundled
- Sistema de plugins extensible

## 🔌 Plugins

Sistema de plugins via `openclaw/plugin-sdk`
- Plugins en `/usr/lib/node_modules/openclaw/plugins/`
- Carga via `plugins.entries.*.enabled: true` en config

## 🖥️ Harnesses (runtimes alternativos)

| Harness ID | Función |
|---|---|
| `openclaw` (alias `pi`) | Built-in |
| `codex` | OpenAI Codex |
| `copilot` | GitHub Copilot |
| `claude-cli` | Anthropic Claude CLI |

## 📡 Canales (channels)

Telegram, Discord, Slack, WhatsApp, Signal, iMessage, Line, Mattermost, Gmail, Webhook, etc.
Config en `channels.entries.*.enabled`.

## 🔐 Autenticación

- Modo: `token`
- Header: `Authorization: Bearer <token>`
- Token actual: `<REDACTED>`

## 📋 Comandos CLI

| Comando | Función |
|---|---|
| `openclaw gateway` | Arranca gateway |
| `openclaw gateway --force` | Forzar reinicio |
| `openclaw onboard` | Onboarding |
| `openclaw doctor` | Health check |
| `openclaw config set` | Set config |
| `openclaw memory add` | Add memory |
| `openclaw harness list` | List harnesses |
| `openclaw dashboard --no-open` | URL panel |

## 🔗 Conectividad verificada

- Local: `http://127.0.0.1:18789/`
- DuckDNS: `https://maxbry1.duckdns.org:8443/`
- Token query: `?token=<REDACTED>`
- WebSocket: `ws://127.0.0.1:18789/`
