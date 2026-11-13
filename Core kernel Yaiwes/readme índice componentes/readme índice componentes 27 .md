# README ÍNDICE COMPONENTES 27 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes` · Rama: `main` · Bloque documental: **YAIWES 131–135**. Continuidad fresh: `readme índice componentes 26 .md` cerró en YAIWES 130. El inventario fresh actual declara **243 componentes** (el archivo 26 registraba 245); por tanto se usa el inventario fresh como autoridad y se registra la discrepancia sin inventar componentes. Las siguientes entradas físicas fresh son **132–136 = NetworkX, Nomad, nsjail, NVIDIA-Garak y Open-Policy-Agent**. Lo no demostrado se marca `NO VERIFICADO`.

## YAIWES 131 — NetworkX ➡️ creación, manipulación y análisis de redes/grafos complejos
**URL raíz/ubicación:** `Core kernel Yaiwes/NetworkX/`; upstream verificado por README/manifiesto: `https://github.com/networkx/networkx`.  
**Handoff:** inventario físico fresh `132`; Crazy Wall nodo `233`, paso `1`, estado `PENDING_STEP1`, destino `None`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `NetworkX/code/README.rst` + `NetworkX/DOWNLOAD_EXTRACT_MANIFEST.json` + `CORE-KERNEL-COMPONENT-INVENTORY.md`. Manifiesto: `source_commit=4e74880b0da01977da79915167c64e5c2af38b47`, 975 archivos, extracción verificada.  
**Determinista:** **Sí / % NO VERIFICADO** para algoritmos de grafo con mismos datos, algoritmo y versión; porcentaje empírico no demostrado.  
**¿Es agente?:** No; es una biblioteca Python de grafos/redes.  
**Cómo funciona el kernel/core para tomar decisiones:** no posee planner cognitivo. Representa nodos/aristas y ejecuta algoritmos definidos sobre la estructura; el README demuestra, por ejemplo, cálculo de shortest path ponderado. La política de selección de algoritmo por un agente externo es **NO VERIFICADO**.  
**Microflujo horizontal:** `datos/relaciones → grafo NetworkX → algoritmo seleccionado → cálculo sobre nodos/aristas → resultado estructurado → consumidor/agente`.  
**Contexto estructural:** paquete Python para creación, manipulación y estudio de estructura, dinámica y funciones de redes complejas.  
**Nivel seleccionado:** graph reasoning / structural-analysis layer.  
**Qué aporta a un agente:** representación explícita de relaciones, recorridos, rutas y análisis de estructuras conectadas sin delegar esos cálculos al LLM.

## YAIWES 132 — Nomad ➡️ orquestación y scheduling de workloads distribuidos
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados B/Nomad/Nomad/`; upstream indicado por documentación del README: HashiCorp Nomad; URL Git upstream exacta: **NO VERIFICADO** en la fuente seleccionada.  
**Handoff:** inventario físico fresh `133`; Crazy Wall nodo `184`, paso `1`, estado `PENDING_STEP1`, destino `None`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Componentes recuperados B/Nomad/Nomad/README.md` + `CORE-KERNEL-COMPONENT-INVENTORY.md`.  
**Determinista:** **Sí para reglas/configuración de scheduling; % NO VERIFICADO**. El resultado temporal de un sistema distribuido ante fallos/concurrencia no queda cuantificado por el README.  
**¿Es agente?:** No; es un workload orchestrator.  
**Cómo funciona el kernel/core para tomar decisiones:** combina resource management y scheduling; coordina despliegue y gestión de contenedores, aplicaciones no containerizadas y VMs. Usa elección de líder y replicación de estado para alta disponibilidad. La heurística interna completa del scheduler no está demostrada por la fuente seleccionada: **NO VERIFICADO**.  
**Microflujo horizontal:** `job/workload → scheduler/resource manager → selección de recursos/nodo → task driver → ejecución → estado/fallo → reprogramación/gestión`.  
**Contexto estructural:** binario autocontenido, distribuido y resiliente; soporta Linux/Windows/macOS, drivers de tareas, plugins de dispositivos/GPU, federación multi-región y multi-cloud.  
**Nivel seleccionado:** execution orchestration / workload scheduling layer.  
**Qué aporta a un agente:** ejecución y placement de trabajos, tolerancia a fallos, administración de recursos y despliegue de herramientas/servicios a escala.

