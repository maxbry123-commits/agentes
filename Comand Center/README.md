COMAND CENTER — AGENTE YAIWES

Schema operativo: comand-center.trigger-engine/v1
Repositorio: maxbry123-commits/agentes
Rama: main
Modo de construcción: FAIL_CLOSED_STRICT_3_STEPS

PROPÓSITO

Comand Center es un disparador acotado para el agente SEALS ya existente. No sustituye al agente, no crea un segundo runtime y no reimplementa seals_core. Su única responsabilidad operativa es leer el inventario físico del Core Kernel, localizar los registros cuyo wall_status sea PENDING_STEP1 y entregar cada uno de esos registros, dentro de los límites configurados, a la función existente Seals team YAIWES/seals_core/ejecutor.py::ejecutar_tarea().

FUENTES AUTORITATIVAS LEÍDAS POR ESTA CONSTRUCCIÓN

1. Claude readme/Readme Claude.md
   Es la memoria del orquestador y la única raíz real de memoria indicada para este trabajo.

2. Seals team YAIWES/dag_schema.yaml
   Define el ciclo ya construido del primer agente. Comand Center no lo reemplaza.

3. Seals team YAIWES/seals_core/
   Contiene el código real del agente. Esta carpeta se trata como solo lectura desde Comand Center. El dispatcher carga específicamente seals_core/ejecutor.py y llama a ejecutar_tarea(tarea).

4. Core kernel Yaiwes/CORE-KERNEL-COMPONENT-INVENTORY.json
   Es la fuente de nodos que pueden ser considerados por el dispatcher. El inventario leído durante esta construcción declara actualmente component_count=245. El código no fija ese número: siempre lee el valor y la lista de componentes desde el archivo fresh.

ESTRUCTURA

Comand Center/
  comandante_tactico_seal.py
  config_disparo.json
  webhook_listener.py
  idempotencia.py
  README.md

No se requiere ningún otro archivo versionado para que esta construcción exista. idempotencia.py puede generar en tiempo de ejecución un archivo local .control_disparos.json para conservar el estado de disparos y SHA procesados; ese archivo es estado de ejecución, no código fuente ni parte de esta estructura versionada.

FLUJO EXACTO DEL DISPATCHER

El flujo implementado en comandante_tactico_seal.py es el siguiente:

1. Recibe un commit SHA como identificador del ciclo.
2. Lee config_disparo.json.
3. Verifica que los cuatro valores del archivo de configuración sean exactamente los valores fijos autorizados. Si cambian, falla cerrado con CONFIG_DISPARO_NO_COINCIDE_CON_CONTRATO_FIJO.
4. Si requiere_sha_no_procesado está activo, consulta idempotencia.py y evita volver a disparar un SHA ya cerrado.
5. Lee Core kernel Yaiwes/CORE-KERNEL-COMPONENT-INVENTORY.json.
6. Filtra exclusivamente los elementos cuyo wall_status sea PENDING_STEP1.
7. Calcula cuántos disparos se han registrado durante la última hora.
8. Calcula el cupo horario restante con el máximo fijo de 20 disparos por hora.
9. Calcula el cupo de presupuesto del ciclo usando el máximo fijo de 200 llamadas LLM. Para PENDING_STEP1 se usa el tipo ya existente evaluar_componente, cuya ruta actual en ejecutar_tarea realiza una llamada LLM por tarea.
10. Calcula limite_ciclo como el mínimo entre cantidad de PENDING_STEP1, cupo horario y cupo de presupuesto. Por esta razón el bucle de despacho siempre tiene un límite superior explícito.
11. Para cada nodo dentro de pendientes[:limite_ciclo], crea únicamente el diccionario que exige ejecutar_tarea: tipo, nombre, url y descripcion.
12. tipo se fija en evaluar_componente porque esa rama ya existe en seals_core/ejecutor.py y corresponde a la evaluación STEP1. No se añade un nuevo tipo de tarea.
13. Antes de invocar el ejecutor, registra el intento de disparo para que el límite horario no dependa de que una llamada externa termine correctamente.
14. Invoca la función existente ejecutar_tarea(tarea).
15. Si un nodo produce una excepción, registra el GAP en el resultado del ciclo y continúa con los demás nodos que todavía están dentro del límite. No crea un bucle de reintentos ilimitado.
16. Si existen más PENDING_STEP1 que cupo disponible, el ciclo devuelve un GAP LIMITE_EXCEDIDO con la acción fija PAUSAR_Y_REGISTRAR_GAP_NO_DETENER_PROYECTO.
17. Al cerrar un ciclo que sí pudo ejecutar su lote acotado, registra el commit SHA como procesado para impedir el doble disparo del mismo evento.
18. Devuelve un objeto JSON con schema, SHA, estado del ciclo, número de disparos, presupuesto estimado utilizado, resultados y GAPS.

CARGA DEL EJECUTOR EXISTENTE

La ruta física contiene espacios: Seals team YAIWES/seals_core/ejecutor.py. Por esa razón no puede expresarse como un import de paquete Python convencional con ese nombre de directorio. comandante_tactico_seal.py usa importlib únicamente para cargar ese archivo físico exacto. Antes de cargarlo añade seals_core al sys.path para que los imports locales ya existentes dentro de ejecutor.py, concretamente instalador_deterministico, consultor_experto y verificador, sigan resolviendo como fueron escritos.

