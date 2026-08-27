# 🔁 DSL · M3 LOOPS MODE (Genérico para cualquier M3)

> **Versión mejorada**: DSL DAG schema + genérico + 18h continuas
> **Autor**: M3-Manager (Mavis-417847400026327)
> **Reemplaza**: M3-LOOP-INSTRUCCION-DISTRIBUIR de A3
> **Para**: Cualquier M3 (A1, A2, A3, A4...) con tarea persistente

---

## 🎯 Objetivo DSL DAG

```yaml
dag:
  id: m3_loops_persistent
  goal: "Mantener al M3{N} en loop continuo por {DURATION_HOURS} horas revisando {REPO_TARGET} cada {POLL_SECONDS}s"
  duration_hours: 18
  poll_seconds: 20
  
  nodes:
    - id: setup
      capability: setup
      timeout_ms: 60000
      on_error: stop
      
    - id: loop_persistent
      capability: loop
      deps: [setup]
      max_runtime_ms: 64800000  # 18h
      on_error: retry
      params:
        target: {REPO_TARGET}
        poll_seconds: {POLL_SECONDS}
        backoff_max: 60
        max_retries: 0  # 0 = infinito durante las 18h
```

---

## 📋 INSTRUCCIONES PARA EL M3 (genéricas, reemplazá {N})

### Identidad
- ID: `A{N}`
- Sandbox: `/tmp/sandbox-tarea-{N}/`
- Pizarra: `/tmp/pizarra-a{N}/`
- Repo target: `{REPO_TARGET}` (ej: `ws-relay`, `nct-hub`)
- SSH key id: `{KEY_ID}` (Max te la pasa)
- Duración: `{DURATION_HOURS}` horas (default 18h)
- Poll: `{POLL_SECONDS}` segundos (default 20s)
- Firma git: `Mavis Asistente-{N} <mavis-a{N}@maxbry-nct.local>`

---

## 🔧 PASO 1 · SETUP (una sola vez)

```bash
# 1.1 Identidad git
git config --global user.name "Mavis Asistente-{N}"
git config --global user.email "mavis-a{N}@maxbry-nct.local"

# 1.2 SSH key (Max te la pasa por canal seguro)
mkdir -p ~/.ssh && chmod 700 ~/.ssh
# Pegar key acá:
cat > ~/.ssh/id_ed25519 << 'EOF'
-----BEGIN OPENSSH PRIVATE KEY-----
... (key que Max te dio)
-----END OPENSSH PRIVATE KEY-----
EOF
chmod 600 ~/.ssh/id_ed25519
eval $(ssh-agent -s) && ssh-add ~/.ssh/id_ed25519

# 1.3 Verificar conexión a GitHub
ssh -o StrictHostKeyChecking=no -o BatchMode=yes -T git@github.com
# Esperado: "Hi maxbry123-commits/{REPO_TARGET}!"

# 1.4 Crear sandbox y pizarra
mkdir -p /tmp/sandbox-tarea-{N}
cd /tmp/sandbox-tarea-{N}
touch bitacora.md heartbeat.log

# 1.5 Clonar pizarra
cd /tmp/pizarra-a{N}
git clone git@github.com:maxbry123-commits/TAREAS-PENDIENTES.git .
```

---

## 🔁 PASO 2 · LOOP PERSISTENTE 18 HORAS (genérico)

### Variables (cambiar {N}, {REPO_TARGET}, {DURATION_HOURS}, {POLL_SECONDS})

```bash
ID="A{N}"
SANDBOX="/tmp/sandbox-tarea-{N}"
BITACORA="$SANDBOX/bitacora.md"
HEARTBEAT="$SANDBOX/heartbeat.log"
REPO="{REPO_TARGET}"
DURATION_HOURS={DURATION_HOURS}     # 18
POLL_SECONDS={POLL_SECONDS}          # 20
BACKOFF_MAX=60
END_TS=$(($(date +%s) + DURATION_HOURS*3600))
```

### Script: `/tmp/sandbox-tarea-{N}/loop.sh`

