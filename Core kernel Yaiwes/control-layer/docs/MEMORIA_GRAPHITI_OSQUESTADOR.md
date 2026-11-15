# Memoria · Integrar Graphiti, Grapify, OCR Baidu, Osquestador auditor
**Estado base en repo:** `control-layer/memory/` (parcial)

---

## 1. Qué ya existe (no reescribir)

```text
control-layer/memory/
  router.py, guard.py, policy.py, classifier.py
  session_store.py, doc_registry.py, versioning.py
  providers/local_provider.py
  providers/tencent/          # adapter oculto
  MEMORY.md                   # tiers 0–3 parciales
```

Diseño fijo:

```text
ControlBus / Wordflow
        ↓
Memory Control Plane (qué/dónde/cuándo/cuánto)
        ↓
Router + Guard + Policy + Classifier
        ↓
LocalProvider (primero)  →  TencentAdapter (opcional oculto)
        ↓
Tiers 0 RAW · 1 SESSION · 2 STRATEGIC · 3 PROJECT
```

Usuario exige: **memoria nativa**. No obligar Obsidian/Graphiti/n8n como sistemas independientes visibles.

---

## 2. Graphiti → capability nativa (no SaaS)

| Paso | Acción |
|------|--------|
| 1 | Pin source OS Graphiti en `manifests/AGENTS_SOURCE_MANIFEST.yaml` (repo+ref+sha256) |
| 2 | Pull determinista → `agents/sources/graphiti/` o `vendor/graphiti/` |
| 3 | Evolution modo 4: destilar motor de grafo (nodos/aristas/consulta) |
| 4 | Compilar package `extensions/memory_graph/` |
| 5 | Registrar capability `memory.graph.upsert` / `memory.graph.query` |
| 6 | Wire a MemoryRouter: tier 2/3 + aristas laterales |

Aristas objetivo (S12): `version_de`, `contradice`, `refina`, `depende_de`, `cita_a`, `autoridad_sobre`.  
Conflicto → estado CONFLICT (C60): no auto-elige ganador; escala Council/Director salvo `autoridad_sobre`.

**Grapify:** mismo pipeline si es utilitario de grafo/visualización; capability `memory.graph.visualize` opcional (export), no UI externa obligatoria.

---

## 3. OCR Baidu → capability nativa

| Opción | Uso |
|--------|-----|
| A API Baidu | Solo detrás de CredentialBroker; never key en prompt/event |
| B OS OCR (Paddle/Tesseract/etc.) | Preferible para nativo: pin source + Evolution modo 4 → `extensions/ocr/` |

Capability: `ocr.extract_text` (input: image/pdf artifact_id → text + bbox opcional).  
Resultado → Tier 0/1 o artifact store; no depender de consola Baidu.

---

## 4. Osquestador auditor de memoria

**Qué es (docs usuario):** kernel/microservicios de memoria + auditoría de integridad; “superpoderes” sobre el plane.

**Estado:** diferido hasta docs completos del osquestador; **slot reservado**:

```text
extensions/osquestador_memory/
  auditor.py      # integridad tiers, scopes, no-regresión
  kernel_hooks.py # API hacia MemoryRouter
  tests/
```

**Auditor debe verificar:**
- chain tips tier0/1/3 coherentes
- isolation project_A ⟂ project_B (MemoryGuard)
- no secrets en records
- regresión post-Evolution (canary memoria)

**Temporal binario:** carpeta + manifest SHA; no mezclar con control-layer core hasta aprobación.

---

## 5. Orden de implementación memoria (cuando toque)

1. Cerrar namespaces G0.11 alineados Mission/Task/Job  
2. Artifact refs en eventos (no blobs en bus)  
3. Graph capability (Graphiti destilado o KG mínimo propio)  
4. OCR capability  
5. Dream/Distill loops  
6. Osquestador + auditor cuando lleguen docs  

**Prohibido:** montar Graphiti como proceso externo obligatorio para el usuario final.
