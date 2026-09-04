# PIPELINE 04 — Arquitectura Dual: 3 Modos de Montaje

**Fecha:** 2026-08-09  
**Estado:** ENCABEZADO ARQUITECTÓNICO OFICIAL  
**Autoridad:** Director

---

## Principio central

El sistema (Wordflow + Capa de Control) debe poder funcionar de **tres maneras distintas** sin romper el núcleo determinista.

```
                    ┌─────────────────────────────────────┐
                    │         NÚCLEO DETERMINISTA         │
                    │  (Sheriff · Contratos · MYTHOS ·     │
                    │   Recovery · Witness · Fichas)       │
                    └─────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
   FUNCIÓN 1                   FUNCIÓN 2                   FUNCIÓN 3
   Kernel de OpenClaw          Capa de Control             Extensión Kernel
```

---

## FUNCIÓN 1 — Kernel de OpenClaw (sustitución)

- Se hace **poda y modificación** del kernel de OpenClaw.
- Se **sustituye el núcleo** de OpenClaw por nuestro núcleo determinista.
- OpenClaw se convierte en la base para crear agentes **TEAM / YAIWES**.
- Resultado: OpenClaw deja de ser probabilístico en el núcleo y pasa a ser determinista + extensible.

**Característica clave:** modifica la estructura interna de OpenClaw.

---

## FUNCIÓN 2 — Capa de Control externa (sin modificar el host)

- Cualquier agente u orquestador se conecta a Wordflow **sin modificar su estructura**.
- Wordflow actúa como **capa de control** externa.
- El agente/orquestador host sigue intacto.
- Wordflow decide (Sheriff, contratos, goals, recovery) y el host solo ejecuta lo autorizado.

**Característica clave:** zero-invasive. El host no se toca.

---

## FUNCIÓN 3 — Extensión Kernel (montable vía ABI)

- Todo Wordflow se monta como **extensión de kernel** de cualquier agente u orquestador.
- Usa el ABI (ExtensionABI + EvidenceOutput).
- El host llama a `attach_to_wordflow_extension` / `load` / `execute`.
- Wordflow aporta capacidades, contratos y evidencia sin reemplazar el kernel del host.

**Característica clave:** plug-in. Se monta y se desmonta.

---

## Resumen de decisión de montaje

| Modo       | ¿Modifica el host? | Cómo se conecta              | Caso de uso principal          |
|------------|--------------------|------------------------------|--------------------------------|
| Función 1  | Sí (poda + replace)| Sustitución de núcleo        | Convertir OpenClaw en TEAM     |
| Función 2  | No                 | Capa de control externa      | Orquestadores ya existentes    |
| Función 3  | No                 | ABI / Extensión kernel       | Cualquier agente que acepte plugins |

---

## Relación con control-layer/ existente

El directorio `control-layer/` actual se evaluará en la siguiente fase de auditoría:

- Si cumple las 3 funciones → se reutiliza y se completa.
- Si está incompleto o contradice → se repara o se reconstruye selectivamente.
- Decisión final: **reparar lo usable + borrar lo que genere deuda**, no start-from-zero ciego ni conservar basura.

---

## Trazabilidad

- Origen: respuesta del Director (2026-08-09) a preguntas P1/P2
- Incorporado como encabezado arquitectónico oficial del PIPELINE

**Estado:** listo para auditoría.
