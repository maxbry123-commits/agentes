# DUAL.02 — Package Montable ABI v1.0
Wordflow Extension ABI (montable sin tocar kernel)

## Contrato mínimo
```python
class ExtensionABI:
    def register(self, capability_id: str, handler) -> None: ...
    def unregister(self, capability_id: str) -> None: ...
    def list_capabilities(self) -> list[str]: ...
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
- Extensiones se montan solo vía attach_to_wordflow_extension(ext)
- Kernel nunca importa código de extensión directamente
- Toda capability debe devolver EvidenceOutput
- Origin: bridge_abi.py + evolution_mount.py
