# Catálogo de 100+ componentes algorítmicos deterministas para el kernel

Nota importante antes de la lista: estos son **algoritmos reales, con matemática o lógica formal detrás** — no texto para un LLM. Cada uno corre solo, sin modelo de lenguaje, y la mayoría ya tiene implementación en librerías de Python probadas (se indica cuál, para no escribirlos desde cero). Se agrupan en tus categorías + 2 que propongo (Verificación, Optimización) porque tu kernel ya las necesita en varios puntos del diseño de Fables.

---

## PRELUDE — inicialización (10)
1. **Topological sort** — ordena tareas por dependencias antes de ejecutar (`networkx.topological_sort`)
2. **Dependency injection container** — arma el contexto inicial sin acoplar componentes (`dependency-injector`)
3. **Configuration cascade** — combina config por capas: default → entorno → usuario (`dynaconf`)
4. **Feature flag evaluation** — activa/desactiva capacidades antes de arrancar un flujo (`flagsmith`, `unleash`)
5. **JSON Schema validation gate** — valida el input antes de que toque cualquier lógica (`jsonschema`)
6. **Idempotency key generation** — hash del input para deduplicar reintentos (`hashlib.sha256`)
7. **Cache warm-up preload** — precarga lo que se sabe que se va a necesitar
8. **Circuit breaker initial state check** — verifica el estado del breaker antes de aceptar tarea (`pybreaker`)
9. **Health check chain** — sondea dependencias externas antes de aceptar la tarea
10. **Context window budgeting** — calcula cuánto contexto cabe antes de empezar

## INVESTIGACIÓN — búsqueda (12)
11. **Breadth-First Search (BFS)** — explora el espacio de soluciones nivel por nivel
12. **Depth-First Search (DFS) con poda** — backtracking clásico
13. **A\* search** — búsqueda informada con heurística admisible
14. **Beam search** — mantiene solo los K mejores caminos en cada paso
15. **Monte Carlo Tree Search (MCTS)** — exploración probabilística de árboles de decisión (usado en AlphaGo)
16. **Iterative deepening DFS** — combina lo mejor de BFS y DFS
17. **Bidirectional search** — busca desde el inicio y la meta a la vez
18. **Random-restart hill climbing** — escapa mínimos locales reintentando desde puntos nuevos
19. **Simulated annealing** — acepta soluciones peores temporalmente para escapar óptimos locales
20. **BM25 ranking** — el algoritmo real detrás de "buscar en documentos" (`rank_bm25`)
21. **Reciprocal Rank Fusion (RRF)** — combina resultados de varios buscadores en un solo ranking
22. **Focused/polite web crawling** — BFS respetando `robots.txt` y límites de tasa (`scrapy`)

## ANÁLISIS (12)
23. **Principal Component Analysis (PCA)** — reduce dimensionalidad de datos (`scikit-learn`)
24. **K-means clustering** — agrupa datos similares
25. **DBSCAN** — clustering por densidad, detecta outliers sin definir K de antemano
26. **Z-score / IQR anomaly detection** — detecta valores atípicos con estadística simple
27. **5 Whys (causa raíz)** — algoritmo determinista de análisis de causa raíz
28. **Diagrama de Ishikawa (espina de pescado)** — estructura las causas por categoría
29. **Matriz SWOT generativa** — clasifica factores en 4 cuadrantes de forma determinista
30. **Sentiment scoring basado en léxico** — polaridad sin LLM (`VADER`)
31. **Análisis de ciclos en grafo de dependencias** — detecta bloqueos circulares (`networkx`)
32. **Pruebas de hipótesis estadística** (t-test, chi-cuadrado) — validación numérica de una afirmación
33. **Descomposición de series de tiempo** — separa tendencia/estacionalidad/ruido (`statsmodels`)
34. **Análisis de sensibilidad** — qué variable de entrada afecta más el resultado

## RAZONAMIENTO — lógica formal (10)
35. **Forward chaining** — motor de reglas: de hechos a conclusiones
36. **Backward chaining** — de la meta hacia atrás, a qué hechos se necesitan
37. **Constraint Satisfaction Problem (CSP) solver** — resuelve problemas con restricciones (`python-constraint`)
38. **SAT solver** — satisfacibilidad booleana (`pysat`)
39. **Resolution theorem proving** — demostración lógica formal
40. **Fuzzy logic inference** — razonamiento con grados de verdad, no solo verdadero/falso (`scikit-fuzzy`)
41. **Finite State Machine / Statechart** — el mismo patrón que ya usas en `StateAuthority`
42. **Rete algorithm** — motor de reglas eficiente para sistemas expertos con muchas reglas
43. **Petri nets** — modela procesos concurrentes con estados y transiciones
44. **Analogical Structure Mapping** — razonamiento por analogía formal, no metafórico

## CONCLUSIONES — síntesis (10)
45. **Majority voting** — la conclusión más simple: gana lo que más se repite
46. **Weighted voting** — pondera cada voto según la confianza de su fuente
47. **Borda count** — ranking por consenso entre varias listas ordenadas
48. **Bayesian belief update** — actualiza una probabilidad con nueva evidencia
49. **Dempster-Shafer combination rule** — combina evidencia con incertidumbre explícita
50. **MapReduce pattern** — combina resultados parciales en una conclusión única
51. **TextRank (resumen extractivo)** — resume sin LLM, por grafo de relevancia (`sumy`)
52. **Consensus clustering** — combina varios agrupamientos distintos en uno solo
53. **Delphi method (estructura)** — consenso iterativo entre "expertos" (puede ser entre módulos)

