# NOTA 2026-09-21 - Cierre del cableado del equipo de agentes

Sesion continuada tras corte de contexto. Orden del Director en este turno, textual:
"termina de cerrar no vallas a tocar el plan solo anade y confirma los 2 punto que te
di para meterlo adicional", "Termina sin sobre ingenieria todo para arrancar el equipo
de agentes para que empiecen", "Deja todo los agentes todo integrado y todo conectado y
cableado agente plan todo y paras solo cuando vallas hacer las pruebas para darte una
prueba real paras".

## Lo que se hizo en este turno

1. SALIDA 1 cerrada: Claude notas/INVENTARIO-FORENSE-agent_sources.md
   (blob b62cc6487974d2cb6c4ca0ae0dcb97821c720056). 36 entradas verificadas por Git
   Data API, ninguna supuesta. 20 carpetas REAL + 12 submodules REAL. 1 thin wrapper
   (cua_mcp), 2 paper-only (kimi_k, mimo_code).

2. SALIDA 2, gap mcode cerrado: montado como gitlink real apuntando a
   github.com/MiniMax-AI/minimax-code, commit pineado
   73a2581c6c7525628342f33b53907d4f7bdc146e. Commits 336d6a9e (tree+ref) y af72adba
   (.gitmodules). Read-back verificado: type submodule. 13/13 slots montados.

3. Los 2 puntos adicionales del Director: Claude notas/PLAN-ANEXO-C-2-PUNTOS-ADICIONALES.md
   (blob 2c515211d9a25e8e6870389b145c5ac172c0207c). El PLAN-MAESTRO-4-OBJETIVOS.md NO
   se toco, tal como se ordeno: el anexo solo anade.
   Punto 1: auditoria forense X-Ray de la raiz de Core kernel Yaiwes, componente por
   componente, salida en XRAY-CORE-KERNEL-YAIWES.md.
   Punto 2: auditoria del Wordflow al cierre de cada objetivo con la plantilla del
   metodo de Meta, un archivo por objetivo, mas el cierre de Seals Team y el del
   orquestador comandante.

4. Cableado del equipo: Claude notas/CABLEADO-EQUIPO-AGENTES.md
   (blob 6cf33b612be5ab0fc8ff70030fca212205b1764d). Reparto por objetivo, Ask Consul,
   claves por banco, catalogo real de modelos, grupos y bandera de desbloqueo.

5. Handoffs nuevos, uno por agente que faltaba del loop de 5:
   handoffs/HANDOFF-openhands.md (4c1b0fa5), handoffs/HANDOFF-muse_code.md (d370ecc2),
   handoffs/HANDOFF-muse_glimmer.md (57460597). Ya existian los de claude_code, codex,
   opencode, aider y smolagents.

6. Mensaje para el otro equipo de Claude anotado textual en
   Claude notas/MENSAJE-PARA-EQUIPO-ROUTER-CLAUDE.md.

## Bloqueo de claves: RESUELTO, cambia el metodo

El bloqueo anterior (no se podian sellar las claves NVIDIA con libsodium en este
entorno) YA NO APLICA, porque el metodo cambia: no se suben claves a ningun lado.

Metodo nuevo, del equipo del router (BANCO-SECRETO-README.md):
1. Vault cifrado AES-256-GCM, contraseña maestra solo del Director, fuera de git.
2. Los agentes piden por credential_ref: nvidia/digi-maxbry, nvidia/movistar-briseida,
   nvidia/wow-maxbry, nvidia/wow-brisa. (nvidia/digi-briseida queda fuera, inestable.)
3. El broker resuelve dentro. El agente recibe la respuesta, nunca la clave.
4. Nadie pide, copia ni escribe claves. Si se pega una en el chat, no se usa.

Sigue en pie la recomendacion de seguridad, que es del propio equipo del router:
rotar las claves que se pegaron en chat (NVIDIA, GitHub y Hugging Face) y cargar las
nuevas en el banco. Las de NVIDIA estan en texto plano en
Claude notas/instrucciones 1 a 1 director.md, y este repo es publico.

## Correccion real al catalogo de modelos

Evidencia del equipo del router (runner real de GitHub, 2026-09-20): de la cascada
pensada al principio (Kimi K3, GLM 5, DeepSeek v4 y Nemotron rotando por igual), solo
nvidia/nemotron-3-super-120b-a12b aguanta volumen. DeepSeek v4 flash sirve para tareas
menores con 1-2 peticiones en paralelo como maximo. Kimi K3 y GLM 5.3 flash se agotan
con carga en NVIDIA y van mejor por Hugging Face. Kimi k2.6 da 404 y MiniMax m2.7 esta
retirado (410); MiniMax M3 funciona por el router de Hugging Face y es el de codigo.
El cableado ya refleja esto, no la version teorica.

## Donde se paro y por que

Todo queda integrado, conectado y cableado. El siguiente paso era ejecutar pruebas, y
el Director pidio expresamente parar ahi para darlas el mismo:
"paras solo cuando vallas hacer las pruebas para darte una prueba real paras".
No se lanzo ningun run ni ninguna prueba en este turno.
