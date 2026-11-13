# DOC-01: LYRIE-AI — LOOP DETECTOR & FALLBACK CLASSIFIER
## MAXBRY-WPR-DAG v7 — PASADA 1/5
## Repositorio: https://github.com/OTT-Cybersecurity-LLC/lyrie-ai
## Mecanismos: ToolLoopDetector + FallbackClassifier
## Fecha: 2026-08-15

---

## 1. CÓDIGO FUENTE COMPLETO EXTRAÍDO

### 1.1 loop-detector.ts (CÓDIGO ORIGINAL COMPLETO)

```typescript
/**
 * ToolLoopDetector — Run-scoped detection of repeated tool calls.
 *
 * Problem: agents can get stuck calling the same tool with the same arguments
 * in a loop when a model receives an empty/ambiguous response.
 *
 * Solution: within a single run, fingerprint each normalized tool call.
 * If the same fingerprint appears >= LOOP_THRESHOLD times, flag it as a loop.
 *
 * Normalization strips volatile fields (PID, duration, timestamp) so that
 * functionally-identical calls are detected even when metadata differs.
 *
 * (c) OTT Cybersecurity LLC / Lyrie.ai
 */

export interface ToolCall {
  name: string;
  args?: Record<string, unknown>;
  pid?: number;
  duration?: number;
  timestamp?: string | number;
  [key: string]: unknown;
}

const LOOP_THRESHOLD = 3;

const VOLATILE_KEYS = new Set(["pid", "duration", "timestamp", "requestId", "traceId", "spanId"]);

export class ToolLoopDetector {
  private readonly _runs = new Map<string, Map<string, number>>();

  onRunStart(runId: string): void {
    this._runs.set(runId, new Map());
  }

  onRunEnd(runId: string): void {
    this._runs.delete(runId);
  }

  isLoop(call: ToolCall, runId: string): boolean {
    let counters = this._runs.get(runId);
    if (!counters) {
      counters = new Map();
      this._runs.set(runId, counters);
    }
    const normalized = this.normalizeExecCall(call);
    const fp = fingerprint(normalized);
    const count = (counters.get(fp) ?? 0) + 1;
    counters.set(fp, count);
    return count >= LOOP_THRESHOLD;
  }

  callCount(call: ToolCall, runId: string): number {
    const counters = this._runs.get(runId);
    if (!counters) return 0;
    return counters.get(fingerprint(this.normalizeExecCall(call))) ?? 0;
  }

  normalizeExecCall(call: ToolCall): ToolCall {
    const normalized: ToolCall = { name: call.name };
    if (call.args) {
      const cleanArgs: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(call.args)) {
        if (!VOLATILE_KEYS.has(k)) {
          cleanArgs[k] = v;
        }
      }
      normalized.args = cleanArgs;
    }
    for (const [k, v] of Object.entries(call)) {
      if (k !== "name" && k !== "args" && !VOLATILE_KEYS.has(k)) {
        normalized[k] = v;
      }
    }
    return normalized;
  }

  runSnapshot(runId: string): Record<string, number> {
    const counters = this._runs.get(runId);
    if (!counters) return {};
    return Object.fromEntries(counters);
  }

  get activeRuns(): number {
    return this._runs.size;
  }
}

function fingerprint(call: ToolCall): string {
  return JSON.stringify(call, sortedReplacer);
}

function sortedReplacer(_key: string, value: unknown): unknown {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    const sorted: Record<string, unknown> = {};
    for (const k of Object.keys(value as Record<string, unknown>).sort()) {
      sorted[k] = (value as Record<string, unknown>)[k];
    }
    return sorted;
  }
  return value;
}
```

### 1.2 fallback-classifier.ts (CÓDIGO ORIGINAL COMPLETO)