## DECISIONES DIFÍCILES — bajo incertidumbre (12)
54. **Weighted Sum Model (MCDA)** — decide entre opciones con varios criterios ponderados
55. **Analytic Hierarchy Process (AHP)** — pondera criterios de forma jerárquica y consistente
56. **TOPSIS** — rankea opciones por distancia a la solución ideal
57. **Minimax** — decisión que minimiza la peor pérdida posible
58. **Maximin** — decisión que maximiza el peor resultado posible (más conservador)
59. **Expected value / expected utility** — decide por valor esperado bajo probabilidades conocidas
60. **Árbol de decisión con valor monetario esperado**
61. **Minimax regret** — minimiza el "me hubiera arrepentido de no elegir X"
62. **Frontera de Pareto** — identifica soluciones no dominadas por ninguna otra
63. **Equilibrio de Nash** — decisiones óptimas cuando hay más de un agente compitiendo
64. **Kelly criterion** — tamaño óptimo de una apuesta/inversión bajo incertidumbre
65. **Matriz de costo-beneficio**

## DESCUBRIMIENTOS — exploración (10)
66. **Apriori (reglas de asociación)** — descubre patrones "si A entonces B" en datos
67. **FP-Growth** — minería de patrones frecuentes, más rápido que Apriori
68. **Algoritmo genético** — explora soluciones por selección/mutación/cruce
69. **Optimización bayesiana** — descubre el óptimo probando pocas veces (`scikit-optimize`)
70. **Multi-armed bandit (UCB, Thompson sampling)** — equilibrio exploración/explotación
71. **Active learning** — elige qué preguntar para aprender más rápido con menos datos
72. **Curiosity-driven exploration** — bono por explorar lo desconocido, no solo lo óptimo
73. **PC algorithm (descubrimiento causal)** — infiere causalidad a partir de datos observacionales
74. **Latent Dirichlet Allocation (LDA)** — descubre temas ocultos en un conjunto de textos
75. **Novelty detection** — distingue "esto ya lo vi" de "esto es genuinamente nuevo"

## CODA — cierre (8)
76. **Verificación de checksum/hash** antes de declarar cerrado
77. **Two-phase commit** — cierre transaccional seguro entre varios sistemas
78. **Saga pattern** — compensación automática si algo falla al cerrar
79. **Graceful shutdown sequence** — cierre ordenado, sin perder trabajo en curso
80. **Chequeo de consistencia final** — compara estado esperado vs. estado real
81. **Generación de reporte final** desde plantilla, compilando toda la evidencia
82. **Firma/atestación digital al cerrar** (GPG, ya lo tienes en tu ficha)
83. **Creación de punto de rollback final** antes de declarar éxito

## PERSISTENCIA (10)
84. **Write-Ahead Logging (WAL)** — persiste antes de aplicar el cambio, nunca al revés
85. **Event sourcing** — guarda todos los eventos, no solo el estado final (recomendado para tu ledger)
86. **CQRS** — separa la ruta de escritura de la de lectura
87. **Snapshotting periódico** — ya lo tienes diseñado (`corazon/snapshot.py`)
88. **Merkle tree** — verifica integridad del historial completo con una sola raíz (`pymerkle`)
89. **LSM-tree** — persistencia eficiente de escritura a gran volumen
90. **Content-addressable storage** — como Git: deduplica por hash de contenido
91. **Vector clocks / Lamport timestamps** — orden causal entre eventos distribuidos
92. **CRDT (Conflict-free Replicated Data Type)** — fusiona estado sin conflictos entre réplicas paralelas
93. **Write-behind cache** — persistencia diferida en cola, sin bloquear la ejecución

## VERIFICACIÓN — la que propongo agregar (6)
94. **Property-based testing** — verifica invariantes con casos generados automáticamente (`Hypothesis`)
95. **Model checking** — verifica que un sistema cumple una propiedad en TODOS los estados posibles
96. **Contract testing** — verifica que dos servicios cumplen el contrato que declaran (`Pact`, `Schemathesis`)
97. **Fuzzing** — genera entradas aleatorias/extremas para encontrar fallos antes que el usuario
98. **Differential testing** — compara la salida de dos implementaciones del mismo problema
99. **Mutation testing** — verifica que tus propios tests detectan errores introducidos a propósito (`mutmut`)

## OPTIMIZACIÓN — la otra que propongo (6, para llegar a 105)
100. **Programación lineal / Simplex** — optimiza con restricciones lineales (`scipy.optimize.linprog`)
101. **Programación dinámica (memoization)** — evita recomputar subproblemas repetidos
102. **Branch and bound** — optimización combinatoria con poda de ramas
103. **Nelder-Mead (optimización sin gradiente)** — para funciones sin derivada conocida
104. **Constraint propagation (AC-3)** — reduce el espacio de búsqueda antes de resolver un CSP
105. **Programación entera mixta (MIP)** — para decisiones con variables discretas (`PuLP`, `OR-Tools`)

---

## Cómo se conecta esto con lo que ya construimos hoy

Cada uno de estos 105 es candidato a convertirse en un archivo dentro de `reasoning_kernel/decision_on_demand/reasoning_modules/` — **pero como capacidad determinista, no como texto para el LLM.** La diferencia con los módulos de Self-Discover que hicimos antes: esos eran instrucciones en lenguaje natural para el LLM; estos son funciones de Python reales que `expert_panel_router.py` también podría seleccionar, solo que en vez de llamar a `llm_caller()`, `decision_on_demand.py` llamaría directamente a la función del algoritmo — sin gastar ni un token.

**La misma ficha del Enchufe Universal sirve para ambos** — la diferencia está en un solo campo: `ejecucion.kind: code` (para estos 105) en vez de `ejecucion.kind: llm` (para los de razonamiento tipo Self-Discover). El resto del flujo de calificación, registro y cableado que ya tienes es idéntico.
