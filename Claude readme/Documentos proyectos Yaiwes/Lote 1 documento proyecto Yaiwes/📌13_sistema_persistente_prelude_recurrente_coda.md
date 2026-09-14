# Sistema principal del kernel: bucle persistente con cambio de algoritmo
**Instrucciones para programar, ubicar e integrar — Prelude → Bloque Recurrente → Coda y sus mecanismos alternativos**

## 0. Una aclaración honesta antes de empezar (para no repetir el error de Mythos)

El nombre exacto "Prelude → Bloque Recurrente → Coda" viene de un paper real (Geiping et al. 2025, arquitectura "Huginn"), pero ahí ocurre **dentro de los pesos de una red neuronal durante el entrenamiento** — no es algo que se "programe" como bucle de agente. Lo que sí es 100% real, programable hoy, y logra el mismo efecto que describes (repetir, evaluar, cambiar de estrategia si falla, seguir hasta lograrlo) es la familia de algoritmos de **búsqueda evolutiva guiada por LLM** — y ya existe una implementación open source completa de esto: **OpenEvolve** (`pip install openevolve`, MIT license, réplica abierta de AlphaEvolve/FunSearch de Google DeepMind). Vamos a construir tu sistema usando el patrón real, con el nombre Prelude/Recurrente/Coda como las 3 fases de tu propio diseño — es válido usarlo así, solo que ahora sabes de dónde viene cada pieza.

---

## 1. La forma genérica del ciclo (el patrón detrás de TODO lo que pediste)

Todo lo que describiste —el laberinto, el videojuego, la investigación en paralelo, el cambio de algoritmo— es la MISMA estructura de control, con distintas piezas conectadas:

```
PRELUDE (una vez):
    fijar objetivo y criterio de éxito medible
    fijar presupuesto máximo (tiempo, costo, iteraciones) — NUNCA infinito real
    elegir estrategia inicial del portafolio de algoritmos
    (opcional) abrir 5-20 investigaciones web en paralelo sobre el objetivo

BLOQUE RECURRENTE (se repite N veces, o hasta cumplir el objetivo):
    intento = ejecutar_estrategia_actual(tarea, contexto_investigado)
    resultado = evaluar(intento)              # evaluador SEPARADO, nunca el mismo que generó
    registrar_intento_y_resultado(intento, resultado)   # esto es lo que persiste y hace aprender

    si objetivo_cumplido(resultado):
        salir del bucle -> ir a CODA

    fallos_seguidos_con_esta_estrategia += 1
    si fallos_seguidos_con_esta_estrategia >= umbral:
        estrategia_actual = elegir_siguiente_estrategia(portafolio, historial_de_fallos)
        fallos_seguidos_con_esta_estrategia = 0

    si presupuesto_agotado():
        salir del bucle -> ir a CODA (con el mejor intento logrado, no con éxito)

CODA (una vez):
    sintetizar el mejor resultado logrado
    empaquetar evidencia (qué estrategias se probaron, cuál funcionó, por qué)
    persistir el aprendizaje para la próxima vez (esto alimenta el banco de estrategias)
```

**La diferencia real entre "no escalar, no parar" y un sistema irresponsable:** no es lo mismo "nunca rendirse ante el mismo tipo de fallo" que "correr literalmente para siempre". Un presupuesto muy alto (ej. 500 iteraciones o 2 horas de cómputo) cumple tu intención — el sistema no se rinde fácil — sin el riesgo real de un proceso que nunca termina y sigue consumiendo dinero y recursos sin que nadie se entere. Esto no es un capricho de seguridad — es la diferencia entre un sistema persistente y un sistema roto que nadie puede apagar.

---

## 2. Lista grande de componentes/librerías para construir cada parte del ciclo

### Para el BLOQUE RECURRENTE (ejecutar + evaluar + repetir)
1. **OpenEvolve** — el más directo: ya implementa generación de candidatos vía LLM, evaluación, base de datos de programas puntuados, y evolución hasta lograr el objetivo.
2. **Tenacity** — reintentos con backoff, para la capa más simple del bucle.
3. **`pybreaker`** — corta el bucle si una estrategia sigue fallando de forma idéntica (evita reintentos ciegos).
4. **DEAP** (Distributed Evolutionary Algorithms in Python) — si quieres algoritmos genéticos clásicos sin LLM, más barato que OpenEvolve para problemas numéricos.
5. **Optuna** — optimización de hiperparámetros con poda automática de intentos que no van a mejorar (útil como "evaluador" que decide seguir o cambiar).

