# A2 · RESEARCH ENGINE — Documento 1/4
**Bloques B1 (Manifest) + B2 (State) · UOOS Parte 1**
Fuente: `arquitectura_Wordflow.md`, Salida 6/13, líneas 3956-4058, literal

---

## B1 · PROJECT_MANIFEST

```yaml
salida: A2 - Research Engine + Repository Mirror + Skills + Sandbox(stub)
serie: 2 de 19
modo: A
objetivo: >
  Implementar la investigación obligatoria antes de construir, y
  conectar esa investigación con los agentes. Ningún componente crea
  código nuevo sin haber pasado por aquí primero (Ley L01).
flujo_completo: >
  Objetivo → Research Engine → múltiples fuentes → ≥20 investigaciones
  → Architecture Council → selección → descarga determinista →
  Repository Mirror → Skills → Context Builder → Sandbox → Agent Harness
nota_de_alcance: >
  Esta salida menciona Sandbox y Memory solo como Protocol abstractos
  (stubs) — la implementación completa de Sandbox Pool/Broker/Resource
  Governor es G12-G13; la del Memory Engine de 4 capas es G16. Se
  reproducen aquí tal como aparecen en la fuente, sin desarrollarlos.
depende_de: [A1]
grupos_que_dependen_de_este: [G4, G5, G8, G9, G12, G16]
```

## B2 · state.json — estado de una investigación

```yaml
grupo: A2
documento_actual: 1 de 4
estado: en_construcción

# Contrato de entrada de una investigación (literal)
research_request:
  research_id: str
  objective: str
  component: str
  minimum_sources: int = 20
  required_source_types: tuple[str, ...] = ()

# Contrato de resultado de una investigación (literal)
research_finding:
  finding_id: str
  source: str
  url: str
  repository: str | None
  version: str | None
  commit: str | None
  finding: str
  evidence: tuple[str, ...]

estados_posibles_de_una_investigacion:
  - pending
  - in_progress
  - RESEARCH_INCOMPLETE   # si < 20 fuentes válidas — no se permite continuar
  - done
```

---

*Siguiente: Documento 2/4 — B3 (Research Providers + Skills) + B4 (Repository Resolver + Mirror + Context Builder).*
