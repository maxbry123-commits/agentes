# TAREAS VPS PARA MIMO-CODE-VPS-A

Eres mimo-code-vps-A (coder, gemma-4-31b via LiteLLM).
Trabajas en el VPS (95.111.232.89) como root.

## Lista de tareas pendientes
1. Verificar que /opt/nct/scripts/health/nct_health.sh existe y es ejecutable
   (si no, crealo basandote en lo que el sistema tiene)
2. Verificar que los 4 logs/ dirs de los 4 subagentes existen
3. Crear /opt/nct/scripts/health/audit_security.sh que verifique:
   - fail2ban activo
   - ssh: NO password (key only) (esto es info, no se cambia)
   - secretos con permisos 600
   - logs no contienen keys
4. Crear /opt/nct/scripts/health/check_git.sh que verifique:
   - 16/16 repos existen
   - SSH a github funciona
   - Branch main existe en cada uno
5. Ejecutar todos los scripts que crees y reportar el resultado

## Output esperado
- Archivos creados (rutas)
- Output de cada script (OK/FAIL por seccion)
- Tabla resumen al final
