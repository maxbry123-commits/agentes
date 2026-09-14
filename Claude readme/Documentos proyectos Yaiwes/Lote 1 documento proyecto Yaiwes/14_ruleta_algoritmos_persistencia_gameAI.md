# Rotación de algoritmos Y sistemas de persistencia — la "ruleta" del kernel
**Investigación de mecanismos de selección + sistemas de persistencia alternativos + IA de videojuegos aplicable al agente**

## 0. El hallazgo clave: el "AI Director" de Left 4 Dead

Valve describió su propio sistema así: *"un conjunto de algoritmos extremadamente simples, cada uno testeable por separado — no una caja negra opaca."* Mide una señal de **estrés/desempeño** del jugador, la compara contra una curva objetivo, y ajusta qué "capa" de dificultad activar. Esto es, literalmente, un controlador de retroalimentación (como un termostato) decidiendo cuál de varios sistemas usar — exactamente lo que pediste para tu kernel, solo que en vez de "estrés del jugador" mide "qué tan bien va resolviendo la tarea el agente".

---

## 1. Los 3 mecanismos reales para la "ruleta" (cómo decide rotar)

No hay que inventar el mecanismo de rotación — ya existen 3, cada uno con una lógica distinta:

| Mecanismo | Cómo rota | Analogía |
|---|---|---|
| **Round-robin** | Sigue un orden fijo, uno tras otro, sin importar el desempeño | El reloj digital que mencionaste — cambia por turno |
| **Roulette wheel selection** (algoritmo real de genética, ya con ese nombre exacto) | La probabilidad de elegir cada sistema es proporcional a qué tan bien le ha ido antes | Una ruleta de verdad, pero con casillas más grandes para lo que funciona |
| **Epsilon-greedy / UCB (multi-armed bandit)** | Casi siempre usa el que mejor funciona, pero de vez en cuando prueba otro al azar para seguir aprendiendo | Ya lo vimos en el documento anterior — es el más "inteligente" de los 3 |

**Recomendación:** empieza con *roulette wheel selection* — es el punto medio exacto entre "siempre lo mismo" (round-robin) y "demasiado calculado" (bandit), y es el que más se parece a lo que describiste.

---

## 2. Doce sistemas de persistencia distintos para rotar (no solo algoritmos)

Cada uno tiene una garantía distinta — cuando uno falla o no sirve para el caso, rotas al siguiente, no reintentas el mismo:

1. **Relacional/ACID** (SQLite, PostgreSQL) — consistencia estricta, bueno para datos estructurados críticos.
2. **Documento** (MongoDB) — esquema flexible, bueno cuando la forma de los datos cambia entre tareas.
3. **Clave-valor** (Redis) — el más rápido, bueno para estado temporal de corta duración.
4. **Columnar/wide-column** (Cassandra, ScyllaDB) — pensado para volúmenes enormes, útil si el kernel escala mucho.
5. **Grafo** (Neo4j, o tu ya elegido Graphiti) — cuando lo importante son las relaciones, no los datos aislados.
6. **Series de tiempo** (InfluxDB, TimescaleDB) — para el historial de intentos/fallos ordenado cronológicamente.
7. **Objetos/blobs** (MinIO — S3 compatible y open source) — para guardar evidencia grande (reportes, capturas).
8. **Log distribuido append-only** (Kafka, o su alternativa más ligera Redpanda) — para eventos que múltiples partes del kernel necesitan leer.
9. **Base de datos vectorial** (Qdrant, Milvus, Weaviate) — memoria semántica, para "esto se parece a algo que ya viví".
10. **Almacén de consenso distribuido** (etcd, basado en Raft) — cuando necesitas que varias réplicas del kernel se pongan de acuerdo sobre el estado.
11. **Ledger inmutable tipo blockchain** (encadenado por hash, ya lo tienes con Merkle tree) — cuando lo que importa es que nadie pueda alterar el historial después.
12. **Híbrido en memoria + snapshot periódico** (Redis en modo AOF, o SQLite en modo WAL) — el balance entre velocidad y no perder nada si se cae el proceso.

---

## 3. Componentes open source de IA de videojuegos avanzados — y cómo se vuelven mecanismos del agente

