from enchufe.validator_v2 import validar, normalizar_v15, compatibles


def test_v15_valida_bajo_v20() -> None:
    ficha_v15 = {
        "artifact_id": "maxbry.test.module",
        "version": "1.0.0",
        "estado": "draft",
        "contrato": {"rol": "transform", "consume": {"datatype": {"family": "x", "type": "y", "version": 1}}, "expone": {"datatype": {"family": "x", "type": "z", "version": 1}}},
        "ejecucion": {"kind": "code", "transport": "stdio", "runtime_type": "compute", "llm_ratio": 0.0},
        "seguridad": {"sandbox": "process", "limites": {"timeout_ms": 5000}},
        "firma": {"gpg_key_id": "test"},
    }
    v = validar(ficha_v15)
    assert v.valido is True
    assert v.ficha_normalizada is not None
    assert v.ficha_normalizada["categoria"] == "pipeline"


def test_acelerador_fuera_de_A_falla() -> None:
    ficha = {
        "artifact_id": "maxbry.accel.test",
        "version": "1.0.0",
        "estado": "draft",
        "categoria": "acelerador",
        "etapa": "P",
        "contrato": {"rol": "service"},
        "ejecucion": {"kind": "code", "transport": "stdio", "runtime_type": "compute"},
        "seguridad": {"sandbox": "none", "limites": {"timeout_ms": 1000}},
        "firma": {"gpg_key_id": "x"},
    }
    v = validar(ficha)
    assert v.valido is False
    assert "V03_acelerador_etapa_A" in v.errores


def test_compatibles_datatype() -> None:
    a = {"contrato": {"expone": {"datatype": {"family": "t", "type": "u", "version": 1}}}}
    b = {"contrato": {"consume": {"datatype": {"family": "t", "type": "u", "version": 1}}}}
    assert compatibles(a, b) is True