### Para EL CAMBIO DE ALGORITMO (portafolio + selección)
6. **Multi-armed bandit** (UCB1, Thompson Sampling) — mantiene un marcador de qué estrategia ha funcionado más, y la usa para elegir la siguiente, aprendiendo con el tiempo (`river`, librería de ML online, tiene bandits listos).
7. Tu propio **catálogo de 105 algoritmos** (documento anterior) — es literalmente el portafolio de donde `elegir_siguiente_estrategia()` saca la próxima opción.
8. Tu **banco de `reasoning_modules/`** (Self-Discover) — mismo rol, para estrategias de razonamiento en vez de algoritmos de código.
9. **`scikit-optimize`** — optimización bayesiana como forma de elegir el siguiente intento de forma inteligente, no al azar.

### Para EL MODO "LABERINTO / VIDEOJUEGO" (exploración con decisiones cambiantes)
10. **Monte Carlo Tree Search (MCTS)** — el algoritmo real detrás de cómo las IAs de videojuegos (AlphaGo, AlphaZero) exploran árboles de decisión probando caminos, simulando resultados, y reforzando los que funcionan (`mcts` en PyPI, o implementación propia — es corta).
11. **Q-learning / SARSA** — si quieres que el agente aprenda una política de decisión con recompensas, como en un videojuego real.
12. **A\*** con heurística adaptativa — para laberintos/rutas concretas, ya en tu catálogo de 105.

### Para LA INVESTIGACIÓN EN PARALELO (5-20 goles de investigación web)
13. **GPT Researcher** — ya identificado, hace exactamente esto: divide un objetivo en subtemas y los investiga en paralelo.
14. **Stanford STORM** — genera varias "personas"/ángulos de investigación en paralelo antes de sintetizar.
15. Tu propio **Multi-API Fabric en modo SPLIT** — ya diseñado por Fables, es la pieza que reparte los 5-20 goles entre distintas APIs a la vez.
16. **`asyncio.gather`** — la primitiva de Python para correr N investigaciones realmente en paralelo sin librerías externas.

### Para APRENDER DEL FALLO (persistencia que hace crecer al sistema)
17. **ReasoningBank** (patrón de investigación 2025-2026) — extrae qué patrón de razonamiento funcionó o falló, y lo guarda reutilizable.
18. **Reflexion** — genera una autocrítica en texto tras cada fallo, y la inyecta en el siguiente intento como contexto adicional.
19. **Voyager** — cuando una estrategia nueva funciona, la convierte automáticamente en una "skill" reutilizable guardada.
20. **EverMemOS** — memoria auto-organizada para que el aprendizaje de tareas de hace semanas siga disponible hoy.

### Para EL EVALUADOR (nunca el mismo que generó el intento)
21. **Prometheus** (modelo juez open source) — evalúa con criterios objetivos, no con la opinión del mismo generador.
22. **DeepEval / Ragas** — frameworks de evaluación con métricas concretas, no juicios vagos.
23. **AlphaCodium** (patrón de tests) — para tareas de código: el "evaluador" son tests reales que pasan o fallan, lo más objetivo posible.

### Para EL PRESUPUESTO Y EL LÍMITE RESPONSABLE
24. **`asyncio.wait_for`** — timeout duro por intento.
25. **LiteLLM Router** con límite de presupuesto (`max_budget`) — corta por costo acumulado, no solo por tiempo.
26. Tu propio **`resource-governance/lease-management`** — ya diseñado, cumple este rol.

---

## 3. Mecanismos alternativos — el MISMO ciclo, programado de formas distintas

No hay una sola manera correcta de programar Prelude→Recurrente→Coda. Aquí tienes 7 variantes reales, cada una con su punto fuerte:

| Mecanismo | Cómo decide cambiar de estrategia | Mejor para |
|---|---|---|
| **OpenEvolve (evolutivo)** | Mantiene una población de soluciones, las cruza/muta, se queda con las mejores | Optimizar código/algoritmos concretos |
| **MCTS** | Explora ramas de decisión, simula el resultado antes de comprometerse, refuerza lo que ganó | Problemas tipo laberinto/juego con muchas decisiones secuenciales |
| **Reflexion** | Se autocritica en texto tras cada fallo y usa esa crítica como memoria para el siguiente intento | Tareas donde el fallo es más "conceptual" que numérico |
| **Multi-armed bandit** | Trackea estadísticamente qué estrategia gana más veces, sin autocrítica en texto | Cuando tienes muchas estrategias y pocas oportunidades de probarlas todas |
| **Iterated Local Search / Simulated Annealing con reinicio** | Reinicia desde un punto distinto cuando se atasca en un óptimo local | Problemas de optimización numérica pura |
| **Self-Debugging (estilo AlphaCodium)** | El fallo es un test que no pasa; cambia el código hasta que el test pase | Tareas de programación específicamente |
| **Voyager (currículo de skills)** | Cuando algo funciona, se guarda como habilidad nueva; cuando falla, se intenta la siguiente habilidad de la biblioteca | Tareas repetitivas donde quieres que el sistema acumule capacidad con el tiempo |

