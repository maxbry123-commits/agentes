# HOL Registry (Universal Agentic Registry)

## Datos básicos
- **URL canónica**: `universal-agentic-registry.org` (a confirmar)
- **Tipo**: estándar + registry federado
- **Función**: que cualquier agent registry pueda federarse con otros sin perder identidad.

## Concepto
Cada participante (nosotros, Anthropic, OpenAI, otros vendors) publica su catálogo en formato HOL. Luego un aggregator puede consultar N sources y armar una vista global.

## Diferencia con nuestro `01-agent`
- **Nuestro `01-agent`**: schema propio, completo, no estándar.
- **HOL entry**: schema fijo, mínimo, diseñado para interoperabilidad.

## Plan de integración
1. Definir mapeo `01-agent` → HOL entry (qué campos de los nuestros van al HOL).
2. Generar `hol/agentes.json` con nuestros 10 agentes.
3. Publicar en rama `hol/` de este repo (visible a fetcher externos).
4. Registrar nuestro endpoint en el HOL aggregator público.

## Pendiente
- [ ] Bajar el spec oficial de HOL (no confiar solo en nombre).
- [ ] Validar nuestro JSON contra el schema de HOL.
- [ ] Decidir si el sync es pull (nosotros escribimos) o push (HOL nos scrapea).
