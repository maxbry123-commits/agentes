# Capa de persistencia OpenMythos — Wordflow LOOP Yaiwes

Fuente investigada: `kyegomez/OpenMythos` (`README.md`, `open_mythos/main.py`).

Mecanismo fuente confirmado: `Input -> Prelude (una vez) -> Recurrent Block (T loops, mismos pesos, reinyección del input) -> Coda (una vez) -> Output`.

Adaptación Wordflow: no se copia el Transformer/MoE. Se conserva el mecanismo estructural para persistencia de tareas: Prelude congela el estado/contrato; el bloque recurrente reinyecta el ancla en cada intento; Coda consolida la salida. El límite solicitado es 20 iteraciones.

Esta capa es determinista. No llama LLM. La LLM pertenece únicamente a capas explícitas de decisión/razonamiento.

Plugin: `PLUGIN_CONTRACT` expone `wordflow.persistence.open_mythos_loop` para cableado posterior mediante el Enchufe Universal.

Fuente: https://github.com/kyegomez/OpenMythos
