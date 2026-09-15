"""
verificador.py - Gate final de baja frecuencia, unico lugar donde SI
puede pasar por Claude (bajo volumen). Nunca decide flujo por si solo,
solo devuelve un veredicto que el ejecutor determinista aplica.
"""


def verificar_con_claude(tarea: dict) -> dict:
    """
    Placeholder de integracion: aqui se conecta el Claude Agent SDK
    (claude_agent_sdk.query) SOLO para verificacion final antes de cerrar
    un nodo de tipo diseno_arquitectura. Bajo volumen, nunca para tareas
    masivas de instalacion/movimiento.
    """
    # from claude_agent_sdk import query
    # resultado = query(
    #     prompt=f"Verifica si este cambio de arquitectura es correcto: {tarea}",
    #     model="claude-sonnet-5",
    # )
    # status = "PASS" if "CORRECTO" in resultado.upper() else "GAP"
    # return {"status": status, "detalle": resultado}
    return {"status": "PENDIENTE_INTEGRACION_SDK", "detalle": "conectar claude_agent_sdk aqui"}
