# DUAL.02 — Package Montable ABI v1.0
Wordflow Extension ABI (montable sin tocar kernel)

## Estado 2026-08-09
**IMPLEMENTACIÓN REAL**: `wordflow/abi.py`  
**TESTS**: `wordflow/test_abi.py`

## Contrato mínimo (ejecutado)
```python
class ExtensionABI:
    def register(self, capability_id: str, handler) -> None: ...
    def unregister(self, capability_id: str) -> None: ...
    def list_capabilities(self) -> list[str]: ...
    def execute(self, capability_id: str, params: dict | None = None) -> EvidenceOutput: ...
```

## EvidenceOutput (obligatorio)
```python
@dataclass
class EvidenceOutput:
    ok: bool
    capability: str
    evidence_hash: str
    data: dict
    error: str | None = None
```

## Reglas
- Extensiones se montan **solo** vía `attach_to_wordflow_extension(ext)`
- Kernel nunca importa código de extensión directamente
- Toda capability debe devolver `EvidenceOutput`
- Origin: `wordflow/abi.py` (reemplaza stub anterior)