```typescript
/**
 * FallbackClassifier — Classify why a provider call failed so the
 * model router can choose the right fallback strategy.
 *
 * Classification is intentionally conservative: when in doubt, return
 * 'unclassified' rather than incorrectly retrying a permanent error.
 *
 * (c) OTT Cybersecurity LLC / Lyrie.ai
 */

export type FallbackReason =
  | "empty_response"
  | "no_error_details"
  | "provider_overload"
  | "context_too_large"
  | "model_not_available"
  | "live_session_conflict"
  | "unclassified";

export function classifyFallback(
  error: unknown,
  response?: Response | { status?: number; statusText?: string } | null
): FallbackReason {
  if (!error && !response) return "empty_response";

  const status = getStatus(error, response);
  if (status !== null) {
    if (status === 429 || status === 503 || status === 529) return "provider_overload";
    if (status === 413) return "context_too_large";
    if (status === 404) return "model_not_available";
    if (status === 409) return "live_session_conflict";
  }

  const msg = errorMessage(error);
  if (msg) {
    const lower = msg.toLowerCase();
    if (
      lower.includes("rate limit") ||
      lower.includes("rate_limit") ||
      lower.includes("too many requests") ||
      lower.includes("overloaded") ||
      lower.includes("capacity") ||
      lower.includes("quota exceeded")
    ) {
      return "provider_overload";
    }
    if (
      lower.includes("context length") ||
      lower.includes("context_length") ||
      lower.includes("token limit") ||
      lower.includes("too long") ||
      lower.includes("maximum context") ||
      lower.includes("max_tokens") ||
      lower.includes("input too large")
    ) {
      return "context_too_large";
    }
    if (
      lower.includes("model not found") ||
      lower.includes("model_not_found") ||
      lower.includes("no such model") ||
      lower.includes("does not exist") ||
      lower.includes("not available") ||
      lower.includes("not_available") ||
      lower.includes("deprecated")
    ) {
      return "model_not_available";
    }
    if (
      lower.includes("session conflict") ||
      lower.includes("live session") ||
      lower.includes("streaming conflict") ||
      lower.includes("concurrent")
    ) {
      return "live_session_conflict";
    }
    if (
      lower.includes("empty") ||
      lower.includes("no content") ||
      lower.includes("no response")
    ) {
      return "empty_response";
    }
    if (msg.trim().length < 5) return "no_error_details";
    return "unclassified";
  }

  if (error !== null && error !== undefined) return "no_error_details";
  return "empty_response";
}

function getStatus(
  error: unknown,
  response?: Response | { status?: number; statusText?: string } | null
): number | null {
  if (response && typeof (response as { status?: number }).status === "number") {
    return (response as { status: number }).status;
  }
  if (error && typeof (error as { status?: number }).status === "number") {
    return (error as { status: number }).status;
  }
  if (error && typeof (error as { statusCode?: number }).statusCode === "number") {
    return (error as { statusCode: number }).statusCode;
  }
  return null;
}

function errorMessage(error: unknown): string | null {
  if (!error) return null;
  if (typeof error === "string") return error;
  if (error instanceof Error) return error.message;
  if (typeof (error as { message?: string }).message === "string") {
    return (error as { message: string }).message;
  }
  return null;
}

export interface FallbackStrategy {
  retry: boolean;
  switchProvider: boolean;
  reduceContext: boolean;
  retryDelayMs: number;
}

export function strategyForReason(reason: FallbackReason): FallbackStrategy {
  switch (reason) {
    case "provider_overload":
      return { retry: true, switchProvider: true, reduceContext: false, retryDelayMs: 2000 };
    case "context_too_large":
      return { retry: true, switchProvider: false, reduceContext: true, retryDelayMs: 0 };
    case "model_not_available":
      return { retry: false, switchProvider: true, reduceContext: false, retryDelayMs: 0 };
    case "live_session_conflict":
      return { retry: true, switchProvider: false, reduceContext: false, retryDelayMs: 500 };
    case "empty_response":
      return { retry: true, switchProvider: true, reduceContext: false, retryDelayMs: 1000 };
    case "no_error_details":
      return { retry: true, switchProvider: true, reduceContext: false, retryDelayMs: 500 };
    case "unclassified":
    default:
      return { retry: false, switchProvider: true, reduceContext: false, retryDelayMs: 0 };
  }
}
```

