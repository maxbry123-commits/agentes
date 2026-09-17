SOL GPT - DESCARGA DE 4 COMPONENTES NUEVOS - AGENTE YAIWES
(sin Crazy Wall - Crazy Wall solo para tareas importantes, esta es mecanica)

schema: yaiwes.component-ops/v1
repo: maxbry123-commits/agentes | branch: main | modo: FAIL_CLOSED_STRICT_3_STEPS

MOTOR (ubicacion exacta, mismo de siempre):
https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Download%20code%20Yaiwes/RESEARCH_DOWNLOAD_MANIFEST.jsonl

OBJETIVO
Investigar y descargar estos 4 componentes. NO ESTAN VERIFICADOS - antes
de descargar, confirma que existen de verdad (repo real en GitHub) y
reporta la URL exacta que encontraste, no una que asumas.

COMPONENTES A INVESTIGAR Y DESCARGAR:
1. Omniroute - gateway para enrutar entre proveedores de IA sin quedarse
   sin cuota. DESTINO: Core kernel Yaiwes/omniroute/
2. Orca - entorno grafico para orquestar multiples agentes (Cloud Code,
   Codex, etc). DESTINO: Core kernel Yaiwes/orca/
3. Omarchy - distro de DHH basada en Arch Linux. DESTINO: Core kernel
   Yaiwes/omarchy/ (nota: esto es una distro de sistema operativo, no una
   libreria - confirma que aplica antes de descargar el repo completo)
4. Anydoc - libreria en Rust que convierte archivos a Markdown. DESTINO:
   Core kernel Yaiwes/anydoc/

FORMATO DE ENTRADA AL MANIFEST (mismo esquema ya en uso):
{"number": N, "parts": 1, "slug": "<nombre>", "source": "<URL real
encontrada>.git", "source_commit": "<HEAD real al clonar>", "status":
"COMPLETE" o "NOT_FOUND_VERIFY_WITH_DIRECTOR"}

REGLAS
1. Si un componente NO existe o no lo encuentras con certeza, marca
   status: NOT_FOUND_VERIFY_WITH_DIRECTOR - NUNCA inventes una URL.
2. Clona cada uno, fija source_commit al HEAD real.
3. NO decidas destino final dentro de Agente Yaiwes principal - eso lo
   asigna el motor de inventario despues.
4. Evidencia obligatoria: sha del commit clonado + confirmacion de que
   el archivo aparece en el destino indicado.

REPORTA EN: Claude notas/EVIDENCIA-DESCARGA-4-COMPONENTES.md (crear este
archivo, NO en el Crazy Wall).

INICIA AHORA.