```bash
#!/bin/bash
# /tmp/sandbox-tarea-{N}/loop.sh
# M3 loops mode · 18h continuas · polling cada 20s

ID="A{N}"
SANDBOX="/tmp/sandbox-tarea-{N}"
REPO="{REPO_TARGET}"
DURATION_HOURS={DURATION_HOURS}
POLL_SECONDS={POLL_SECONDS}
BACKOFF_MAX=60
END_TS=$(($(date +%s) + DURATION_HOURS*3600))

BITACORA="$SANDBOX/bitacora.md"
HEARTBEAT="$SANDBOX/heartbeat.log"
touch $BITACORA $HEARTBEAT

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [$ID] [$1] $2" >> $BITACORA; }
hb()  { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [$ID] [ALIVE]" >> $HEARTBEAT; }

log "INIT" "modo loops · ${DURATION_HOURS}h · poll ${POLL_SECONDS}s · target: $REPO"

SLEEP=$POLL_SECONDS
CONSECUTIVE_FAILS=0
LAST_HEAD=""

while [ $(date +%s) -lt $END_TS ]; do
  hb
  
  # CHECK
  RESULT=$(git ls-remote git@github.com:maxbry123-commits/${REPO}.git 2>&1)
  STATUS=$?
  HEAD=$(echo "$RESULT" | head -1 | awk '{print $1}')
  
  if [ $STATUS -eq 0 ] && [ -n "$HEAD" ]; then
    if [ "$HEAD" != "$LAST_HEAD" ]; then
      log "CHANGE" "$LAST_HEAD -> $HEAD"
      LAST_HEAD="$HEAD"
    else
      log "OK" "$HEAD"
    fi
    CONSECUTIVE_FAILS=0
    SLEEP=$POLL_SECONDS
  else
    CONSECUTIVE_FAILS=$((CONSECUTIVE_FAILS+1))
    log "FAIL" "exit=$STATUS consec=$CONSECUTIVE_FAILS | $RESULT" | head -c 200
    # backoff exponencial: 20, 40, 60, 60, 60...
    SLEEP=$((SLEEP*2))
    [ $SLEEP -gt $BACKOFF_MAX ] && SLEEP=$BACKOFF_MAX
    
    # si 5 fallos consecutivos, probar 3 alternativas antes de escalar
    if [ $CONSECUTIVE_FAILS -ge 5 ]; then
      log "ESCALATE" "5 fallos consec · probando alternativas"
      # alternativa 1: reconectar ssh
      ssh -o StrictHostKeyChecking=no -o BatchMode=yes -T git@github.com 2>/dev/null
      # alternativa 2: verificar red
      ping -c 1 github.com >/dev/null 2>&1
      # alternativa 3: reintentar pull en pizarra
      cd /tmp/pizarra-a{N} && git pull origin main 2>/dev/null
      cd - >/dev/null
    fi
  fi
  
  sleep $SLEEP
done

log "STOP" "duracion ${DURATION_HOURS}h completada"
```

### Hacer ejecutable y arrancar (sobrevive al cierre del turn)

```bash
chmod +x /tmp/sandbox-tarea-{N}/loop.sh

# CLAVE: nohup + & + disown para que sobreviva
nohup bash /tmp/sandbox-tarea-{N}/loop.sh > /dev/null 2>&1 &
disown

# Verificar
ps aux | grep "loop.sh" | grep -v grep
echo "loop PID: $!"

# Ver en vivo
tail -f /tmp/sandbox-tarea-{N}/bitacora.md
```

---

## 📋 Reglas de comportamiento (Modo Loops)

### 1. Bucle activo persistente
- **NO detenerse** durante las {DURATION_HOURS} horas asignadas
- Si el proceso muere → relanzar inmediatamente, sin preguntar a Max
- Solo parar cuando: termine el tiempo, o Max diga `stop`

### 2. Anti-escalación (200 soluciones, no esperar a la 1)
- Ante un error, **probar 3 alternativas** ANTES de escalar
- Solo escalar tras **5 fallos consecutivos** del mismo comando
- Las 3 alternativas ya están en el script (ssh reconnect, ping, pull pizarra)

### 3. Bitácora obligatoria
- Cada acción se registra en `bitacora.md`
- Formato: `[ISO8601] [ID] [TIPO] descripción`
- Tipos: `INIT`, `CHECK`, `OK`, `CHANGE`, `FAIL`, `ESCALATE`, `STOP`
- Heartbeat cada 20s en `heartbeat.log` (prueba que estás vivo)