| Sistema de videojuego | Qué hace en el juego | Librería open source | Cómo se vuelve un mecanismo de tu agente |
|---|---|---|---|
| **Behavior Trees** | Decide comportamientos complejos combinando nodos simples (secuencia, selector, condición) | `py_trees` (Python, usado también en robótica ROS) | Reemplaza un `if/else` gigante por un árbol de decisión componible y visualizable — ideal para tu `expert-panel-router` |
| **GOAP (Goal-Oriented Action Planning)** | El NPC no sigue un guion — planifica qué acciones lo llevan del estado actual al objetivo, y REPLANIFICA si algo se lo impide | Implementaciones de referencia en Python/C# (buscar "GOAP planner python github") | Es literalmente tu "no se rinde, cambia de plan" — cuando una acción falla, GOAP busca automáticamente otra secuencia de acciones hacia el mismo objetivo |
| **Utility AI** | En vez de reglas fijas, cada acción posible recibe un puntaje (utilidad) según el contexto, y gana la de mayor puntaje | Se implementa como funciones de puntuación propias; referencia de diseño ampliamente documentada | Tu "elegir la siguiente estrategia" puede ser una función de utilidad en vez de reglas rígidas — más flexible que un `if` |
| **HTN (Hierarchical Task Network) Planning** | Descompone una meta grande en subtareas, recursivamente, hasta llegar a acciones concretas | `pyhop` / `GTPyhop` (Universidad de Maryland, Python, código real y documentado) | Tu Prelude puede usar HTN para descomponer el objetivo en subtareas antes de entrar al bloque recurrente |
| **AI Director (Left 4 Dead)** | Mide una señal de "estrés/desempeño" en tiempo real y ajusta qué tan intensa es la siguiente etapa | No hay paquete único — se construye con un controlador PID simple: `simple-pid` (librería real de Python) | Este es tu "reloj/ruleta" en la práctica: mide qué tan bien va el bloque recurrente (score de confianza, tiempo tomado, errores) y decide CUÁNDO rotar, no solo tras contar fallos |
| **Blackboard architecture** | Varios sistemas de IA distintos leen y escriben en una misma pizarra compartida de conocimiento, sin hablarse directamente entre sí | Incluido dentro de `py_trees` (`py_trees.blackboard`) | Es la forma correcta de que `persistent_solver`, `expert_panel_router` y `resource-governance` compartan estado sin acoplarse directamente unos a otros |
| **Influence maps** | Mapa espacial de "qué tan peligrosa/útil" es cada zona, usado en juegos de estrategia para decisiones tácticas | Se implementa como una grilla/matriz propia (no hay librería estándar única) | Útil si tu agente maneja muchas tareas simultáneas: un mapa de "qué áreas del sistema están bajo más carga" para decidir dónde enfocar recursos |
| **Flocking/Boids** | Coordina muchos agentes simples con 3 reglas (separación, alineación, cohesión) para producir comportamiento de grupo | Implementación corta con NumPy, o `pynboids` | Relevante si tu pool de agentes en paralelo (Fleet Manager) necesita coordinarse sin un supervisor central rígido |

---

## 4. Cómo se integra todo — ubicación y programación

### Estructura (extiende `persistent_solver/` del documento anterior, no crea nada paralelo)

```
reasoning-kernel/
└── persistent_solver/
    ├── prelude.py
    ├── recurrent_block.py
    ├── coda.py
    ├── director.py                    ← NUEVO: mide la señal de "estrés" (score, tiempo, fallos)
    ├── selector_ruleta.py             ← NUEVO: round-robin / roulette wheel / bandit
    ├── portafolio_algoritmos/         ← ya existía: 105 algoritmos + reasoning_modules + Behavior Trees/GOAP/HTN/Utility AI
    └── portafolio_persistencia/       ← NUEVO: los 12 sistemas de persistencia, cada uno con su ficha
```

### Cómo programarlo — flujo con las dos ruedas girando

```
1. director.py mide la señal tras cada intento del bloque recurrente:
   señal = f(score_confianza, tiempo_tomado, num_fallos_seguidos)

2. Si la señal indica "esto no está funcionando" (umbral, igual que L4D compara
   contra su curva de tensión objetivo):
     selector_ruleta.girar("algoritmos")     -> nueva entrada de portafolio_algoritmos/
     selector_ruleta.girar("persistencia")   -> nueva entrada de portafolio_persistencia/

3. Las dos ruedas pueden girar JUNTAS (un combo algoritmo+persistencia que ya
   sabes que funciona bien en conjunto) o SEPARADAS (cambias solo el algoritmo
   y mantienes la misma base de datos, o viceversa) — se configura en la ficha
   de cada combinación con un campo "acoplado: true/false".

4. coda.py registra qué combinación (algoritmo, persistencia) tuvo éxito, y
   selector_ruleta.py sube su probabilidad para la próxima vez que la ruleta
   gire (esto es lo que hace que la ruleta "aprenda" en vez de ser puro azar).
```

### Ejemplo de una secuencia real de rotación (para que veas el patrón completo)

| Intento | Algoritmo activo | Persistencia activa | Resultado | ¿Rota? |
|---|---|---|---|---|
| 1 | Behavior Tree (regla simple) | SQLite (relacional) | Falla | Sí — señal de estrés alta |
| 2 | GOAP (replanifica acciones) | Redis (clave-valor, más rápido) | Falla parcial | Sí |
| 3 | MCTS (explora árbol de decisiones) | Grafo (Graphiti) | Éxito | No — se queda, y sube su probabilidad en la ruleta |

La próxima vez que llegue una tarea parecida, la ruleta ya sabe (por `roulette wheel selection`) que la combinación MCTS+Grafo tiene más probabilidad de funcionar, y empieza probando eso primero — sin que nadie lo haya programado a mano.

---

## Resumen

No necesitas inventar el mecanismo de "ruleta que va cambiando" — ya existe con 3 nombres reales (round-robin, roulette wheel selection, multi-armed bandit), y el "cuándo rotar" ya lo resolvió Valve hace 15 años con el AI Director de Left 4 Dead (una señal de estrés + un controlador simple tipo PID). Se integran en una sola carpeta nueva (`persistent_solver/`), con dos ruedas independientes girando —una de algoritmos (incluyendo Behavior Trees, GOAP, HTN, Utility AI de los videojuegos) y otra de sistemas de persistencia (12 tipos distintos)— coordinadas por un `director.py` que decide cuándo girar, no un contador fijo de fallos. Cada combinación que funciona sube su probabilidad para la próxima vez — así es como esto, además de rotar, aprende con el tiempo.