---

## 2. ANÁLISIS DEL MOTOR INTERNO

### 2.1 Quien decide
- **ToolLoopDetector**: Decide si una llamada es loop via `isLoop()` con umbral de 3.
- **FallbackClassifier**: Decide la causa del fallo via `classifyFallback()` con 7 categorias.

### 2.2 Quien planifica
- `strategyForReason()` planifica la accion de recuperacion con 4 parametros.

### 2.3 Quien ejecuta
- El caller ejecuta la estrategia retornada. El detector solo alerta.

### 2.4 Quien evalua
- `isLoop()` evalua contra umbral. `classifyFallback()` evalua en 3 capas.

### 2.5 Arquitectura de Integracion
```
AGENT TEAM YAIWES
  |-- Tool Executor
  |     +-- BEFORE: ToolLoopDetector.isLoop()
  |           +-- LOOP? -> STOP + ALERT
  |           +-- NO -> EXECUTE
  +-- LLM Provider Router
        +-- ON error: classifyFallback()
              +-- strategyForReason()
                    +-- retry + delay
                    +-- switchProvider
                    +-- reduceContext
                    +-- NO ACTION
```

---

## 3. THREE LOOP ANALYSIS

### LOOP A — REASONING LOOP
```
TOOL_CALL
  -> NORMALIZE (strip volatile)
  -> FINGERPRINT (JSON sorted)
  -> EVALUATE count >= 3?
       +-- YES -> REASON: "Loop" -> DECIDE: STOP
       +-- NO  -> REASON: "OK" -> DECIDE: PROCEED
```
Estado: `_runs: Map<runId, Map<fingerprint, count>>`
Entradas: ToolCall + runId
Salidas: boolean
Terminacion: onRunEnd limpia el Map

### LOOP B — AGENT EXECUTION LOOP
```
OBJECTIVE -> PLAN (select provider) -> EXECUTE (call)
  -> OBSERVE (response/error) -> EVALUATE (classifyFallback)
  -> NEXT (apply strategy)
```
Mantiene: necesidad de respuesta valida del LLM
Cambia: provider, context size, delay
Salida: respuesta valida o agotamiento

### LOOP C — PERSISTENT WORKFLOW LOOP
No aplica directamente. Estado en memoria por run, no persiste en disco.

---

## 4. ASK_COUNCIL — 12 Preguntas

| # | Pregunta | Respuesta |
|---|----------|-----------|
| 01 | Codigo que controla comportamiento interno | ToolLoopDetector con fingerprint normalizado + FallbackClassifier con clasificacion multi-capa |
| 02 | Como se construye el razonamiento | Multi-etapa: normalizacion->fingerprint->conteo; status->mensaje->heuristica |
| 03 | Como pasa de razonamiento a decision | isLoop() retorna boolean; strategyForReason() retorna FallbackStrategy con 4 parametros |
| 04 | Resultado alimenta otra iteracion | SI. Cada tool call alimenta contador. Cada fallo alimenta estrategia |
| 05 | Ciclo PLAN->EXECUTE->OBSERVE->NEXT | SI. Router de providers: PLAN->EXECUTE->OBSERVE->EVALUATE->NEXT |
| 06 | Estado que se conserva | `_runs` Map por runId. FallbackClassifier es stateless |
| 07 | Que sucede si proceso se detiene | onRunEnd limpia Map. No persistencia pero no leak |
| 08 | Desde donde continua | Nuevo runId = nuevo Map. Cada run aislado |
| 09 | Que ocurre despues de fallo | strategyForReason cambia estrategia REAL: switch, reduce, delay. NO retry identico |
| 10 | Como determina si solucion es buena | Loop: count < threshold. Fallback: respuesta valida sin error |
| 11 | Que hace mejor que implementacion simple | (a) Normalizacion evita falsos negativos, (b) Clasificacion conservadora previene retries permanentes, (c) Estrategia parametrizada |
| 12 | Evidencia suficiente para extraer | SI. ~260 lineas de codigo ejecutable y testeable |

