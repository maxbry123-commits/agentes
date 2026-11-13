# Apache APISIX — integración YAIWES

Este Wordflow contiene exclusivamente el runtime útil recuperado de Apache APISIX 3.18.0 y su capa de integración YAIWES.

**Función:** gateway API dinámico: routing, plugins, upstream balancing, auth/security y observabilidad.

**Microflujo:** `request + policy ➡️ adapter ➡️ APISIX CLI/LuaJIT ➡️ router/plugins/balancer ➡️ upstream/result ➡️ evidence`.

**Aislamiento:** OpenResty/LuaJIT en proceso/contenedor; 0% LLM; fail-closed.

**Entradas movidas:** `apisix/`, `bin/`, `utils/`, `Makefile`, `apisix-master-0.rockspec`.

**No movido:** README/docs/examples/tests/benchmark/CI/Docker upstream.
