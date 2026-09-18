SOL GPT - GENERAR REQUIREMENTS.TXT REPRODUCIBLE (P2-32) - AGENTE YAIWES
(sin Crazy Wall, tarea mecanica)

OBJETIVO
El archivo actual usa >= (rangos), no versiones fijas - dos instalaciones
en momentos distintos pueden traer versiones distintas. Necesito el lock
real, no que yo invente numeros de version sin verificar.

PASOS
1. En un entorno limpio, instalar: requests>=2.31.0, claude-agent-sdk>=0.1.0,
   tenacity>=8.2.0, pyyaml>=6.0
2. Correr: pip freeze > requirements.lock.txt
3. Confirmar que instalar DESDE ESE lock en un entorno limpio nuevo trae
   exactamente las mismas versiones (aceptacion de P2-32).

DESTINO: Seals team YAIWES/requirements.lock.txt (nuevo archivo, no
reemplaza requirements.txt, que se queda con los rangos como referencia
de compatibilidad minima).

REPORTA EN: Claude notas/EVIDENCIA-DESCARGA-4-COMPONENTES.md (mismo
archivo de evidencia de descargas ya en uso).

INICIA AHORA.