## YAIWES 133 — nsjail ➡️ aislamiento de procesos Linux y sandbox de ejecución
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados A/nsjail/`; upstream demostrado por README: `https://github.com/google/nsjail.git`.  
**Handoff:** inventario físico fresh `134`; Crazy Wall nodo `96`, paso `1`, estado `PENDING_STEP1`, destino `None`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Componentes recuperados A/nsjail/README.md` + `CORE-KERNEL-COMPONENT-INVENTORY.md`.  
**Determinista:** **Sí para aplicación de configuración/políticas; % NO VERIFICADO**. El resultado del proceso ejecutado dentro del jail puede no ser determinista.  
**¿Es agente?:** No; es una herramienta de aislamiento/sandbox.  
**Cómo funciona el kernel/core para tomar decisiones:** no toma decisiones cognitivas; aplica configuración explícita de namespaces, límites de recursos, filesystem, cgroups y filtros seccomp-bpf para restringir un proceso.  
**Microflujo horizontal:** `comando/proceso → configuración nsjail → namespaces + mounts + límites + seccomp → proceso aislado → salida/terminación`.  
**Contexto estructural:** soporta modos LISTEN, ONCE, EXECVE y RERUN; aislamiento UTS/MOUNT/PID/IPC/NET/USER/CGROUPS/TIME, límites CPU/memoria/procesos y políticas Kafel seccomp-bpf.  
**Nivel seleccionado:** sandbox / execution-isolation layer.  
**Qué aporta a un agente:** contención de tools/código ejecutado, límites de recursos y reducción de superficie de syscall/filesystem/red según política.

## YAIWES 134 — NVIDIA-Garak ➡️ red-teaming y evaluación de vulnerabilidades de LLM
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados A/NVIDIA-Garak/`; upstream demostrado por README: `https://github.com/NVIDIA/garak.git`.  
**Handoff:** inventario físico fresh `135`; Crazy Wall nodo `97`, paso `1`, estado `PENDING_STEP1`, destino `None`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Componentes recuperados A/NVIDIA-Garak/README.md` + `CORE-KERNEL-COMPONENT-INVENTORY.md`.  
**Determinista:** **No / % NO VERIFICADO** como evaluación completa de modelos generativos; combina probes estáticos, dinámicos y adaptativos contra LLM/sistemas de diálogo.  
**¿Es agente?:** No como agente autónomo general; es scanner/toolkit de red-teaming y assessment.  
**Cómo funciona el kernel/core para tomar decisiones:** selecciona/ejecuta probes contra un generador/modelo y usa detectores asociados para identificar fallos; el README indica que por defecto intenta todos los probes conocidos y permite seleccionar familias/plugins específicos. La política adaptativa interna completa es **NO VERIFICADO**.  
**Microflujo horizontal:** `modelo/endpoint objetivo → selección de generator → probes → respuestas del modelo → detectores → hallazgos/evaluación`.  
**Contexto estructural:** busca fallos como hallucination, data leakage, prompt injection, misinformation, toxicity y jailbreaks; soporta múltiples interfaces/modelos, incluyendo REST.  
**Nivel seleccionado:** adversarial evaluation / LLM security testing layer.  
**Qué aporta a un agente:** pruebas adversariales para descubrir debilidades antes de promover modelos, prompts o configuraciones a producción.

## YAIWES 135 — Open-Policy-Agent ➡️ evaluación declarativa y enforcement de políticas
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Open-Policy-Agent/`; upstream demostrado por badges/enlaces del README: `https://github.com/open-policy-agent/opa`.  
**Handoff:** inventario físico fresh `136`; Crazy Wall nodo `98`, paso `1`, estado `PENDING_STEP1`, destino `None`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Componentes recuperados A/Open-Policy-Agent/README.md` + `CORE-KERNEL-COMPONENT-INVENTORY.md`.  
**Determinista:** **Sí / % NO VERIFICADO** para evaluación de las mismas reglas Rego, datos e input bajo la misma versión; porcentaje empírico no demostrado.  
**¿Es agente?:** No; es un policy engine general-purpose.  
**Cómo funciona el kernel/core para tomar decisiones:** las reglas declarativas gobiernan comportamiento; un servicio consulta OPA cuando necesita una decisión, OPA evalúa reglas + datos y devuelve el resultado de política para que el servicio lo aplique.  
**Microflujo horizontal:** `evento/solicitud + contexto → query OPA → reglas Rego + datos → evaluación → decisión allow/deny u otra → servicio/agente aplica decisión`.  
**Contexto estructural:** motor de políticas open source y context-aware; integra mediante SDK Go, API Go de bajo nivel o REST API y separa decisiones de política del código del servicio.  
**Nivel seleccionado:** policy decision / governance layer.  
**Qué aporta a un agente:** decisiones de autorización/gobernanza reproducibles y externas al LLM, útiles para controlar tools, recursos, acciones y despliegues.

---
**COMPONENTES_DOCUMENTADOS = 135**  
**TOTAL_COMPONENTES_INVENTARIO_FRESH = 243**  
**DISCREPANCIA_DE_INVENTARIO = archivo 26 registró 245; inventario fresh actual declara 243. No se infiere la causa.**  
**SIGUIENTE_SECUENCIA_DOCUMENTAL = YAIWES 136–140**  
**SIGUIENTE FÍSICO = inventario fresh desde entrada 137; verificar fresh antes de escribir el próximo archivo.**