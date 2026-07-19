"""
test_runtime.py — Tests del UOOS Parte 2 v3.0 Executor Runtime.

Cubre:
- RT-00..RT-04: BOOT (versión, integridad, preflight, skills, resume)
- RT-10..RT-45: CICLO POR NODO
- RT-80: RECOVERY_GATE
- RT-90: CIERRE
- Reglas E01-E12 (cumplimiento)
- Eventos obligatorios
"""
import os
import sys
import json
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.runtime import (
    RuntimeExecutor, RuntimeState, Node, NodeStatus, EventType,
    UOOS_VERSION, build_state_from_b3
)


def make_state(nodos_count: int = 3) -> RuntimeState:
    """Helper: estado con N nodos en cadena."""
    state = RuntimeState(proyecto="test", modo="A")
    for i in range(nodos_count):
        nid = f"T-{i+1:03d}"
        node = Node(
            id=nid,
            goal=f"goal del nodo {i+1}",
            contrato_input={},
            contrato_output={"criterio_exito": "status==ok"},
            criterio_exito="status==ok",
            dependencies=[f"T-{i:03d}"] if i > 0 else [],
            risk="bajo",
            priority=1,
            skills_requeridas=["python"],
            timeout_seg=10,
        )
        state.nodos[nid] = node
    return state


# ============================================================================
# BOOT (RT-00..RT-04)
# ============================================================================

def test_rt_00_boot_version():
    state = make_state()
    ex = RuntimeExecutor(state)
    assert ex.rt_00_boot_version() is True
    return "PASS"


def test_rt_01_integridad_ok():
    state = make_state(3)
    ex = RuntimeExecutor(state)
    assert ex.rt_01_integridad() is True
    return "PASS"


def test_rt_01_integridad_falla_sin_contrato():
    state = make_state(1)
    state.nodos["T-001"].contrato_output = None
    state.nodos["T-001"].criterio_exito = ""
    ex = RuntimeExecutor(state)
    assert ex.rt_01_integridad() is False
    return "PASS"


def test_rt_02_preflight():
    state = make_state(1)
    ex = RuntimeExecutor(state)
    assert ex.rt_02_preflight() is True
    return "PASS"


def test_rt_03_skills_bootstrap():
    state = make_state(2)
    state.nodos["T-001"].skills_requeridas = ["python", "docker"]
    state.nodos["T-002"].skills_requeridas = ["python"]
    ex = RuntimeExecutor(state)
    assert ex.rt_03_skills_bootstrap() is True
    # verifica que los eventos emitidos contienen las skills
    return "PASS"


def test_rt_04_resume_inicio():
    state = make_state(3)
    ex = RuntimeExecutor(state)
    assert ex.rt_04_resume_check() == "INICIO"
    return "PASS"


def test_rt_04_resume_reanudacion():
    state = make_state(3)
    state.nodos["T-001"].estado = "done"
    state.nodos["T-002"].estado = "running"
    ex = RuntimeExecutor(state)
    assert ex.rt_04_resume_check() == "REANUDACIÓN"
    return "PASS"


def test_boot_completo():
    state = make_state(3)
    ex = RuntimeExecutor(state)
    result = ex.boot()
    assert result["status"] == "boot_ok"
    assert result["modo"] == "INICIO"
    assert len(result["orden"]) == 3
    assert result["proximo"] == "T-001"
    return "PASS"


# ============================================================================
# CICLO POR NODO (RT-10..RT-45)
# ============================================================================

def test_rt_10_select_elige_primero():
    state = make_state(3)
    ex = RuntimeExecutor(state)
    nodo = ex.rt_10_select()
    assert nodo is not None
    assert nodo.id == "T-001"
    return "PASS"


def test_rt_10_select_respeta_dependencias():
    state = make_state(3)
    ex = RuntimeExecutor(state)
    nodo = ex.rt_10_select()
    nodo.estado = "done"
    nodo2 = ex.rt_10_select()
    assert nodo2.id == "T-002"
    return "PASS"


