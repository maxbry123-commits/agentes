# Coda Workflow Persistencias

Destino autorizado para componentes externos que se convertirán en eslabones de persistencia del workflow YAIWES.

## Flujo de trabajo

1. Resolver y validar la URL canónica de cada repositorio fuente.
2. Descargar y extraer usando el motor existente en `main`:
   `➡️📂motores de descarga extracción copiado movimiento archivos agentes/📂Motor descarga de componentes y extracción de zip/`.
3. Publicar cada componente dentro de esta raíz, aislado en su propia carpeta.
4. Ejecutar auditoría defensiva por componente: dependencias, scripts de instalación, hooks, procesos, red, filesystem, shell, credenciales, ejecución dinámica y persistencia no autorizada.
5. No etiquetar código como malicioso sin evidencia. Todo hallazgo se registra con archivo, función, comportamiento, riesgo y prueba.
6. Sustituir únicamente la lógica peligrosa/no necesaria mediante cambios quirúrgicos y trazables.
7. Convertir el componente saneado en un eslabón simple del workflow persistente: `INPUT -> CLAIM -> EXECUTE -> CHECKPOINT -> VERIFY -> HANDOFF/NEXT`.
8. Mantener estado recuperable e idempotente; un reinicio no debe duplicar ni perder tareas.
9. Probar de forma aislada cada eslabón y luego probar la cadena completa.
10. Cerrar solo con evidencia de test y sin gaps críticos conocidos.

## Estructura prevista

- `componentes/` — repos descargados y saneados.
- `Fables enchufe universal/` — plugin/capa de cableado que aporte el usuario.
- `evidence/` — hallazgos y pruebas por componente.
- `tests/` — pruebas unitarias, de integración y de recuperación.

## Estado inicial

`PREPARED_FOR_INPUT`: raíz creada; faltan las URLs de los repositorios fuente y el plugin Fables.
