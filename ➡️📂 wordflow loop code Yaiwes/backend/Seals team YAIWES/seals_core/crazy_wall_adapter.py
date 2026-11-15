"""
crazy_wall_adapter.py - P0-07 FIX. Adapter oficial hacia el Crazy Wall
real (via GitHub API, mismo patron que watchdog.py). Antes: dag_schema
decia "registrar en Crazy Wall" pero Python solo escribia un JSONL local.
Regla: 1 node = 1 claim. 1 path = 1 writer. Read-back obligatorio
despues de cada mutacion (se relee el archivo tras escribir, para
confirmar que la escritura fue real y no se perdio).
"""
import base64
import json
import os

import requests

REPO = "maxbry123-commits/agentes"
CRAZY_WALL_PATH = "%F0%9F%93%82%20Bit%C3%A1cora%20stated%20JSON%20Craxy%20wall.json"
API_BASE = f"https://api.github.com/repos/{REPO}/contents/{CRAZY_WALL_PATH}"


class CrazyWallAdapter:
    def __init__(self, token: str | None = None, sesion_http=None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.http = sesion_http or requests
        self._sha_actual = None

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _leer_fresco(self) -> tuple[dict, str]:
        resp = self.http.get(API_BASE, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        contenido = json.loads(base64.b64decode(data["content"]).decode("utf-8"))
        return contenido, data["sha"]

    def claim(self, node_id: int, worker_id: str) -> tuple[bool, str]:
        """1 node = 1 claim. Rechaza si ya esta CLAIMED por otro worker."""
        crazy_wall, sha = self._leer_fresco()
        for nodo in crazy_wall.get("nodes", []):
            if nodo.get("id") == node_id:
                if nodo.get("lock") not in (None, "FREE"):
                    return False, f"nodo_ya_reclamado_por:{nodo.get('owner')}"
                nodo["lock"] = "CLAIMED"
                nodo["owner"] = worker_id
                self._sha_actual = sha
                return self._escribir_con_readback(crazy_wall, sha, f"claim nodo {node_id} por {worker_id}")
        return False, "nodo_no_encontrado"

    def checkpoint(self, node_id: int, dato: dict) -> tuple[bool, str]:
        crazy_wall, sha = self._leer_fresco()
        for nodo in crazy_wall.get("nodes", []):
            if nodo.get("id") == node_id:
                nodo.setdefault("checkpoint", {})["after"] = dato
                return self._escribir_con_readback(crazy_wall, sha, f"checkpoint nodo {node_id}")
        return False, "nodo_no_encontrado"

    def record_gap(self, node_id: int, motivo: str) -> tuple[bool, str]:
        crazy_wall, sha = self._leer_fresco()
        for nodo in crazy_wall.get("nodes", []):
            if nodo.get("id") == node_id:
                nodo.setdefault("history", []).append({"event": "GAP", "motivo": motivo})
                return self._escribir_con_readback(crazy_wall, sha, f"GAP nodo {node_id}: {motivo}")
        return False, "nodo_no_encontrado"

    def record_evidence(self, node_id: int, evidence_record) -> tuple[bool, str]:
        crazy_wall, sha = self._leer_fresco()
        for nodo in crazy_wall.get("nodes", []):
            if nodo.get("id") == node_id:
                nodo.setdefault("evidence", []).append(vars(evidence_record))
                return self._escribir_con_readback(crazy_wall, sha, f"evidencia nodo {node_id}")
        return False, "nodo_no_encontrado"

    def release(self, node_id: int) -> tuple[bool, str]:
        crazy_wall, sha = self._leer_fresco()
        for nodo in crazy_wall.get("nodes", []):
            if nodo.get("id") == node_id:
                nodo["lock"] = "FREE"
                nodo["owner"] = None
                return self._escribir_con_readback(crazy_wall, sha, f"release nodo {node_id}")
        return False, "nodo_no_encontrado"

    def _escribir_con_readback(self, crazy_wall: dict, sha: str, mensaje: str) -> tuple[bool, str]:
        contenido_b64 = base64.b64encode(json.dumps(crazy_wall, ensure_ascii=False, indent=2).encode("utf-8")).decode("ascii")
        resp = self.http.put(
            API_BASE,
            headers=self._headers(),
            json={"message": f"CrazyWallAdapter: {mensaje}", "content": contenido_b64, "sha": sha},
            timeout=30,
        )
        if resp.status_code not in (200, 201):
            return False, f"escritura_fallo:{resp.status_code}"
        # Read-back obligatorio: releer para confirmar que la escritura fue real.
        _, sha_nuevo = self._leer_fresco()
        if sha_nuevo == sha:
            return False, "readback_no_detecto_cambio"
        return True, "escrito_y_confirmado_con_readback"
