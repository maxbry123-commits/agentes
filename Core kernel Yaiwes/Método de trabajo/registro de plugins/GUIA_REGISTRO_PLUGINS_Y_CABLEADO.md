# GUÍA DE MÉTODO DE TRABAJO — REGISTRO DE PLUGINS Y CABLEADO

## Propósito

Norma operativa para IA y agentes que crean, reutilizan, registran y conectan código o documentos en este repositorio.

## Regla principal

Todo componente que deba admitir conexiones futuras debe dejar su mecanismo de plugin preparado al crearse y validarse.

```text
SOURCE → REUSE/PATCH/ADAPT/GENERATE → VALIDATE → REGISTER → FREEZE → CONNECT BY PLUGIN
```

Una vez registrado y validado, el archivo/componente queda estable. **No se edita posteriormente el archivo original solo para añadir una conexión.**

Las conexiones futuras se realizan mediante el plugin, contrato, extension point, adapter o cable correspondiente.

## No significa que todo sea una extensión

La arquitectura real de cada repositorio manda. Microkernel/Plugin Architecture es una referencia arquitectónica formal, no una orden para convertir todos los componentes en extensiones de un único núcleo.

## Registro

Cada plugin debe conservar trazabilidad de:

- `plugin_id`
- `version`
- `type`
- `entrypoint` o documento origen
- `source` y commit cuando exista
- contrato
- capacidades
- entradas/salidas
- dependencias
- punto de extensión
- cableado
- tests
- evidencia
- estado
- `immutable_component: true`

## Código y documentos

Código y documentos pueden registrarse, pero no se confunden: un documento registrado no se convierte en código ejecutable.

## Cableado

```text
COMPONENTE → PLUGIN/CONTRACT → ADAPTER → CABLE → DESTINO
```

El cable debe identificar origen, destino, contrato, versión, entradas, salidas, seguridad, tests y evidencia.

## Modificación futura

Si una nueva conexión necesita cambiar el comportamiento del componente:

1. no editar el componente registrado;
2. reutilizar su plugin/contrato;
3. crear un adapter o cable nuevo si hace falta;
4. si el contrato debe cambiar, crear una nueva versión del componente;
5. conservar la versión anterior como evidencia.

## Seguridad

- FAIL-CLOSED.
- Sin secretos en código, manifests o evidence.
- UNKNOWN/sin evidencia no es PASS.
- No inventar APIs, rutas, stages, engines ni cuerpos de agentes.

## Reutilización

`REUSE > PATCH > ADAPT > GENERATE`.

Antes de crear algo nuevo se busca primero una implementación real reutilizable.

## Refactoria

Para cambios derivados de código existente:

```text
source/ → new/ → diff → tests → contract check → integration
```

La copia `source/` permanece como evidencia. El hot path no se modifica sin paridad de tests.

## Regla LEGO

No duplicar capacidades que ya tienen autoridad única. Registrar y conectar la implementación existente.

## PASS

Un componente/conexión solo se declara PASS cuando existe evidencia real del código, contrato, registro, cableado y validación requerida.

**Generar una vez. Registrar una vez. Dejar estable. Conectar por plugin.**
