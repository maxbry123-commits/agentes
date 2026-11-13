# Background Process Manager + Audit Compliance Hardening

**Date:** 2026-03-25
**Author:** Alexander Soellner + Claude Opus 4.6
**Status:** Approved

---

## 1. Background Process Manager

### Problem
`exec_command()` wartet synchron auf Completion. Langlaufende Befehle (Modell-Downloads, Training, Builds) blockieren den PGE-Loop. Es gibt keine Moeglichkeit, Prozesse im Hintergrund zu starten und spaeter zu pruefen.

### Loesung
Neues Modul `mcp/background_tasks.py` mit `BackgroundProcessManager` + `ProcessMonitor` + 6 MCP-Tools.

### Komponenten

**BackgroundProcessManager:**
- Startet Shell-Befehle als detached Subprocess
- Schreibt stdout+stderr in Log-Datei (`~/.cognithor/workspace/background_logs/{job_id}.log`)
- Speichert Job-Metadaten in SQLite (`~/.cognithor/background_jobs.db`)
- Verwaltet Lifecycle: running -> completed | failed | killed | timeout

**ProcessMonitor (Hybrid-Ansatz):**
- Laeuft als asyncio-Task im Gateway
- Pollt alle `check_interval` Sekunden (Default: 30)
- 5 Pruefmethoden pro Job:
  1. **Process-Alive**: `os.waitpid(pid, WNOHANG)` — lebt der Prozess noch?
  2. **Exit-Code**: Sauber beendet (0) oder Fehler (!=0)?
  3. **Output-Stall**: Log-Dateigroesse nicht gewachsen seit 2 Checks -> Warning
  4. **Timeout**: Laufzeit > konfiguriertes Limit -> SIGTERM, dann SIGKILL
  5. **Resource-Check**: Optionaler psutil-Check fuer Memory/CPU (graceful skip wenn psutil fehlt)
- Bei Status-Aenderung: Sendet Notification an den Channel des Users

**6 MCP-Tools:**

| Tool | Beschreibung | Gatekeeper |
|------|-------------|------------|
| `start_background` | Startet Befehl im Hintergrund. Params: command, description, timeout_seconds, check_interval. Returns: job_id | YELLOW |
| `list_background_jobs` | Listet alle Jobs (optional: nur aktive). Returns: Liste mit id, command, status, started_at, duration | GREEN |
| `check_background_job` | Status + letzte 50 Zeilen Output. Params: job_id. Returns: status, exit_code, last_output | GREEN |
| `read_background_log` | Log lesen. Params: job_id, tail (letzte N Zeilen), head (erste N), offset, limit, grep (Filter). Returns: lines | GREEN |
| `stop_background_job` | Beendet einen Prozess. Params: job_id, force (SIGKILL statt SIGTERM). Returns: success | YELLOW |
| `wait_background_job` | Wartet auf Completion. Params: job_id, timeout. Returns: final status + exit_code | GREEN |

**SQLite Schema:**
```sql
CREATE TABLE background_jobs (
    id TEXT PRIMARY KEY,
    command TEXT NOT NULL,
    description TEXT DEFAULT '',
    agent_name TEXT DEFAULT 'jarvis',
    session_id TEXT DEFAULT '',
    channel TEXT DEFAULT '',
    pid INTEGER,
    status TEXT DEFAULT 'running',
    exit_code INTEGER,
    started_at REAL NOT NULL,
    finished_at REAL,
    timeout_seconds INTEGER DEFAULT 3600,
    check_interval INTEGER DEFAULT 30,
    log_file TEXT NOT NULL,
    last_check_at REAL,
    last_output_size INTEGER DEFAULT 0,
    working_dir TEXT DEFAULT ''
);
```

**Log-Management:**
- Max 10 MB pro Log-Datei (truncated von vorne, letzten 10 MB behalten)
- Automatische Cleanup: Logs von abgeschlossenen Jobs aelter als 7 Tage loeschen
- `read_background_log` unterstuetzt: tail=N, head=N, offset+limit, grep="pattern"

**Gateway-Integration:**
- `ProcessMonitor` wird in `gateway.py` als Background-Task gestartet
- Nutzt bestehenden `_background_tasks` Set
- Stoppt sauber bei Gateway-Shutdown
- Beim Start: Prueft ob laufende Jobs aus vorheriger Session noch aktiv (orphan detection)

---

## 2. Audit Compliance Hardening

### Problem
Das Audit-System ist bereits solide (Hash-Chain, Credential-Masking, Compliance-Reports), hat aber konkrete Luecken bei EU AI Act Art. 62 (Incident Reporting) und GDPR Art. 17 (Right to Erasure fuer persistente Logs).

### Was NICHT geaendert wird
- Hash-Chain in gatekeeper.jsonl bleibt wie sie ist
- AuditLogger Grundstruktur bleibt
- Compliance-Report Endpoints bleiben
- Credential-Masking bleibt

### Was hinzugefuegt wird

**A) Background-Job Audit-Logging:**
Jeder Background-Job erzeugt Audit-Eintraege:
- `TOOL_CALL` beim Start (command, job_id, agent)
- `SYSTEM` bei Status-Aenderung (completed/failed/killed/timeout)
- `SECURITY` wenn Resource-Limits ueberschritten oder Timeout erreicht

**B) Hash-Chain Integrity Verification:**
Neuer API-Endpoint: `GET /api/v1/audit/verify`
- Liest gatekeeper.jsonl und verifiziert die Hash-Chain
- Gibt zurueck: total_entries, valid_entries, broken_at (wenn manipuliert)
- Keine Aenderung am bestehenden Format, nur ein Read-Only-Check

**C) Retention Scheduling:**
Background-Task im Gateway der taeglich alte Audit-Eintraege aufraeumt:
- Default: 90 Tage (konfigurierbar)
- Laeuft als asyncio-Task, einmal pro Tag
- Loescht aus In-Memory-Deque UND aus JSONL-Dateien (per-date Partitionierung)

**D) Background-Job Logs in Audit-Trail:**
Jeder `start_background` und `stop_background_job` Aufruf wird im regulaeren Audit-Trail mitgeschrieben — inklusive Command, Job-ID, und wer es ausgeloest hat.

---

## 3. Nicht im Scope

- HMAC/Ed25519 Signaturen (erfordert Key-Management-Infrastruktur)
- Blockchain-Ankerung (opt-in Feature, existiert bereits als Config-Flag)
- User Data Export API (eigenes Feature)
- Breach Notification Automation (eigenes Feature)
- WORM Storage (OS-Level, nicht in Python loesbar)
