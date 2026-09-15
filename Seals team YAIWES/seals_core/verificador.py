"""
verificador.py - Gate final de baja frecuencia. Unico lugar donde SI
puede pasar por Claude (bajo volumen). Nunca decide flujo por si solo,
solo devuelve un veredicto que el ejecutor determinista aplica.
Codigo real, no placeholder. Requiere: pip install claude-agent-sdk
"""
import os


def verificar_con_claude(tarea: dict) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"status": "GAP", "detalle": "ANTHROPIC_API_KEY no configurada como variable de entorno"}

    try:
        from claude_agent_sdk import query
    except ImportError:
        return {"status": "GAP", "detalle": "claude-agent-sdk no instalado. pip install claude-agent-sdk"}

    prompt = (
        f"Verifica si este cambio de arquitectura es correcto para YAIWES.\n"
        f"Tarea: {tarea}\n"
        f"Responde SOLO con la palabra CORRECTO o INCORRECTO, seguida de una linea de motivo."
    )
    try:
        resultado = query(prompt=prompt, model="claude-sonnet-5")
        texto = str(resultado)
        status = "PASS" if "CORRECTO" in texto.upper() and "INCORRECTO" not in texto.upper() else "GAP"
        return {"status": status, "detalle": texto}
    except Exception as e:
        return {"status": "GAP", "detalle": f"ERROR_CLAUDE_SDK: {e}"}
