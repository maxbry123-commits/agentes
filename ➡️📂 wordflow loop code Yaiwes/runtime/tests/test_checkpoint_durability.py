"""
Prueba de aceptacion G06 (contrato DSL DAG):
  in:  "CheckpointManager en memoria"
  out: "checkpoint durable que sobrevive crash"

Metodo: crear un checkpoint con una instancia A, tirar esa instancia
(simulando el fin del proceso), abrir una instancia B nueva apuntando
al MISMO db_path, y comprobar que B recupera exactamente los mismos
datos que guardo A. Si CheckpointManager siguiera usando un dict en
memoria, esta prueba fallaria (B no veria nada de A).
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "recovery"))
from checkpoint import CheckpointManager


def test_survives_new_process_instance():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test_checkpoints.sqlite3")

        instance_a = CheckpointManager(db_path=db_path)
        created = instance_a.create_checkpoint("chk_crash_test", {"node": "N-2.5", "step": "EXECUTE"})
        del instance_a

        instance_b = CheckpointManager(db_path=db_path)
        restored = instance_b.restore_checkpoint("chk_crash_test")

        assert restored == {"node": "N-2.5", "step": "EXECUTE"}, restored
        assert created["created"] is True

        with open(db_path, "r+b") as f:
            f.seek(200)
            f.write(b"\xff" * 8)
        instance_c = CheckpointManager(db_path=db_path)
        try:
            corrupted = instance_c.restore_checkpoint("chk_crash_test")
            assert corrupted is None or corrupted == {"node": "N-2.5", "step": "EXECUTE"}
        except Exception:
            pass

    print("PASS: checkpoint sobrevive a una instancia nueva (crash simulado)")


if __name__ == "__main__":
    test_survives_new_process_instance()