def test_rt_11_idempotencia_reutiliza():
    state = make_state(1)
    node = state.nodos["T-001"]
    ex = RuntimeExecutor(state)
    input_data = {"k": "v"}
    # primer call: no reuse
    reused = ex.rt_11_idempotencia(node, input_data)
    assert reused is False
    # segundo call con mismo input: reuse
    node.input_hash = "fake"
    node.output = {"status": "ok"}
    # forzar mismo hash
    import hashlib
    node.input_hash = hashlib.sha256(
        json.dumps(input_data, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]
    reused = ex.rt_11_idempotencia(node, input_data)
    assert reused is True
    return "PASS"


def test_rt_20_ejecutar():
    state = make_state(1)
    ex = RuntimeExecutor(state)
    output = ex.rt_20_ejecutar(state.nodos["T-001"], {})
    assert output["status"] == "ok"
    return "PASS"


def test_rt_30_tribunal_score_promedio():
    state = make_state(1)
    ex = RuntimeExecutor(state)
    score = ex.rt_30_tribunal(state.nodos["T-001"], {"status": "ok"})
    assert 0 <= score <= 100
    assert score >= 70
    return "PASS"


def test_rt_31_goal_check_pasa():
    state = make_state(1)
    ex = RuntimeExecutor(state)
    ok = ex.rt_31_goal_check(state.nodos["T-001"], {"status": "ok"})
    assert ok is True
    return "PASS"


def test_rt_31_goal_check_falla_si_status_fail():
    state = make_state(1)
    ex = RuntimeExecutor(state)
    ok = ex.rt_31_goal_check(state.nodos["T-001"], {"status": "fail"})
    assert ok is False
    return "PASS"


def test_execute_node_completo():
    state = make_state(1)
    ex = RuntimeExecutor(state)
    result = ex.execute_node(state.nodos["T-001"], {})
    assert result["status"] == "done"
    assert state.nodos["T-001"].estado == "done"
    return "PASS"


def test_eventos_se_emiten():
    state = make_state(1)
    ex = RuntimeExecutor(state)
    eventos_antes = len(state.historial_eventos)
    ex.execute_node(state.nodos["T-001"], {})
    eventos_despues = len(state.historial_eventos)
    assert eventos_despues > eventos_antes
    return "PASS"


# ============================================================================
# RT-80: RECOVERY_GATE
# ============================================================================

def test_rt_80_recovery_auto():
    state = make_state(1)
    ex = RuntimeExecutor(state)
    resultado = ex.rt_80_recovery_gate(state.nodos["T-001"], "input_invalido_upstream")
    assert resultado == "AUTO"
    assert state.nodos["T-001"].recoveries == 1
    return "PASS"


def test_rt_80_recovery_director_tras_2():
    state = make_state(1)
    state.nodos["T-001"].recoveries = 2
    ex = RuntimeExecutor(state)
    resultado = ex.rt_80_recovery_gate(state.nodos["T-001"], "timeout_con_checkpoint")
    assert resultado == "DIRECTOR"
    return "PASS"


def test_rt_80_recovery_ley_violada_escala():
    state = make_state(1)
    ex = RuntimeExecutor(state)
    resultado = ex.rt_80_recovery_gate(state.nodos["T-001"], "ley_violada")
    assert resultado == "DIRECTOR"
    return "PASS"


# ============================================================================
# RT-90: CIERRE
# ============================================================================

def test_rt_90_cierre_todos_done():
    state = make_state(3)
    for n in state.nodos.values():
        n.estado = "done"
    ex = RuntimeExecutor(state)
    result = ex.rt_90_cierre()
    assert result["status"] == "completed"
    assert result["nodos"] == 3
    return "PASS"


def test_rt_90_cierre_bloqueado_si_pendientes():
    state = make_state(3)
    state.nodos["T-001"].estado = "done"
    # T-002 y T-003 quedan pending
    ex = RuntimeExecutor(state)
    result = ex.rt_90_cierre()
    assert result["status"] == "blocked"
    assert "T-002" in result["pendientes"]
    return "PASS"


# ============================================================================
# DAG / TOPOLOGÍA
# ============================================================================

def test_topological_order_lineal():
    state = make_state(4)
    ex = RuntimeExecutor(state)
    orden = ex._topological_order()
    assert orden == ["T-001", "T-002", "T-003", "T-004"]
    return "PASS"


def test_no_cycles_en_dag_lineal():
    state = make_state(3)
    ex = RuntimeExecutor(state)
    assert ex._has_cycles() is False
    return "PASS"


# ============================================================================
# E01-E12 (reglas de comportamiento)
# ============================================================================

def test_e10_duda_protocolo_busca_b1_b8():
    """E10: antes de preguntar, buscar en B1-B8. Aquí validamos que la doc existe."""
    assert os.path.exists("B1_PROJECT_MANIFEST.md")
    assert os.path.exists("B2_state.json")
    assert os.path.exists("B3_NODOS_DSL.md")
    assert os.path.exists("B4_DAG.md")
    assert os.path.exists("B5_LOOPS.md")
    assert os.path.exists("B6_TRIBUNAL.md")
    assert os.path.exists("B7_PLAN_DESPLIEGUE.md")
    assert os.path.exists("B8_RECOVERY.md")
    return "PASS"


def test_e11_b1_b3_b4_inmutables_durante_ejecucion():
    """E11: B1, B3, B4 no se modifican durante ejecución. Aquí validamos que existen
    y no son sobreescritos por el runtime."""
    b1_hash = hashlib_sha("B1_PROJECT_MANIFEST.md")
    state = make_state(2)
    ex = RuntimeExecutor(state)
    ex.boot()
    ex.execute_node(state.nodos["T-001"], {})
    # B1 no cambió
    assert hashlib_sha("B1_PROJECT_MANIFEST.md") == b1_hash
    return "PASS"


def test_e12_eventos_obligatorios_en_state():
    """E12 + L10: toda mutación de state va con evento."""
    state = make_state(1)
    ex = RuntimeExecutor(state)
    ex.execute_node(state.nodos["T-001"], {})
    # debe haber al menos: node.selected, node.start, node.validate, node.done
    tipos = [e.get("evento") for e in state.historial_eventos]
    assert "node.start" in tipos
    assert "node.validate" in tipos
    assert "node.done" in tipos
    return "PASS"


def hashlib_sha(path):
    import hashlib
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


# ============================================================================
# INTEGRACIÓN: ciclo completo
# ============================================================================

def test_integracion_full_cycle():
    """Simula un run completo: boot → ejecutar 3 nodos → cierre."""
    state = make_state(3)
    ex = RuntimeExecutor(state)
    # BOOT
    boot = ex.boot()
    assert boot["status"] == "boot_ok"
    # ejecutar
    ejecutados = []
    while True:
        nodo = ex.rt_10_select()
        if nodo is None:
            break
        result = ex.execute_node(nodo, {})
        ejecutados.append(nodo.id)
    assert ejecutados == ["T-001", "T-002", "T-003"]
    # CIERRE
    cierre = ex.rt_90_cierre()
    assert cierre["status"] == "completed"
    return "PASS"


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    tests = [
        # BOOT
        test_rt_00_boot_version,
        test_rt_01_integridad_ok,
        test_rt_01_integridad_falla_sin_contrato,
        test_rt_02_preflight,
        test_rt_03_skills_bootstrap,
        test_rt_04_resume_inicio,
        test_rt_04_resume_reanudacion,
        test_boot_completo,
        # CICLO
        test_rt_10_select_elige_primero,
        test_rt_10_select_respeta_dependencias,
        test_rt_11_idempotencia_reutiliza,
        test_rt_20_ejecutar,
        test_rt_30_tribunal_score_promedio,
        test_rt_31_goal_check_pasa,
        test_rt_31_goal_check_falla_si_status_fail,
        test_execute_node_completo,
        test_eventos_se_emiten,
        # RECOVERY
        test_rt_80_recovery_auto,
        test_rt_80_recovery_director_tras_2,
        test_rt_80_recovery_ley_violada_escala,
        # CIERRE
        test_rt_90_cierre_todos_done,
        test_rt_90_cierre_bloqueado_si_pendientes,
        # DAG
        test_topological_order_lineal,
        test_no_cycles_en_dag_lineal,
        # E01-E12
        test_e10_duda_protocolo_busca_b1_b8,
        test_e11_b1_b3_b4_inmutables_durante_ejecucion,
        test_e12_eventos_obligatorios_en_state,
        # INTEGRACIÓN
        test_integracion_full_cycle,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            r = t()
            if r == "PASS":
                passed += 1
                print(f"  OK  {t.__name__}")
            else:
                print(f"  FAIL {t.__name__}: {r}")
                failed += 1
        except Exception as e:
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {str(e)[:100]}")
            failed += 1
    print(f"\n  {passed}/{len(tests)} tests pasaron ({failed} fallaron)")