Esta carga dinámica no copia ejecutor.py, no modifica seals_core, no altera dag_schema.yaml y no crea una arquitectura paralela. Su resultado es obtener la función callable ejecutar_tarea que ya existe.

CONFIGURACIÓN FIJA DE SEGURIDAD

config_disparo.json contiene exactamente:

{
  "max_disparos_por_hora": 20,
  "requiere_sha_no_procesado": true,
  "presupuesto_maximo_llamadas_llm_por_ciclo": 200,
  "si_limite_excedido": "PAUSAR_Y_REGISTRAR_GAP_NO_DETENER_PROYECTO"
}

comandante_tactico_seal.py valida el objeto completo. No acepta silenciosamente una configuración distinta.

IDEMPOTENCIA

idempotencia.py mantiene dos tipos de información de ejecución:

- shas_procesados: lista de commit SHA cuyos ciclos ya fueron cerrados.
- disparos: registros recientes con commit_sha, component_id y timestamp.

El SHA se valida para impedir cadenas vacías. registrar_sha_procesado no inserta dos veces el mismo SHA. contar_disparos_ultima_hora utiliza una ventana móvil de una hora. registrar_disparo elimina del bloque de disparos operativos los registros anteriores a esa ventana antes de guardar el nuevo intento. El guardado utiliza un archivo temporal y os.replace para reducir el riesgo de dejar un estado parcialmente escrito.

El estado local por defecto se llama .control_disparos.json y se crea junto a idempotencia.py únicamente cuando el dispatcher se ejecuta. No almacena API keys ni secretos.

LÍMITES Y COMPORTAMIENTO FAIL-CLOSED

No existe un bucle infinito en Comand Center. El único bucle de dispatch recorre una porción finita pendientes[:limite_ciclo]. limite_ciclo nunca puede superar max_disparos_por_hora restante ni el presupuesto LLM restante.

Cuando el cupo disponible es cero y existen nodos pendientes, el dispatcher no llama al agente. Devuelve PAUSADO_LIMITE y un GAP con la acción PAUSAR_Y_REGISTRAR_GAP_NO_DETENER_PROYECTO.

Cuando el lote permitido es menor que la cantidad de nodos pendientes, procesa solamente el lote autorizado y registra cuántos quedaron fuera del ciclo actual. No amplía el límite y no entra en un segundo bucle para saltarse la restricción.

Si una ejecución individual falla, ese fallo no autoriza un bucle ilimitado. El dispatcher registra EJECUCION_GAP y continúa con los demás elementos ya incluidos en el lote acotado.

WEBHOOK LISTENER

webhook_listener.py es intencionalmente un placeholder. No instala Flask, FastAPI ni otro servidor. No abre un socket y no registra endpoints.

El contrato documentado para el trabajo futuro de Claude es:

1. recibir un push event de GitHub;
2. extraer el commit SHA del evento;
3. entregar ese SHA a comandante_tactico_seal.ejecutar_ciclo().

La función recibir_push_github_placeholder() lanza NotImplementedError para dejar claro que el servidor HTTP todavía no existe y evitar que un placeholder sea interpretado como un listener productivo.

EJECUCIÓN MANUAL DEL DISPATCHER

Desde la raíz del repositorio se puede invocar:

python "Comand Center/comandante_tactico_seal.py" <COMMIT_SHA>

El comando imprime el resultado del ciclo como JSON. La ejecución real puede llegar a la ruta evaluar_componente del agente SEALS y, por tanto, a su cliente LLM existente. Comand Center no contiene ni suministra las credenciales de Cerebras. Las credenciales siguen siendo responsabilidad del mecanismo ya existente fuera de estos archivos.

REGLAS QUE ESTA CARPETA NO ROMPE

- No modifica Seals team YAIWES/seals_core/.
- No modifica Seals team YAIWES/dag_schema.yaml.
- No crea ni usa GitHub Actions.
- No escribe API keys de Cerebras.
- No copia componentes del Core Kernel.
- No decide una arquitectura nueva para los componentes.
- No crea un segundo ejecutor.
- No procesa componentes cuyo wall_status no sea PENDING_STEP1.
- No crea un bucle sin límite superior.
- No implementa todavía el servidor HTTP del webhook.

RELACIÓN CON EL DAG EXISTENTE

El DAG de SEALS sigue siendo la definición del ciclo del agente. Comand Center únicamente actúa como punto de disparo inicial para los registros PENDING_STEP1. La selección, evaluación y ejecución siguen ocurriendo mediante el código existente. Este cambio no redefine las etapas del DAG ni modifica sus estados.

EVIDENCIA Y VALIDACIÓN

La construcción debe considerarse válida solamente si se comprueban estas condiciones sobre main:

- existen exactamente los cinco archivos descritos para Comand Center;
- config_disparo.json coincide exactamente con los cuatro valores fijos;
- los tres archivos Python compilan sin SyntaxError;
- un inventario de prueba con más de 20 PENDING_STEP1 nunca produce más de 20 disparos cuando la ventana horaria está vacía;
- la segunda ejecución con el mismo SHA es rechazada por idempotencia;
- webhook_listener.py sigue siendo un placeholder y no contiene un servidor HTTP;
- el árbol Seals team YAIWES/seals_core/ permanece sin modificación;
- cada archivo creado tiene evidencia de path y sha256.

No se declara PASS si alguna de esas comprobaciones falta.
