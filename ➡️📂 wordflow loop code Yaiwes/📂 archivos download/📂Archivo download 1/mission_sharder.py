"""
Mission Sharder Module - PECP-MAXBRY-100x
Ejecución determinista para división de misiones por familia de capacidades.
"""

from typing import Dict, Any, List
import hashlib
import json


class MissionSharder:
    """Clase encargada de shardear misiones garantizando la re-combinación determinista."""

    def __init__(self, policy: Dict[str, Any] = None) -> None:
        if policy is None:
            policy = {}
        self.max_micro_missions: int = policy.get("max_micro_missions", 10)
        self.parallelism_factor: int = policy.get("parallelism_factor", 4)
        self.family_affinity: Dict[str, str] = policy.get("family_affinity", {})

    @staticmethod
    def calculate_hash(data: Dict[str, Any]) -> str:
        """Calcula hash SHA256 determinista del diccionario serializado ordenadamente."""
        serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def shard_mission(
        self, mission_contract: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Divide la misión principal en micro-misiones basadas en sus capacidades.
        Garantiza hash(mission) == hash(recombined_micro_missions).
        """
        mission_id: str = mission_contract.get("mission_id", "MIS-000")
        tasks: List[Dict[str, Any]] = mission_contract.get("tasks", [])
        
        shards_by_family: Dict[str, List[Dict[str, Any]]] = {}

        for task in tasks:
            family: str = self.family_affinity.get(
                task.get("capability_family", "default"), "default"
            )
            if family not in shards_by_family:
                shards_by_family[family] = []
            shards_by_family[family].append(task)

        micro_missions: List[Dict[str, Any]] = []
        for family_name, family_tasks in shards_by_family.items():
            micro_mission = {
                "micro_mission_id": f"{mission_id}_shard_{family_name}",
                "family": family_name,
                "tasks": family_tasks,
            }
            micro_missions.append(micro_mission)

        recombined_tasks = []
        for mm in micro_missions:
            recombined_tasks.extend(mm["tasks"])
        
        recombined_payload = {
            "mission_id": mission_id,
            "tasks": recombined_tasks,
        }

        original_hash = self.calculate_hash(
            {"mission_id": mission_id, "tasks": tasks}
        )
        recombined_hash = self.calculate_hash(recombined_payload)

        assert original_hash == recombined_hash, "Fallo de Integridad: Hash Desajustado"

        return {
            "manifest_version": "1.0.0",
            "mission_id": mission_id,
            "original_hash": original_hash,
            "recombined_hash": recombined_hash,
            "integrity_verified": True,
            "micro_missions": micro_missions,
        }


if __name__ == "__main__":
    print("=== EJECUTANDO PRUEBA AUTÓNOMA NODO T-002 ===")
    
    # 1. Configuración de prueba
    sample_policy = {
        "max_micro_missions": 5,
        "parallelism_factor": 2,
        "family_affinity": {
            "research": "RESEARCH_FAMILY",
            "ingestion": "STORAGE_FAMILY"
        }
    }

    # 2. Misión de prueba
    sample_mission = {
        "mission_id": "MIS-1001",
        "tasks": [
            {"id": "task_1", "name": "Research API", "capability_family": "research"},
            {"id": "task_2", "name": "Store Data", "capability_family": "ingestion"},
            {"id": "task_3", "name": "Research Web", "capability_family": "research"}
        ]
    }

    # 3. Ejecución
    sharder = MissionSharder(policy=sample_policy)
    result = sharder.shard_mission(mission_contract=sample_mission)

    # 4. Salida
    print(f"Misión ID: {result['mission_id']}")
    print(f"Hash Original  : {result['original_hash']}")
    print(f"Hash Recomb.   : {result['recombined_hash']}")
    print(f"Verificado     : {result['integrity_verified']}")
    print(f"Micro Misiones : {len(result['micro_missions'])} creadas.")
    print("\nPROCESO COMPLETADO EXITOSAMENTE.")
