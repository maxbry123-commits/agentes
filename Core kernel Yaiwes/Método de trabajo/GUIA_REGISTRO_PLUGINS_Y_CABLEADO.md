# GUÍA DE MÉTODO DE TRABAJO — REGISTRO DE PLUGINS Y CABLEADO

**Aplicación:** IA, agentes, código y documentos del proyecto.
**Regla de verdad:** GitHub = truth. FAIL-CLOSED. No inventar implementaciones ni conexiones.

## 1. Regla principal

Todo archivo nuevo que deba ser reutilizable/conectable debe nacer con su mecanismo de plugin preparado. El archivo se valida y registra; después queda estable para futuras conexiones.

**Una conexión futura NO se implementa editando el archivo registrado.** Se realiza mediante su plugin, contrato, extension point, adapter o cable externo.

```text
CREAR
  ↓
PREPARAR PLUGIN
  ↓
VALIDAR
  ↓
REGISTRAR
  ↓
DEJAR ESTABLE
  ↓
CONECTAR POR PLUGIN / CONTRATO / CABLE
```

## 2. No confundir componente con conexión

El componente contiene su funcionalidad propia.
La conexión es una relación externa.

```text
archivo A ── plugin A ── cable/contrato ── archivo B
```

Para añadir una conexión no se modifica A ni B solo para insertar la conexión.

## 3. Método REUSE > PATCH > ADAPT > GENERATE

Antes de crear:
1. Buscar código/documentación existente.
2. Identificar source y commit.
3. Reutilizar cuando sea compatible.
4. Parchear solo lo necesario.
5. Adaptar mediante una interfaz externa cuando las interfaces difieran.
6. Generar solo cuando no exista una fuente reutilizable.

## 4. Plugin preparado desde la creación

Cuando un archivo sea un componente reutilizable, su plugin debe dejar identificados, cuando existan:

- plugin_id;
- tipo: code/document/plugin/adapter;
- source;
- source_commit;
- versión;
- entrypoint o referencia documental;
- contrato;
- extension point;
- inputs/outputs;
- dependencias;
- capabilities;
- tests;
- evidencia;
- estado.

El registro puede evolucionar. El archivo componente no se modifica únicamente para añadir conexiones.

## 5. Cambios posteriores

Si una nueva conexión no es compatible:

```text
NO editar componente registrado
        ↓
crear/usar adapter o cable
        ↓
validar contrato
        ↓
registrar evidencia
```

Si el componente necesita realmente una modificación funcional, se crea una nueva versión mediante Refactoria; no se modifica silenciosamente la versión registrada.

## 6. Cableado

Cada cable debe poder demostrar:

- origen;
- destino;
- contrato;
- versión;
- adapter, si existe;
- entradas/salidas;
- tests;
- evidencia.

La documentación por sí sola no demuestra que un cable exista: debe existir soporte en el código/configuración real.

## 7. Documentos y código

Los documentos pueden registrarse como componentes documentales, pero no se tratan como código ejecutable. Código y documentos conservan sus propios contratos y consumidores.

## 8. Arquitectura

La referencia **Microkernel Architecture / Plugin Architecture** describe un patrón reconocido de extensibilidad, pero no obliga a que todos los componentes del repositorio sean extensiones de una estructura concreta. Cada repositorio conserva su arquitectura real.

## 9. Regla LEGO

No duplicar capacidades que ya tengan autoridad única. En particular, respetar las autoridades existentes para `goal_lock`, `cognitive_loop` y `evidence_packet`.

## 10. OpenClaw

Para esta fase, OpenClaw es el componente externo a materializar y cablear con Wordflow. Hermes queda fuera de esta resolución.

El flujo es:

```text
SOURCE REAL
  ↓
REFÁCTORÍA
  ↓
VALIDACIÓN
  ↓
PLUGIN / REGISTRO
  ↓
COMPONENTE ESTABLE
  ↓
CONTRATO / EXTENSION POINT
  ↓
CABLE / ADAPTER
  ↓
WORDflow
  ↓
TESTS + EVIDENCIA
```

No se debe inventar el body ni modificar el componente materializado únicamente para conectarlo.

## 11. FAIL-CLOSED

Sin source real → OPEN/BLOCKED.
Sin contrato → OPEN/BLOCKED.
Sin cable verificable → no integración.
Sin tests requeridos → no PASS.
Sin evidencia → no PASS.

## 12. Regla para IA/agentes

Antes de crear o modificar:

1. Buscar.
2. Identificar source.
3. Identificar si existe plugin.
4. Preparar plugin si el nuevo archivo debe ser reutilizable/conectable.
5. Validar.
6. Registrar.
7. Dejar estable el componente.
8. Conectar posteriormente por plugin/contrato/cable, sin editar el componente para realizar la conexión.
9. Ejecutar pruebas.
10. Registrar evidencia y checkpoint.

**Norma central:** generar/preparar → validar → registrar → dejar estable → conectar externamente.