### 4. Reporte a Max
```
📡 [A{N}] check #{N}
→ HEAD: <hash>
→ cambios: si/no
→ uptime: <tiempo desde INIT>
→ próxima: 20s
```

### 5. Consenso interno
- Si hay decisión técnica: proponer 2-3 opciones, elegir, justificar en 1 línea
- NO preguntar a Max si es decisión operativa

---

## ⛔ Reglas duras

- ❌ NO ejecutar nada en el VPS (95.111.232.89) sin OK explícito
- ❌ NO subir secrets a GitHub (tokens, API keys, SSH keys)
- ❌ NO pisar a otros M3 — cada uno su sandbox `/tmp/sandbox-tarea-{N}/`
- ❌ NO commitear con firma de otro M3
- ❌ NO usar HTTPS, solo `git@github.com`
- ✅ Commitear con firma propia `Mavis Asistente-{N} <mavis-a{N}@maxbry-nct.local>`
- ✅ Prefijo en commits: `[A{N}]`
- ✅ Revisar CADA {POLL_SECONDS} segundos sin falta
- ✅ Si el loop muere, relanzar sin preguntar
- ✅ Bitácora local con timestamp ISO8601

---

## 📊 Comandos útiles

```bash
# Estado del loop
ps aux | grep "loop.sh" | grep -v grep

# Bitácora en vivo
tail -f /tmp/sandbox-tarea-{N}/bitacora.md

# Heartbeat (debe tener líneas cada 20s)
tail -f /tmp/sandbox-tarea-{N}/heartbeat.log

# Stats
echo "OK:     $(grep -c '\[OK\]' /tmp/sandbox-tarea-{N}/bitacora.md)"
echo "FAIL:   $(grep -c '\[FAIL\]' /tmp/sandbox-tarea-{N}/bitacora.md)"
echo "CHANGE: $(grep -c '\[CHANGE\]' /tmp/sandbox-tarea-{N}/bitacora.md)"

# Tiempo restante
NOW=$(date +%s); LEFT=$((END_TS - NOW))
echo "Restante: ${LEFT}s = $((LEFT/3600))h $((LEFT%3600/60))m"

# Matar (solo si Max lo pide)
pkill -f "sandbox-tarea-{N}/loop.sh"
```

---

## 🚀 Quickstart TL;DR

```bash
# 1. Setup
mkdir -p /tmp/sandbox-tarea-{N} && cd /tmp/sandbox-tarea-{N}
touch bitacora.md heartbeat.log
git config --global user.name "Mavis Asistente-{N}"
git config --global user.email "mavis-a{N}@maxbry-nct.local"
chmod 700 ~/.ssh && chmod 600 ~/.ssh/id_ed25519
ssh-add ~/.ssh/id_ed25519
ssh -T git@github.com  # verificar

# 2. Crear loop.sh (pegar script de arriba, ya con tus variables)

# 3. Arrancar (sobrevive al cierre)
nohup bash /tmp/sandbox-tarea-{N}/loop.sh > /dev/null 2>&1 &
disown

# 4. Reportar
echo "📡 [A{N}] modo loops activo · 18h · poll 20s · target {REPO_TARGET}"
```

---

## 🔄 Diferencias vs versión original de A3

| Original (A3) | Mejorado (M3-Manager) |
|---|---|
| Hardcodeado para A3 + ws-relay | Genérico, placeholders {N} {REPO} |
| `MAX_RETRY=200` (finito) | `END_TS` por duración (18h) |
| `200 soluciones antes de escalar` | `3 alternativas automáticas` en el script |
| Sin heartbeat | `heartbeat.log` cada 20s |
| No menciona pizarra | Pull pizarra como alternativa 3 |
| Setup manual de `bitacora.md` | `touch` automático |
| Sin chequeo de uptime | Comando `LEFT` para ver restante |

---

**Versión**: 2026-07-10T17:25Z · M3-Manager
**Para usar**: copiá, reemplazá `{N}` por tu ID, `{REPO_TARGET}` por tu repo, `{DURATION_HOURS}` por las horas, `{POLL_SECONDS}` por el intervalo.
