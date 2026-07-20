#!/usr/bin/env python3
"""
_generate_template.py — genera el HTML de validación para un agente
usando el template de openclaw/index.html y el validation.json del dir.

Uso:
  python3 _generate_template.py <agent_id>
  # crea <agent_id>/index.html si no existe
"""
import json, os, sys, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
TEMPLATE_PATH = ROOT / "openclaw" / "index.html"

TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>{nombre} — Validation</title>
<style>
  body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#0e0f12; color:#e6e6e6; margin:0; padding:24px; line-height:1.5; }}
  h1 {{ color:#ff6b35; border-bottom:2px solid #ff6b35; padding-bottom:8px; }}
  h2 {{ color:#00b4d8; margin-top:32px; padding:6px 12px; background:#1c1f24; border-left:4px solid #00b4d8; }}
  .ok {{ color:#3ddc97; font-weight:600; }}
  .pending {{ color:#ffd166; font-weight:600; }}
  .fail {{ color:#ef476f; font-weight:600; }}
  code, pre {{ background:#1c1f24; padding:2px 6px; border-radius:4px; font-family:"JetBrains Mono",Menlo,monospace; font-size:0.9em; }}
  pre {{ padding:12px; overflow-x:auto; }}
  table {{ border-collapse:collapse; width:100%; margin:12px 0; }}
  th, td {{ border:1px solid #2a2d33; padding:8px 12px; text-align:left; }}
  th {{ background:#1c1f24; }}
  .badge {{ display:inline-block; padding:2px 8px; border-radius:10px; font-size:0.8em; font-weight:600; }}
  .badge-platinum {{ background:#e5e4e2; color:#0e0f12; }}
  .badge-gold     {{ background:#d4af37; color:#0e0f12; }}
  .badge-silver   {{ background:#c0c0c0; color:#0e0f12; }}
  .badge-bronze   {{ background:#cd7f32; color:#fff; }}
  .summary {{ background:#1c1f24; padding:16px; border-radius:8px; margin:16px 0; }}
</style>
</head>
<body>

<h1>🤖 {nombre} — Validation Card</h1>
<div class="summary">
  <strong>ID:</strong> <code>{id}</code> &nbsp;·&nbsp;
  <strong>Provider:</strong> {provider} &nbsp;·&nbsp;
  <strong>Modelo:</strong> {model} &nbsp;·&nbsp;
  <span class="badge badge-{tier}">{tier_upper}</span><br>
  <strong>Endpoint:</strong> <code>{endpoint}</code> &nbsp;·&nbsp;
  <strong>Auth:</strong> <code>{auth}</code>
</div>

<h2>1. Info general</h2>
<p>{descripcion}</p>

<h2>2. Comandos ejecutados</h2>
<pre><code>{comandos}</code></pre>
<p class="pending">Status: pendiente ejecutar.</p>

<h2>3. Verificación binario</h2>
<table>
  <tr><th>binario</th><td><code>{binario}</code></td></tr>
  <tr><th>versión</th><td><code>{version_cmd}</code></td></tr>
  <tr><th>ubicación</th><td><code>{ubicacion}</code></td></tr>
</table>

<h2>4. MCP</h2>
<table>
  <tr><th>id</th><th>transport</th><th>endpoint</th><th>tools</th><th>ping</th></tr>
  {mcp_rows}
</table>

<h2>5. API Endpoints</h2>
<table>
  <tr><th>method</th><th>path</th><th>auth</th><th>status esperado</th></tr>
  {api_rows}
</table>

<h2>6. Skills / Tools instalados</h2>
<p>{skills_list}</p>

<h2>7. Test funcional</h2>
<p><strong>Prompt:</strong> <em>"{prompt}"</em></p>
<p><strong>Respuesta esperada:</strong> <em>"{respuesta}"</em></p>
<p><strong>Score mínimo:</strong> {score}.</p>

<h2>8. Config persistente</h2>
<ul>
  <li><strong>Config:</strong> <code>{config_path}</code></li>
  <li><strong>Env vars:</strong> <code>{env_vars}</code></li>
</ul>

<h2>9. Trazabilidad investigación</h2>
<ul>
  {trazabilidad_rows}
</ul>

<h2>10. Conectividad sistema</h2>
<table>
  <tr><th>servicio</th><th>puerto</th><th>status</th></tr>
  {conectividad_rows}
</table>

<h2>11. Tests finales</h2>
<table>
  <tr><th>nombre</th><th>esperado</th><th>status</th></tr>
  {tests_rows}
</table>

<hr>
<p style="color:#888;font-size:0.85em">Generado por M3 (sesión root) — 2026-07-20. Fuente: <code>validation.json</code>.</p>

</body>
</html>
"""

def render(agent_id):
    vpath = ROOT / agent_id / "validation.json"
    if not vpath.exists():
        return None
    v = json.loads(vpath.read_text())
    s = v["sections"]
    g = lambda k, d="": s.get(k, {}).get("dato", d)
    info = s["1_info_general"]
    mcps = s.get("4_mcp", {}).get("servidores", [])
    mcp_rows = "\n".join(
        f"<tr><td>{m['id']}</td><td>{m['transport']}</td><td><code>{m['endpoint']}</code></td><td>{', '.join(m.get('tools',[]))}</td><td class='pending'>pendiente</td></tr>"
        for m in mcps
    ) or "<tr><td colspan='5' class='pending'>pendiente</td></tr>"
    api_rows = "\n".join(
        f"<tr><td>{a['method']}</td><td><code>{a['path']}</code></td><td>{a['auth']}</td><td>{a['status_esperado']}</td></tr>"
        for a in s.get("5_api_endpoints", [])
    ) or "<tr><td colspan='4' class='pending'>pendiente</td></tr>"
    tests = s.get("11_tests_finales", [])
    tests_rows = "\n".join(
        f"<tr><td>{t['nombre']}</td><td>{t['esperado']}</td><td class='pending'>{t.get('status','pendiente')}</td></tr>"
        for t in tests
    ) or "<tr><td colspan='3' class='pending'>pendiente</td></tr>"
    conectividad = s.get("10_conectividad_sistema", {}).get("habla_con", [])
    conectividad_rows = "\n".join(
        f"<tr><td>{c['servicio']}</td><td>{c['puerto']}</td><td class='{c.get('status_class','pending')}'>{c['status']}</td></tr>"
        for c in conectividad
    ) or "<tr><td colspan='3' class='pending'>pendiente</td></tr>"
    traz = s.get("9_trazabilidad_investigacion", [])
    traz_rows = "\n".join(
        f'<li><a href="{t["url"]}">{t.get("tipo","link")}</a></li>' for t in traz
    ) or "<li class='pending'>pendiente</li>"
    cmds = s.get("2_comandos_ejecutados", [])
    cmds_text = "\n".join(f"$ {c['cmd']}\n{c.get('esperado','')}" for c in cmds) or "(pendiente)"
    cfg = s.get("8_config_persistente", {})
    return TEMPLATE.format(
        id=info["id"], nombre=info["nombre"], provider=info["provider"], model=info["model"],
        tier=info["tier"], tier_upper=info["tier"].upper(),
        endpoint=info["endpoint"], auth=info.get("auth","N/A"),
        descripcion=info.get("descripcion",""),
        comandos=cmds_text,
        binario=s.get("3_verificacion_binario", {}).get("binario", info["id"]),
        version_cmd=s.get("3_verificacion_binario", {}).get("version_cmd", "N/A"),
        ubicacion=s.get("3_verificacion_binario", {}).get("ubicacion", "N/A"),
        mcp_rows=mcp_rows, api_rows=api_rows, tests_rows=tests_rows,
        conectividad_rows=conectividad_rows, trazabilidad_rows=traz_rows,
        skills_list=", ".join(s.get("6_skills_tools", {}).get("skills_instalados", []) or ["(pendiente)"]),
        prompt=s.get("7_test_funcional", {}).get("prompt", "(pendiente)"),
        respuesta=s.get("7_test_funcional", {}).get("respuesta_esperada", "(pendiente)"),
        score=s.get("7_test_funcional", {}).get("score_minimo", "0.8"),
        config_path=cfg.get("config_path","(pendiente)"),
        env_vars=", ".join(cfg.get("env_vars", []) or ["(pendiente)"]),
    )

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if target:
        out = render(target)
        if out is None:
            print(f"[skip] {target} no tiene validation.json")
            sys.exit(0)
        (ROOT / target / "index.html").write_text(out)
        print(f"[gen] {target}/index.html")
    else:
        for d in sorted(ROOT.iterdir()):
            if d.is_dir() and (d / "validation.json").exists() and d.name != "openclaw":
                out = render(d.name)
                if out:
                    (d / "index.html").write_text(out)
                    print(f"[gen] {d.name}/index.html")

if __name__ == "__main__":
    main()