**Recomendación práctica:** no elijas solo uno — regístralos todos como estrategias distintas dentro del mismo portafolio (punto 2 de la lista de componentes). El sistema de cambio de algoritmo (`elegir_siguiente_estrategia`) puede literalmente alternar entre estos 7 mecanismos, no solo entre variantes de uno solo.

---

## 4. Cómo programarlo e integrarlo — paso a paso, con ubicación exacta

### Paso 1 — Dónde vive (nueva carpeta, no toca nada existente)
```
reasoning-kernel/
└── persistent_solver/          ← NUEVO
    ├── prelude.py               # fija objetivo, presupuesto, abre investigación paralela
    ├── recurrent_block.py       # el bucle: ejecutar -> evaluar -> registrar -> decidir seguir/cambiar
    ├── coda.py                  # sintetiza, empaqueta evidencia, persiste aprendizaje
    ├── portafolio_estrategias/  # registro de las 7 variantes + tu catálogo de 105 + reasoning_modules
    └── evaluador.py             # SIEMPRE una instancia/lógica distinta a la que generó el intento
```

### Paso 2 — Cómo se activa como "el sistema principal"
En tu `expert_panel_router.py` ya existente, agrega una condición: si la tarea entrante tiene alta ambigüedad o el `classifier-scheduler` le da un score EXTREME (tu propia escala LOW/MEDIUM/HIGH/EXTREME de Mythos), en vez de rutear a un solo workflow o a un solo módulo de razonamiento, rutea a `persistent_solver.prelude.iniciar(tarea)`. Así se convierte en la ruta principal para tareas difíciles, sin reemplazar los caminos rápidos para tareas simples (Nivel A del protocolo de cierre sigue intacto para tareas fáciles).

### Paso 3 — Cómo conecta con los algoritmos deterministas que ya discutimos
`recurrent_block.py` no contiene lógica de ningún algoritmo — solo llama a lo que esté registrado en `portafolio_estrategias/`, exactamente igual que `decision_on_demand.py` llama a los módulos de `reasoning_modules/`. Cada entrada del catálogo de 105 (documento anterior) se registra aquí con la misma ficha del Enchufe Universal, solo que ahora con un campo adicional:
```yaml
compatible_con_persistent_solver: true
tasa_exito_historica: 0.0   # se actualiza automáticamente tras cada uso — esto es lo que aprende
```

### Paso 4 — Cómo sigue creciendo en esta única dirección
Cada vez que el bucle recurrente prueba una estrategia nueva y funciona, `coda.py` la registra en el portafolio con su tasa de éxito. La próxima vez que el sistema entre en el bucle, `elegir_siguiente_estrategia()` ya tiene una opción más entre las cuales elegir, priorizando las que históricamente ganan más — sin que nadie tenga que programar esa preferencia a mano. Este es tu "crecer en una única dirección": el punto de entrada (`persistent_solver/`) no cambia nunca de forma; lo único que crece es el contenido de `portafolio_estrategias/`, igual que ha crecido `reasoning_modules/` y tu catálogo de 105.

---

## Resumen

El ciclo Prelude→Recurrente→Coda que describes ya existe como algoritmo real (OpenEvolve/FunSearch, MCTS, Reflexion, y 5 variantes más), no hay que inventarlo — hay que ensamblarlo. Vive en una carpeta nueva (`persistent_solver/`) que nunca toca el resto del kernel, se activa desde tu router existente cuando una tarea es difícil, usa como "portafolio de estrategias" exactamente los catálogos que ya construimos (105 algoritmos + reasoning_modules), y aprende solo porque cada intento —éxito o fallo— se registra y alimenta la elección de la próxima estrategia. El único ajuste de diseño que te recomiendo frente a tu idea original: cambia "nunca parar" por "un presupuesto muy alto" — logra la misma persistencia sin el riesgo real de un proceso que nadie puede detener.