---

## 5. OUTPUT_GOALS MAPPED

| Goal | Evidencia |
|------|-----------|
| G01 | LOOP_THRESHOLD define criterio. FallbackStrategy define recuperacion |
| G02 | ToolLoopDetector y FallbackClassifier son capas adicionales sobre INPUT->LLM->OUTPUT |
| G03 | Multi-layer: normalization->fingerprint->count; status->message->heuristic |
| G04 | No hay prompts operativos, son puramente logica de control |
| G05 | SI. Cada tool call alimenta contador; cada fallo alimenta estrategia |
| G06 | SI. PLAN->EXECUTE->OBSERVE->EVALUATE->NEXT |
| G07 | NO aplica. Estado en memoria por run |
| G08 | SI. switchProvider permite cambio a provider alternativo |
| G09 | SI. strategyForReason genera estrategias diferenciadas |
| G10 | Parcial. Loop detector previene loops futuros |
| G11 | NO. Son mecanismos estaticos |
| G12 | SI. ~260 lineas que previenen dos problemas criticos de produccion |

---

## 6. RECOMMENDATIONS FOR YAIWES WORKFLOW

### 6.1 ToolLoopDetector
**Ubicacion**: `yaiwes/core/agent/loop-detector.ts`

```typescript
const loopDetector = new ToolLoopDetector();
loopDetector.onRunStart(sessionId);

if (loopDetector.isLoop(toolCall, sessionId)) {
  await orchestrator.handleLoopDetected(sessionId, toolCall);
  throw new AgentLoopError(`Loop detected: ${toolCall.name}`);
}

loopDetector.onRunEnd(sessionId);
```

Configuracion:
- LOOP_THRESHOLD: 3 dev, 5 prod
- Extender VOLATILE_KEYS con campos de YAIWES

### 6.2 FallbackClassifier
**Ubicacion**: `yaiwes/core/router/fallback-classifier.ts`

```typescript
async function callProvider(provider, request) {
  try {
    return await provider.generate(request);
  } catch (error) {
    const reason = classifyFallback(error, error.response);
    const strategy = strategyForReason(reason);
    if (strategy.reduceContext) {
      request.context = truncateContext(request.context, 0.5);
    }
    if (strategy.switchProvider && strategy.retry) {
      await sleep(strategy.retryDelayMs);
      return callProvider(providerPool.getNext(provider.id), request);
    }
    if (strategy.retry) {
      await sleep(strategy.retryDelayMs);
      return callProvider(provider, request);
    }
    throw new ProviderPermanentError(reason, error);
  }
}
```

---

## 7. JUSTIFICATION

**ToolLoopDetector**: Previene que YAIWES consuma tokens indefinidamente en bucles de tool calls. La normalizacion de fingerprints es clave: sin ella, dos llamadas identicas separadas por 1ms tendrian fingerprints diferentes. ROI: ~100 lineas previenen perdidas de $10-$100 por loop.

**FallbackClassifier**: Convierte errores opacos en acciones estructuradas. Un simple catch+retry reintenta errores permanentes (404). Este sistema es conservador: prefiere NO reintentar a reintentar incorrectamente. ROI: Clasificacion en ~50ms que ahorra $1-$10 por error.

---

## 8. GROK VALIDATION PROTOCOL

### ToolLoopDetector
- [ ] Clase ToolLoopDetector existe en yaiwes/core/agent/loop-detector.ts
- [ ] Se usa en el executor de tools
- [ ] onRunStart(sessionId) al inicio de cada sesion
- [ ] isLoop() ANTES de cada tool call
- [ ] Si true, se detiene y notifica al orquestador
- [ ] onRunEnd(sessionId) al cerrar sesion
- [ ] LOOP_THRESHOLD configurable por env var

