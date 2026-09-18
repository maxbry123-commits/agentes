"""
isolation.py - FIX P1-25. Cada worker (de los 50+ del ecosistema) acepta
identidad completa y 1 WRITER = 1 ISOLATED WRITE SCOPE. Dos workers no
pueden escribir simultaneamente el mismo scope.
"""
from dataclasses import dataclass


@dataclass
class WorkerIdentity:
    parent_id: str
    child_id: str
    node_id: str
    claim_id: str
    workspace: str
    base_sha: str
    write_scope: str
    command_id: str


class RegistroDeEscritura:
    """P1-25 aceptacion: dos workers no pueden escribir simultaneamente
    el mismo scope. Registro en memoria del proceso - la version durable
    entre los 50+ workers vive en CrazyWallAdapter (claim/release ya
    implementados en P0-07), esto es la capa rapida local."""

    def __init__(self):
        self._scopes_ocupados: dict[str, str] = {}  # write_scope -> claim_id

    def reclamar_scope(self, identity: WorkerIdentity) -> tuple[bool, str]:
        ocupante = self._scopes_ocupados.get(identity.write_scope)
        if ocupante is not None and ocupante != identity.claim_id:
            return False, f"WRITE_SCOPE_OCUPADO_POR:{ocupante}"
        self._scopes_ocupados[identity.write_scope] = identity.claim_id
        return True, "scope_reclamado"

    def liberar_scope(self, identity: WorkerIdentity) -> None:
        if self._scopes_ocupados.get(identity.write_scope) == identity.claim_id:
            del self._scopes_ocupados[identity.write_scope]


REGISTRO_ESCRITURA_GLOBAL = RegistroDeEscritura()
