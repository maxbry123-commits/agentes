# skills-registry — ⭐⭐⭐⭐☆

## Datos básicos
- **URL canónica**: `github.com/skills-registry/registry` (a confirmar)
- **Tipo**: estándar JSON Schema para skills
- **Tier**: media madurez, pero su schema es referencia para la industria

## Qué aporta vs los otros 3
- **Schema estándar**: define el JSON Schema canónico de una skill (input/output, side effects, versionado).
- **Validación**: provee `validate.js` para certificar skills que cumplen el schema.
- **Interoperabilidad**: si adoptamos su schema, somos compatibles con cualquier tool que lo consuma.

## Plan de integración
1. Adoptar su JSON Schema como base de nuestro `02-skill`.
2. Diferencias: nuestro schema actual permite `required_tools` y `hints`; ¿el de ellos también? Alinear.
3. Validar todas nuestras skills existentes contra su schema.
4. Publicar nuestro catálogo en su formato para ganar visibilidad.

## Pendiente
- [ ] Confirmar versión actual del schema (v0.x o v1.x).
- [ ] Chequear si su `validate.js` funciona offline (sin red).
- [ ] Hacer un `spectral` lint del schema propio.