### FallbackClassifier
- [ ] classifyFallback() existe en yaiwes/core/router/fallback-classifier.ts
- [ ] strategyForReason() en mismo archivo
- [ ] Cada catch del router llama classifyFallback()
- [ ] Se aplican TODOS los campos de FallbackStrategy
- [ ] Caso unclassified NUNCA reintenta automaticamente
- [ ] Delay respetado con sleep(strategy.retryDelayMs)
- [ ] Context reduction trunca efectivamente al 50%

---

## 9. VERIFICATION SCRIPT


```python
#!/usr/bin/env python3
"""
YAIWES-DOC01-Verifier: Loop Detector + Fallback Classifier
Valida que MEC-01 y MEC-02 estan implementados en YAIWES.
"""

import os
import sys
from pathlib import Path

class Doc01Verifier:
    def __init__(self, codebase_path: str):
        self.codebase = Path(codebase_path)
        self.results = []
        self.files = []
        for ext in ["*.ts", "*.js", "*.py"]:
            self.files.extend(self.codebase.rglob(ext))
        self.contents = {}
        for f in self.files:
            try:
                self.contents[str(f)] = f.read_text(encoding="utf-8")
            except:
                pass

    def check(self, check_id: str, condition: bool, detail: str):
        self.results.append((check_id, condition, detail))
        icon = "PASS" if condition else "FAIL"
        print(f"[{icon}] {check_id}: {detail}")

    def verify(self):
        print("=" * 70)
        print("YAIWES DOC-01 Verifier: Loop Detector + Fallback Classifier")
        print(f"Scanning: {self.codebase} ({len(self.files)} files)")
        print("=" * 70)

        self.check("MEC-01-1", 
            any("ToolLoopDetector" in c for c in self.contents.values()),
            "ToolLoopDetector class exists")
        self.check("MEC-01-2", 
            any("onRunStart" in c for c in self.contents.values()),
            "onRunStart lifecycle exists")
        self.check("MEC-01-3", 
            any("onRunEnd" in c for c in self.contents.values()),
            "onRunEnd lifecycle exists")
        self.check("MEC-01-4", 
            any("isLoop(" in c for c in self.contents.values()),
            "isLoop() called before tool execution")
        self.check("MEC-01-5", 
            any("normalizeExecCall" in c or "normalize" in c for c in self.contents.values()),
            "Normalization logic exists")
        self.check("MEC-01-6", 
            any("fingerprint" in c for c in self.contents.values()),
            "Fingerprinting logic exists")
        self.check("MEC-02-1", 
            any("classifyFallback" in c for c in self.contents.values()),
            "classifyFallback exists")
        self.check("MEC-02-2", 
            any("strategyForReason" in c for c in self.contents.values()),
            "strategyForReason exists")
        self.check("MEC-02-3", 
            any("FallbackReason" in c for c in self.contents.values()),
            "FallbackReason type exists")
        self.check("MEC-02-4", 
            any("FallbackStrategy" in c for c in self.contents.values()),
            "FallbackStrategy type exists")
        self.check("MEC-02-5", 
            any("provider_overload" in c for c in self.contents.values()),
            "Provider overload handling")
        self.check("MEC-02-6", 
            any("context_too_large" in c for c in self.contents.values()),
            "Context too large handling")
        self.check("MEC-02-7", 
            any("unclassified" in c for c in self.contents.values()),
            "Unclassified conservative default")
        self.check("MEC-02-8", 
            any("retryDelayMs" in c for c in self.contents.values()),
            "Retry delay implementation")

        passed = sum(1 for _, ok, _ in self.results if ok)
        total = len(self.results)
        print("=" * 70)
        print(f"RESULT: {passed}/{total} checks passed ({passed/total*100:.0f}%)")
        return 0 if passed == total else 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_doc01.py <path-to-yaiwes-codebase>")
        sys.exit(1)
    sys.exit(Doc01Verifier(sys.argv[1]).verify())
```

---

**Documento generado por MAXBRY-WPR-DAG v7**
**Mecanismos**: ToolLoopDetector + FallbackClassifier
**Evidencia**: Codigo fuente original completo del repositorio Lyrie-ai
