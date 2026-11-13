"""
test_p0_01_dag_real.py - Prueba de equivalencia DAG/runtime exigida por
la auditoria 5x (P0-01): modificar una transicion del DAG debe modificar
realmente el flujo ejecutado. Usa un archivo YAML temporal para no tocar
el dag_schema.yaml real durante el test.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import dag_engine


def test_dag_se_carga_fresco_no_cacheado(tmp_path, monkeypatch):
    yaml_original = """
steps:
  - id: RESEARCH
    action: investigar
  - id: EXECUTE
    action: ejecutar
edges: ["RESEARCH->EXECUTE"]
"""
    archivo_dag = tmp_path / "dag_schema.yaml"
    archivo_dag.write_text(yaml_original)
    monkeypatch.setattr(dag_engine, "_DAG_PATH", archivo_dag)

    dag = dag_engine.cargar_dag()
    assert dag_engine.transicion_permitida(dag, "RESEARCH", "EXECUTE") is True
    assert dag_engine.transicion_permitida(dag, "EXECUTE", "VALIDATE") is False

    # Se modifica el archivo YAML en disco (simula editar dag_schema.yaml)
    archivo_dag.write_text(yaml_original.replace('edges: ["RESEARCH->EXECUTE"]', 'edges: []'))

    # Como cargar_dag() lee fresco (no cachea), el cambio se refleja YA,
    # sin reiniciar nada - esto es lo que exige el criterio de aceptacion.
    dag_modificado = dag_engine.cargar_dag()
    assert dag_engine.transicion_permitida(dag_modificado, "RESEARCH", "EXECUTE") is False


def test_tipo_sin_ruta_en_dag_es_gap():
    ok, motivo = dag_engine.validar_ruta_de_tipo("tipo_que_no_existe_en_ningun_lado")
    assert ok is False
    assert "tipo_sin_nodo_dag" in motivo


def test_tipos_reales_si_tienen_ruta_en_dag():
    for tipo in ("instalar_paquete", "verificar_existencia", "evaluar_componente", "diseno_arquitectura"):
        ok, nodo = dag_engine.validar_ruta_de_tipo(tipo)
        assert ok is True, f"{tipo} deberia tener ruta declarada en el DAG real"
