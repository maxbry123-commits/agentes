# YAIWES Wordflow — Ajv schema validation

## Rol
Capacidad C determinista para validar contratos JSON Schema/JTD sin LLM. El kernel accede mediante adapter + ficha + Universal Plugin Bus; no importa el proyecto externo directamente.

## Flujo
`Schema + data -> adapter.py -> proceso Node aislado -> Ajv compile -> validate -> {valid, errors}`.

## Código integrado
Se movió únicamente `lib/` y los metadatos mínimos de compilación `package.json` + `tsconfig.json`. No se trasladaron README upstream, docs, benchmark, spec ni scripts auxiliares.

## Cableado
`WIRING.json` conecta fail-closed con Universal Plugin Bus v2 y Ficha Contract v2. `adapter.py` constituye la frontera Python YAIWES y `yaiwes_bridge.js` ejecuta Ajv en proceso Node aislado.

## Procedencia
Origen físico: `Core kernel Yaiwes/Componentes recuperados A/Ajv/`.
Upstream: `https://github.com/ajv-validator/ajv`.
Tree SHA del código movido `lib/`: `0c002b98c6d6560c7fbca0de1a1bc5573953a5ce`.

## Cierre
Exige verificación estática, build, caso válido, caso inválido y repetición runtime 10x. Sin SHA+log real permanece ACTIVE_LOOP.
