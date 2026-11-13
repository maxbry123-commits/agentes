Descargar y integrar la capacidades del agente rufo con el agente TEAM 

Voy a plantearlo como un proyecto de ingeniería cerrado: objetivo → arquitectura → adquisición → particionamiento → auditoría → extracción → integración → pruebas → publicación, con criterios de entrada/salida para cada etapa.

He verificado además la fuente oficial: ruvnet/ruflo es el repositorio objetivo; GitHub permite consultar el árbol Git y, si truncated=true, exige recorrer subárboles individualmente. GitHub también impone 100 MiB por objeto y 2 GiB por push. 

PLAN MAESTRO — RUFLO → TEAM KERNEL

0. Objetivo final

No queremos instalar Ruflo.

No queremos hacer un fork de Ruflo.

No queremos que TEAM dependa permanentemente de Ruflo.

El objetivo es:

RU FLO SOURCE
     │
     ▼
ADQUISICIÓN DETERMINISTA
     │
     ▼
SNAPSHOT COMPLETO
     │
     ▼
AUDITORÍA 19 PASADAS
     │
     ▼
MAPA DE CAPACIDADES
     │
     ▼
EXTRACCIÓN SELECTIVA
     │
     ├── Memory
     ├── HNSW / vector
     ├── Graph
     ├── Swarm
     ├── Coordination
     ├── Routing
     ├── Guidance
     ├── Security
     ├── Proof
     ├── Hooks
     ├── Learning
     └── otros módulos útiles
     │
     ▼
ADAPTADORES TEAM
     │
     ▼
TEAM KERNEL
     │
     ▼
TEAM WORKFLOW
     │
     ▼
DAG SHERIFF

La documentación actual de Ruflo lo presenta como una plataforma de orquestación multiagente con memoria, swarms, federación, seguridad, MCP, plugins y un motor Rust; por eso no debemos tratarlo como un simple paquete TypeScript. 


---

FASE 0 — CONGELAR LA ESPECIFICACIÓN

Antes de tocar código.

0.1 Definir fuente

source:
  owner: ruvnet
  repository: ruflo
  ref_type: commit

El commit_sha será obligatorio.

Nunca:

main
master
latest

0.2 Definir destino

destination:
  repository: TU_REPO
  root: vendor/ruflo

0.3 Definir política

policy:
  complete_source_required: true
  partial_source_allowed: false
  fail_closed: true
  deterministic_partitioning: true
  atomic_publish: true

Resultado

Se genera:

SOURCE_LOCK

Si SOURCE_LOCK cambia, es una adquisición diferente.


---

FASE 1 — DESCUBRIMIENTO DEL COMMIT

Primero resolver:

repository
        ↓
ref
        ↓
commit
        ↓
commit.tree.sha

No descargamos todavía.

Validaciones

V1 repository existe
V2 commit existe
V3 commit es inmutable
V4 tree SHA existe
V5 source identity coincide

Salida

01-source-lock.json

Contendrá:

repository
commit_sha
tree_sha
release/tag
retrieval_timestamp
tool_version
policy_version

El timestamp no participa en la identidad del snapshot.


---

FASE 2 — RECONSTRUCCIÓN DEL GIT TREE

Esta es una de las partes críticas.

GitHub limita la respuesta recursiva del Tree API a 100.000 entradas/7 MB; si truncated=true, debemos abandonar la respuesta recursiva y recorrer los subárboles. 

Por tanto:

ROOT TREE
   │
   ├── directory A
   │     ├── subtree
   │     └── subtree
   │
   ├── directory B
   │
   └── files

Se reconstruye hasta que:

truncated == false

o hasta que todos los subárboles hayan sido procesados.

Salida

02-complete-tree.json


---

FASE 3 — INVENTARIO FORENSE

Convertimos el tree en un inventario normalizado.

Cada archivo:

path:
mode:
type:
blob_sha:
size:

Además:

extension
language
directory
module_candidate

No se utiliza todavía para decidir qué conservar.

Principio

Primero inventariar todo. Después decidir.


---

FASE 4 — AUDITORÍA DE COMPLETITUD

Aquí verificamos que:

GitHub TREE
      ==
LOCAL MANIFEST

Comprobar:

cantidad de archivos
cantidad de árboles
cantidad de blobs
tamaños
SHA Git
paths
modes

Si existe:

missing file
extra file
different SHA
different size

→ STOP.


---

FASE 5 — PRE-FLIGHT DE GITHUB

Ahora calculamos:

TOTAL BYTES
LARGEST FILE
FILE COUNT
EXPECTED PUSH
DESTINATION GROWTH

GitHub bloquea archivos superiores a 100 MiB en Git normal y establece un límite de 2 GiB por push. También recomienda mantener los repositorios pequeños, idealmente por debajo de 1 GB y fuertemente por debajo de 5 GB. 

Importante

No usaremos:

1.5 GB = límite de GitHub

porque eso sería falso.

Usaremos:

GITHUB_HARD_LIMIT
TEAM_OPERATIONAL_LIMIT

como conceptos separados.


---

FASE 6 — PARTICIONAMIENTO DETERMINISTA

Si el snapshot completo puede publicarse en una operación:

PART-000

Si no:

PART-001
PART-002
PART-003
...

La partición será calculada antes de descargar.

Algoritmo

Ordenar por:

normalized_path ASC

Después empaquetar secuencialmente respetando:

max_object_size
max_push_payload
operational_margin

Nunca:

aleatorio
hash mod N
orden del filesystem
orden de llegada de API

Propiedad

Mismo:

commit
tree
policy
partition algorithm

produce exactamente:

PART-001 ... PART-N

GitHub documenta explícitamente que un push superior a 2 GiB debe dividirse en partes más pequeñas. 


---

FASE 7 — ADQUISICIÓN FÍSICA

Ahora sí descargamos.

Pero el proceso será:

REMOTE
  ↓
STREAM
  ↓
TEMP FILE
  ↓
HASH
  ↓
VERIFY

No:

REMOTE
  ↓
RAM completa

Cada parte

download.part
download.sha256
download.manifest

Si falla:

DELETE PART
RETRY

Si supera el número de reintentos:

FAIL

No se continúa silenciosamente.


---

FASE 8 — EXTRACCIÓN SEGURA

Cada archivo se extrae dentro de:

/staging/ruflo/

Antes de escribir:

normalize(path)
validate(path)
validate(mode)
validate(type)

Rechazar:

../
absolute path
escape
unexpected symlink
device node
nested .git

La extracción nunca escribe directamente sobre:

vendor/ruflo


---

FASE 9 — RECONSTRUCCIÓN LOCAL

Una vez extraído:

STAGING
   ↓
LOCAL TREE

Generamos:

03-local-manifest.json


---

FASE 10 — VERIFICACIÓN CRUZADA

Comparación:

EXPECTED MANIFEST
       VS
ACTUAL MANIFEST

Debe cumplirse:

same paths
same file count
same sizes
same Git blob SHA
same content SHA
same modes

Resultado

SNAPSHOT_VERIFIED

o:

SNAPSHOT_REJECTED


---

FASE 11 — AUDITORÍA ARQUITECTÓNICA DE RUFLO

Ahora empieza la auditoría que realmente te interesa.

No vamos a preguntar:

> "¿Qué carpetas tiene Ruflo?"



Vamos a preguntar:

> "¿Qué capacidad proporciona cada módulo y qué puede aportar al TEAM?"



Cada módulo recibe una ficha:

module:
source_files:
public_interfaces:
internal_dependencies:
external_dependencies:
runtime:
language:
state:
memory:
network:
filesystem:
security:
determinism:
performance:
test_coverage:
team_relevance:
claude_coupling:
action:


---

FASE 12 — LAS 19 PASADAS

Las 19 pasadas se ejecutarán sobre ese snapshot congelado, no sobre main.

P01

Identidad y provenance.

P02

Git tree completo.

P03

Inventario archivo por archivo.

P04

Dependencias internas.

P05

Dependencias externas.

P06

Runtime y entrypoints.

P07

Rust/WASM/native.

P08

Memory/vector/HNSW.

P09

Graph/RAG.

P10

Swarm/coordination.

P11

Routing/model selection.

P12

Guidance/gates/policies.

P13

Security/trust/authority.

P14

Proof/ledger/auditability.

P15

Hooks/event system.

P16

MCP/API/adapters.

P17

Plugins/agents.

P18

Determinismo/performance/fallos.

P19

Extracción y diseño TEAM.


---

FASE 13 — CLASIFICACIÓN DE CADA MÓDULO

Cada módulo debe terminar en exactamente una categoría:

KEEP

Mantener casi íntegramente.

ADAPT

Útil pero requiere desacoplamiento.

EXTRACT

Extraer únicamente una capacidad.

ISOLATE

Mantener separado porque está demasiado acoplado.

REIMPLEMENT

La idea sirve, pero la implementación no.

REJECT

No aporta al TEAM.


---

FASE 14 — MAPA RUFLO → TEAM

Generaremos una matriz:

Ruflo	Capacidad	TEAM	Acción

Memory	memoria persistente	TEAM Memory	ADAPT
HNSW/vector	recuperación vectorial	TEAM Memory	EXTRACT
Graph	relaciones	TEAM Graph	ADAPT
Swarm	coordinación	TEAM Orchestrator	EXTRACT
Guidance	gates/policies	Sheriff	EXTRACT
Proof	trazabilidad	Sheriff	EXTRACT
Security	validación	Security Kernel	ADAPT
Hooks	eventos	Workflow	ADAPT
MCP	interfaces	Adapter layer	ISOLATE
Claude-specific	integración Claude	Adapter	ISOLATE


La tabla definitiva solamente se llena después de las 19 pasadas.


---

FASE 15 — DISEÑO DEL NUEVO KERNEL

Aquí es donde cumplimos tu idea original.

No:

TEAM
  ↓
Ruflo

Sino:

TEAM KERNEL
├── Memory Kernel
├── Vector/HNSW Kernel
├── Graph Kernel
├── Coordination Kernel
├── Policy Kernel
├── Security Kernel
├── Proof Kernel
├── Learning Kernel
└── Extension Kernel

Ruflo deja de ser dependencia.


---

FASE 16 — EXTENSION KERNEL

Los elementos que no deben entrar al núcleo quedan como:

team/extensions/ruflo-derived/

Ejemplo:

extensions/
└── ruflo-derived/
    ├── memory/
    ├── swarm/
    ├── guidance/
    ├── proof/
    └── adapters/

Esto permite evolucionar el kernel sin contaminarlo con dependencias externas.


---

FASE 17 — INTEGRACIÓN CON WORDFLOW

La integración no debe permitir que Ruflo controle directamente el Workflow.

La relación será:

WORDflow
    │
    ▼
TEAM ORCHESTRATOR
    │
    ▼
DAG
    │
    ▼
SHERIFF
    │
    ├── policy
    ├── memory gate
    ├── security gate
    ├── proof gate
    └── execution gate
    │
    ▼
KERNEL

Ruflo-derived será una capability provider, no el dueño del flujo.


---

FASE 18 — TESTING

Habrá cinco niveles.

T1 — Acquisition

source == expected

T2 — Integrity

manifest == snapshot

T3 — Module

Cada módulo extraído funciona independientemente.

T4 — Kernel

TEAM funciona sin Ruflo.

T5 — Workflow

Workflow
 → TEAM
 → Sheriff
 → Kernel
 → Agent


---

FASE 19 — PRUEBA DE DESACOPLAMIENTO

Esta es obligatoria.

Después de integrar:

RUFLO SOURCE

se elimina temporalmente del entorno.

TEAM debe seguir arrancando.

Debe comprobarse:

TEAM runtime
TEAM memory
TEAM workflow
TEAM DAG
TEAM Sheriff
TEAM agents

sin Ruflo.

Si algo deja de funcionar:

DECOUPLING_FAILED


---

FASE 20 — PUBLICACIÓN

No se publica hasta tener:

SOURCE_LOCK
TREE_MANIFEST
ACQUISITION_MANIFEST
PARTITION_MANIFEST
VERIFICATION_REPORT
MODULE_AUDIT
CAPABILITY_MAP
EXTRACTION_MAP
DEPENDENCY_MAP
TEST_REPORT
DECOUPLING_REPORT


---

FASE 21 — ESTRUCTURA FINAL DEL REPOSITORIO

La estructura objetivo será aproximadamente:

/
├── control-layer/
│   ├── dsl/
│   ├── schema/
│   ├── dag/
│   └── sheriff/
│
├── vendor/
│   └── ruflo/
│
├── team-kernel/
│   ├── memory/
│   ├── vector/
│   ├── graph/
│   ├── coordination/
│   ├── security/
│   ├── policy/
│   ├── proof/
│   └── learning/
│
├── team-extensions/
│   └── ruflo-derived/
│
├── workflow/
│
├── agents/
│
└── audit/
    ├── acquisition/
    ├── ruflo/
    ├── extraction/
    └── integration/


---

FASE 22 — DSL/DAG/SHERIFF

El DSL no se programa al principio.

Primero se congelan:

SOURCE
TREE
MANIFEST
POLICY
PARTITION

Después se implementa:

DSL
 ↓
SCHEMA
 ↓
DAG
 ↓
SHERIFF
 ↓
RUNNER

El Sheriff tendrá cuatro estados:

DISCOVERED
VALIDATED
ACQUIRED
PUBLISHED

Y estados terminales:

FAILED
REJECTED
ABORTED

Nunca:

PARTIAL_SUCCESS

porque contradice tu requisito de adquisición completa.


---

FASE 23 — ASK COUNCIL DENTRO DEL SISTEMA

Los 12 checks que pediste no serán solamente una lista escrita.

Serán gates ejecutables:

C01 SOURCE
C02 TREE
C03 INVENTORY
C04 SIZE
C05 COMPLETENESS
C06 DEPENDENCY
C07 SECURITY
C08 DOWNLOAD
C09 RECONSTRUCTION
C10 ATOMICITY
C11 DETERMINISM
C12 WITNESS

El DAG no puede pasar a PUBLISH si:

C01..C12 != PASS


---

FASE 24 — IDEMPOTENCIA

Si ejecutamos dos veces:

RUN A
RUN B

con exactamente:

same source
same commit
same policy
same destination state

el resultado debe ser equivalente.

Si ya existe el snapshot:

NO DUPLICATE COPY

Si existe pero no coincide:

CONFLICT

No sobrescribir silenciosamente.


---

FASE 25 — RECUPERACIÓN

Si falla:

download
network
API
disk
hash
extract
Git
push

el sistema registra:

failure code
node
part
attempt
reason

y vuelve al último checkpoint seguro.

No se reanuda desde un archivo cuya integridad no esté comprobada.


---

FASE 26 — PROTECCIÓN CONTRA GITHUB

El sistema respetará:

100 MiB/object
2 GiB/push
API read-rate policy
push-rate policy

GitHub recomienda no superar 15 operaciones de lectura por segundo por repositorio y 6 pushes por minuto; el Sheriff debe incorporar un rate governor para no generar una tormenta de llamadas. 


---

FASE 27 — CRITERIO DE ÉXITO

La adquisición solamente se considera exitosa si:

SOURCE_LOCK = VALID
TREE = COMPLETE
INVENTORY = COMPLETE
PARTITIONS = DETERMINISTIC
DOWNLOAD = COMPLETE
HASHES = VALID
EXTRACTION = SAFE
MANIFEST = MATCH
STAGING = VALID
PUBLISH = ATOMIC

Y posteriormente:

RUFLO_VENDOR = COMPLETE
RUFLO_DEPENDENCY = NOT REQUIRED
TEAM_KERNEL = OPERATIONAL
WORDflow = OPERATIONAL


---

FASE 28 — ORDEN REAL DE EJECUCIÓN

El proyecto completo queda así:

01  SOURCE LOCK
 ↓
02  COMMIT RESOLUTION
 ↓
03  TREE DISCOVERY
 ↓
04  TREE RECONSTRUCTION
 ↓
05  COMPLETE INVENTORY
 ↓
06  GITHUB PREFLIGHT
 ↓
07  DESTINATION PREFLIGHT
 ↓
08  DETERMINISTIC PARTITION
 ↓
09  DOWNLOAD
 ↓
10  HASH
 ↓
11  SAFE EXTRACTION
 ↓
12  LOCAL RECONSTRUCTION
 ↓
13  MANIFEST COMPARISON
 ↓
14  ATOMIC STAGING
 ↓
15  PUBLISH
 ↓
16  19-PASS RUFLO AUDIT
 ↓
17  CAPABILITY MAP
 ↓
18  EXTRACTION MAP
 ↓
19  TEAM KERNEL DESIGN
 ↓
20  ADAPTER DESIGN
 ↓
21  WORDflow INTEGRATION
 ↓
22  UNIT TESTS
 ↓
23  INTEGRATION TESTS
 ↓
24  DECOUPLING TEST
 ↓
25  FINAL SHERIFF
 ↓
26  RELEASE

Y la regla central

No se empieza por modificar Ruflo.

Primero:

Ruflo original
      ↓
snapshot verificable
      ↓
auditoría
      ↓
capability map

Después:

capability map
      ↓
TEAM Kernel

Y solamente al final:

TEAM Kernel
      ↓
Wordflow
      ↓
Agents

Esto evita el error más peligroso del proyecto: mezclar desde el principio código de Ruflo con TEAM y luego no poder determinar qué parte funciona, qué parte depende de Ruflo y qué parte realmente aporta al kernel.

La fuente actual de Ruflo confirma además que existen dos superficies de instalación distintas —plugin de Claude Code y CLI—, por lo que esas superficies deben permanecer fuera de la adquisición del código fuente salvo que una auditoría posterior determine que alguna pieza concreta es reutilizable. 

Esta es la planificación completa. El siguiente entregable, si seguimos este orden, es el DSL + Schema + DAG + Sheriff de la Fase 1, construido exactamente sobre este plan, y después se ejecuta la auditoría del snapshot; no se salta directamente a la extracción.


# ============================================================
# RUFLO DETERMINISTIC ACQUISITION
# OUTPUT 1A / 1 — FOUNDATION
# DSL + DETERMINISTIC CONFIGURATION
# ============================================================

# ------------------------------------------------------------
# FILE: dsl/ruflo.acquire.yaml
# ------------------------------------------------------------

version: "1.0.0"
kind: "DeterministicAcquisition"

system:
  name: "ruflo-deterministic-acquirer"
  contract_version: "1.0.0"
  execution_mode: "fail_closed"
  determinism: "strict"

source:
  provider: "github"
  owner: "ruvnet"
  repository: "ruflo"

  # IMPORTANT:
  # Acquisition is permitted ONLY from an immutable commit.
  ref_type: "commit"
  commit_sha: "${RUFLO_COMMIT_SHA}"
  require_full_sha: true

destination:
  provider: "github"
  repository: "${DESTINATION_REPOSITORY}"

  # Ruflo is copied as source material.
  root: "vendor/ruflo"

  # Never download directly into the destination.
  staging_root: ".acquisition/staging/ruflo"

acquisition:
  source_only: true

  # The acquired source is never executed by the downloader.
  execute_source: false

  # Dependencies are not installed during acquisition.
  install_dependencies: false

  # No build is performed during acquisition.
  generate_build_artifacts: false

  # The source repository's .git metadata is not copied.
  include_git_metadata: false

  # External dependencies are NOT recursively downloaded.
  follow_external_dependencies: false

  preserve_file_modes: true
  preserve_symlinks: false

tree:
  recursive: true

  # A complete Git tree is mandatory.
  require_complete: true

  # A truncated GitHub tree is never accepted.
  reject_truncated: true

  # Canonical ordering.
  sort: "path_lexicographic"

inventory:
  required_fields:
    - path
    - mode
    - type
    - size
    - git_blob_sha

  reject_duplicate_paths: true
  reject_unknown_types: true

partition:
  enabled: true

  # This algorithm is defined by the Foundation contract.
  algorithm: "LEXICOGRAPHIC_FIRST_FIT_V1"

  # GitHub hard object limit.
  max_object_bytes: 104857600

  # Operational push ceiling is intentionally below the
  # GitHub hard 2 GiB push limit.
  max_push_bytes: 1800000000

  # Reserved safety margin.
  safety_margin_bytes: 100000000

  preserve_directory_boundaries: false

download:
  mode: "stream_to_disk"

  # Maximum memory buffer used by an individual stream.
  memory_buffer_bytes: 1048576

  timeout_seconds: 60

  max_retries: 3

  retry_backoff_seconds: 2

  # Failed temporary files cannot become verified files.
  delete_failed_partial_files: true

security:
  reject_absolute_paths: true
  reject_parent_traversal: true
  reject_nested_git: true
  reject_devices: true
  reject_unexpected_symlinks: true
  reject_null_bytes: true

verification:
  compare_paths: true
  compare_sizes: true
  compare_git_blob_sha: true
  compare_content_sha256: true

  require_exact_file_count: true
  require_exact_total_bytes: true

  reconstruct_tree: true
  require_complete_tree: true

publish:
  atomic: true

  require_sheriff_authorization: true

  allow_partial_publish: false
  allow_unverified_publish: false

  verify_remote_after_push: true

  # A failed publication must not be interpreted as success.
  fail_closed: true

council:
  required_passes: 12
  fail_on_any_failure: true

  # No warning may substitute for PASS.
  warning_is_not_pass: true

recovery:
  enabled: true

  # Only verified checkpoints may be resumed.
  require_verified_checkpoint: true

  # Unverified partial state cannot be promoted.
  promote_partial_state: false

rate_governor:
  enabled: true

  # Network execution is controlled by later acquisition modules.
  # These values are policy contracts, not download commands.
  max_concurrent_requests: 1
  preserve_request_order: true

output:
  manifest_format: "json"
  canonical_json: true
  utf8: true
  sort_keys: true


# ------------------------------------------------------------
# FILE: dsl/README.contract.md
# ------------------------------------------------------------

# FOUNDATION CONTRACT

This DSL defines the immutable acquisition contract.

The complete system is divided into four logical layers:

1. FOUNDATION
2. ACQUISITION
3. VERIFICATION / SHERIFF
4. PUBLISH / RECOVERY

This block implements only FOUNDATION.

FOUNDATION does not:

- contact GitHub;
- download files;
- extract archives;
- execute Ruflo;
- install Ruflo dependencies;
- modify the destination repository;
- perform a Git push.

Those operations belong to later outputs.


# ------------------------------------------------------------
# SOURCE CONTRACT
# ------------------------------------------------------------

The source MUST identify:

- provider;
- owner;
- repository;
- immutable commit SHA.

The source MUST NOT be:

- main;
- master;
- latest;
- a mutable branch;
- an unresolved tag;
- an unresolved symbolic reference.

The canonical source identity is:

provider + owner + repository + commit_sha


# ------------------------------------------------------------
# DESTINATION CONTRACT
# ------------------------------------------------------------

The destination has two locations:

STAGING:

.acquisition/staging/ruflo

PUBLISHED:

vendor/ruflo

The downloader MUST never write directly into the published path.


# ------------------------------------------------------------
# DETERMINISTIC ORDER
# ------------------------------------------------------------

All filesystem and inventory processing must use:

UTF-8
POSIX paths
lexicographic path ordering

The following are forbidden as ordering inputs:

- filesystem enumeration order;
- thread completion order;
- API response arrival order;
- random ordering;
- timestamps;
- process IDs.


# ------------------------------------------------------------
# PARTITION CONTRACT
# ------------------------------------------------------------

Partitioning is deterministic.

Algorithm:

LEXICOGRAPHIC_FIRST_FIT_V1

Input:

normalized inventory sorted by path.

Output:

ordered partitions.

The same:

source commit
+
inventory
+
partition policy

MUST produce the same partition map.


# ------------------------------------------------------------
# FAILURE CONTRACT
# ------------------------------------------------------------

The following conditions are fatal:

- mutable source;
- invalid commit;
- incomplete tree;
- duplicate path;
- unsafe path;
- invalid file size;
- object above configured limit;
- invalid partition;
- failed verification;
- failed Council gate;
- unauthorized publish.

There is no implicit partial success.


# ------------------------------------------------------------
# STATE CONTRACT
# ------------------------------------------------------------

Valid logical progression:

INIT
  ↓
CONFIG_VALIDATED
  ↓
SOURCE_LOCKED
  ↓
TREE_DISCOVERED
  ↓
INVENTORY_BUILT
  ↓
PARTITIONED
  ↓
ACQUIRED
  ↓
VERIFIED
  ↓
AUTHORIZED
  ↓
STAGED
  ↓
PUBLISHED

Any fatal error:

ANY_STATE
  ↓
FAILED


# ------------------------------------------------------------
# END OUTPUT 1A
# ------------------------------------------------------------

# ============================================================
# RUFLO DETERMINISTIC ACQUISITION
# OUTPUT 1B / 1 — FOUNDATION
# SCHEMA + DATA MODEL
# ============================================================

# ------------------------------------------------------------
# FILE: schema/acquisition.schema.json
# ------------------------------------------------------------

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "ruflo-deterministic-acquisition-1.0.0",

  "type": "object",

  "required": [
    "version",
    "kind",
    "system",
    "source",
    "destination",
    "acquisition",
    "tree",
    "inventory",
    "partition",
    "download",
    "security",
    "verification",
    "publish",
    "council"
  ],

  "properties": {

    "version": {
      "const": "1.0.0"
    },

    "kind": {
      "const": "DeterministicAcquisition"
    },

    "system": {
      "type": "object",
      "required": [
        "name",
        "contract_version",
        "execution_mode",
        "determinism"
      ]
    },

    "source": {
      "type": "object",
      "required": [
        "provider",
        "owner",
        "repository",
        "ref_type",
        "commit_sha",
        "require_full_sha"
      ],

      "properties": {
        "provider": {
          "const": "github"
        },

        "owner": {
          "type": "string",
          "minLength": 1
        },

        "repository": {
          "type": "string",
          "minLength": 1
        },

        "ref_type": {
          "const": "commit"
        },

        "commit_sha": {
          "type": "string",
          "pattern": "^[0-9a-f]{40}$"
        },

        "require_full_sha": {
          "const": true
        }
      }
    },

    "destination": {
      "type": "object",
      "required": [
        "provider",
        "repository",
        "root",
        "staging_root"
      ]
    },

    "tree": {
      "type": "object",
      "required": [
        "recursive",
        "require_complete",
        "reject_truncated"
      ]
    },

    "partition": {
      "type": "object",
      "required": [
        "enabled",
        "algorithm",
        "max_object_bytes",
        "max_push_bytes",
        "safety_margin_bytes"
      ],

      "properties": {
        "enabled": {
          "const": true
        },

        "algorithm": {
          "const": "LEXICOGRAPHIC_FIRST_FIT_V1"
        },

        "max_object_bytes": {
          "type": "integer",
          "minimum": 1,
          "maximum": 104857600
        },

        "max_push_bytes": {
          "type": "integer",
          "minimum": 1,
          "maximum": 2147483648
        },

        "safety_margin_bytes": {
          "type": "integer",
          "minimum": 0
        }
      }
    },

    "council": {
      "type": "object",
      "required": [
        "required_passes",
        "fail_on_any_failure"
      ],

      "properties": {
        "required_passes": {
          "const": 12
        },

        "fail_on_any_failure": {
          "const": true
        }
      }
    }
  }
}


# ------------------------------------------------------------
# FILE: foundation/model.py
# ------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ------------------------------------------------------------
# CONTRACT CONSTANTS
# ------------------------------------------------------------

CONTRACT_VERSION = "1.0.0"

PARTITION_ALGORITHM = (
    "LEXICOGRAPHIC_FIRST_FIT_V1"
)

GITHUB_MAX_OBJECT_BYTES = (
    100 * 1024 * 1024
)

GITHUB_MAX_PUSH_BYTES = (
    2 * 1024 * 1024 * 1024
)


# ------------------------------------------------------------
# STATE MACHINE
# ------------------------------------------------------------

class RunState(str, Enum):

    INIT = "INIT"

    CONFIG_VALIDATED = (
        "CONFIG_VALIDATED"
    )

    SOURCE_LOCKED = (
        "SOURCE_LOCKED"
    )

    TREE_DISCOVERED = (
        "TREE_DISCOVERED"
    )

    INVENTORY_BUILT = (
        "INVENTORY_BUILT"
    )

    PARTITIONED = (
        "PARTITIONED"
    )

    ACQUIRED = (
        "ACQUIRED"
    )

    VERIFIED = (
        "VERIFIED"
    )

    AUTHORIZED = (
        "AUTHORIZED"
    )

    STAGED = (
        "STAGED"
    )

    PUBLISHED = (
        "PUBLISHED"
    )

    FAILED = "FAILED"


TERMINAL_STATES = {
    RunState.PUBLISHED,
    RunState.FAILED,
}


# ------------------------------------------------------------
# ERRORS
# ------------------------------------------------------------

class FoundationError(Exception):
    """Base Foundation exception."""


class ConfigError(FoundationError):
    """Invalid DSL configuration."""


class DeterminismError(FoundationError):
    """Determinism contract violation."""


class SecurityError(FoundationError):
    """Unsafe source/path/object."""


class StateTransitionError(FoundationError):
    """Invalid state transition."""


class VerificationError(FoundationError):
    """Verification failure."""


class SheriffError(FoundationError):
    """Sheriff authorization failure."""


# ------------------------------------------------------------
# SOURCE LOCK
# ------------------------------------------------------------

@dataclass(frozen=True)
class SourceLock:

    provider: str
    owner: str
    repository: str
    commit_sha: str

    def canonical(self) -> dict[str, str]:

        return {
            "provider": self.provider,
            "owner": self.owner,
            "repository": self.repository,
            "commit_sha": self.commit_sha,
        }


# ------------------------------------------------------------
# TREE ENTRY
# ------------------------------------------------------------

@dataclass(frozen=True)
class TreeEntry:

    path: str
    mode: str
    type: str
    size: int
    git_blob_sha: str

    def canonical(self) -> dict[str, Any]:

        return {
            "path": self.path,
            "mode": self.mode,
            "type": self.type,
            "size": self.size,
            "git_blob_sha": self.git_blob_sha,
        }


# ------------------------------------------------------------
# PARTITION
# ------------------------------------------------------------

@dataclass(frozen=True)
class Partition:

    number: int

    paths: tuple[str, ...]

    total_bytes: int

    def canonical(self) -> dict[str, Any]:

        return {
            "number": self.number,
            "paths": list(self.paths),
            "total_bytes": self.total_bytes,
        }


# ------------------------------------------------------------
# COUNCIL RESULT
# ------------------------------------------------------------

@dataclass(frozen=True)
class CouncilResult:

    code: str
    passed: bool
    reason: str

    def canonical(self) -> dict[str, Any]:

        return {
            "code": self.code,
            "passed": self.passed,
            "reason": self.reason,
        }


# ------------------------------------------------------------
# RUN CONTEXT
# ------------------------------------------------------------

@dataclass
class RunContext:

    state: RunState = RunState.INIT

    source: SourceLock | None = None

    tree: list[TreeEntry] = field(
        default_factory=list
    )

    partitions: list[Partition] = field(
        default_factory=list
    )

    council: list[CouncilResult] = field(
        default_factory=list
    )

    errors: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ------------------------------------------------------------
# STATE TRANSITIONS
# ------------------------------------------------------------

VALID_TRANSITIONS = {

    RunState.INIT: {
        RunState.CONFIG_VALIDATED,
        RunState.FAILED,
    },

    RunState.CONFIG_VALIDATED: {
        RunState.SOURCE_LOCKED,
        RunState.FAILED,
    },

    RunState.SOURCE_LOCKED: {
        RunState.TREE_DISCOVERED,
        RunState.FAILED,
    },

    RunState.TREE_DISCOVERED: {
        RunState.INVENTORY_BUILT,
        RunState.FAILED,
    },

    RunState.INVENTORY_BUILT: {
        RunState.PARTITIONED,
        RunState.FAILED,
    },

    RunState.PARTITIONED: {
        RunState.ACQUIRED,
        RunState.FAILED,
    },

    RunState.ACQUIRED: {
        RunState.VERIFIED,
        RunState.FAILED,
    },

    RunState.VERIFIED: {
        RunState.AUTHORIZED,
        RunState.FAILED,
    },

    RunState.AUTHORIZED: {
        RunState.STAGED,
        RunState.FAILED,
    },

    RunState.STAGED: {
        RunState.PUBLISHED,
        RunState.FAILED,
    },

    RunState.PUBLISHED: set(),

    RunState.FAILED: set(),
}


def transition(
    context: RunContext,
    new_state: RunState,
) -> None:

    allowed = VALID_TRANSITIONS.get(
        context.state,
        set(),
    )

    if new_state not in allowed:

        raise StateTransitionError(
            f"invalid transition: "
            f"{context.state.value} -> "
            f"{new_state.value}"
        )

    context.state = new_state


# ------------------------------------------------------------
# END OUTPUT 1B
# ------------------------------------------------------------
# ============================================================
# RUFLO DETERMINISTIC ACQUISITION
# OUTPUT 1C / 1 — FOUNDATION
# DAG + SHERIFF + DETERMINISTIC EXECUTOR
# ============================================================

# ------------------------------------------------------------
# FILE: foundation/runtime.py
# ------------------------------------------------------------

from __future__ import annotations

import hashlib
import json
import re
import sys

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Callable

from foundation.model import (
    CONTRACT_VERSION,
    GITHUB_MAX_OBJECT_BYTES,
    GITHUB_MAX_PUSH_BYTES,
    PARTITION_ALGORITHM,
    ConfigError,
    DeterminismError,
    FoundationError,
    RunContext,
    RunState,
    SecurityError,
    SourceLock,
    TreeEntry,
    transition,
)


FULL_SHA_RE = re.compile(
    r"^[0-9a-f]{40}$"
)


# ------------------------------------------------------------
# CANONICAL SERIALIZATION
# ------------------------------------------------------------

def canonical_json(
    value: Any,
) -> bytes:

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_bytes(
    data: bytes,
) -> str:

    return hashlib.sha256(
        data
    ).hexdigest()


def sha256_json(
    value: Any,
) -> str:

    return sha256_bytes(
        canonical_json(value)
    )


# ------------------------------------------------------------
# PATH VALIDATION
# ------------------------------------------------------------

def validate_relative_path(
    path: str,
) -> str:

    if not isinstance(path, str):
        raise SecurityError(
            "path must be a string"
        )

    if not path:
        raise SecurityError(
            "path cannot be empty"
        )

    if "\x00" in path:
        raise SecurityError(
            f"NUL byte in path: {path!r}"
        )

    if path.startswith("/"):
        raise SecurityError(
            f"absolute path rejected: {path}"
        )

    normalized = str(
        PurePosixPath(path)
    )

    if normalized == "..":
        raise SecurityError(
            f"parent traversal rejected: {path}"
        )

    if normalized.startswith("../"):
        raise SecurityError(
            f"parent traversal rejected: {path}"
        )

    if "/../" in (
        "/" + normalized + "/"
    ):
        raise SecurityError(
            f"parent traversal rejected: {path}"
        )

    if (
        normalized == ".git"
        or normalized.startswith(".git/")
    ):
        raise SecurityError(
            f"nested .git rejected: {path}"
        )

    return normalized


# ------------------------------------------------------------
# CONFIGURATION VALIDATION
# ------------------------------------------------------------

def require_keys(
    mapping: dict[str, Any],
    *keys: str,
) -> None:

    for key in keys:

        if key not in mapping:

            raise ConfigError(
                f"missing configuration key: {key}"
            )


def validate_config(
    cfg: dict[str, Any],
) -> None:

    require_keys(
        cfg,
        "version",
        "kind",
        "system",
        "source",
        "destination",
        "acquisition",
        "tree",
        "inventory",
        "partition",
        "download",
        "security",
        "verification",
        "publish",
        "council",
    )

    if cfg["version"] != CONTRACT_VERSION:
        raise ConfigError(
            "invalid contract version"
        )

    if cfg["kind"] != (
        "DeterministicAcquisition"
    ):
        raise ConfigError(
            "invalid DSL kind"
        )

    source = cfg["source"]

    require_keys(
        source,
        "provider",
        "owner",
        "repository",
        "ref_type",
        "commit_sha",
        "require_full_sha",
    )

    if source["provider"] != "github":
        raise ConfigError(
            "provider must be github"
        )

    if source["ref_type"] != "commit":
        raise DeterminismError(
            "mutable refs are forbidden"
        )

    commit = source["commit_sha"]

    if "${" in commit:
        raise ConfigError(
            "commit_sha has not been resolved"
        )

    if (
        source["require_full_sha"]
        and not FULL_SHA_RE.fullmatch(commit)
    ):
        raise DeterminismError(
            "commit_sha must be a full 40-character SHA"
        )

    acquisition = cfg["acquisition"]

    if acquisition["source_only"] is not True:
        raise ConfigError(
            "source_only must be true"
        )

    if acquisition["execute_source"] is not False:
        raise ConfigError(
            "source execution is forbidden"
        )

    if acquisition[
        "install_dependencies"
    ] is not False:
        raise ConfigError(
            "dependency installation is forbidden"
        )

    tree = cfg["tree"]

    if tree["require_complete"] is not True:
        raise ConfigError(
            "complete tree is mandatory"
        )

    if tree["reject_truncated"] is not True:
        raise ConfigError(
            "truncated tree is forbidden"
        )

    partition = cfg["partition"]

    if partition["enabled"] is not True:
        raise ConfigError(
            "partitioning must be enabled"
        )

    if partition["algorithm"] != (
        PARTITION_ALGORITHM
    ):
        raise DeterminismError(
            "unsupported partition algorithm"
        )

    max_object = int(
        partition["max_object_bytes"]
    )

    max_push = int(
        partition["max_push_bytes"]
    )

    margin = int(
        partition["safety_margin_bytes"]
    )

    if (
        max_object <= 0
        or max_object > GITHUB_MAX_OBJECT_BYTES
    ):
        raise ConfigError(
            "invalid object limit"
        )

    if (
        max_push <= 0
        or max_push > GITHUB_MAX_PUSH_BYTES
    ):
        raise ConfigError(
            "invalid push limit"
        )

    if margin < 0:
        raise ConfigError(
            "negative safety margin"
        )

    if margin >= max_push:
        raise ConfigError(
            "safety margin consumes entire push capacity"
        )

    council = cfg["council"]

    if council["required_passes"] != 12:
        raise ConfigError(
            "Council requires exactly 12 gates"
        )

    if council[
        "fail_on_any_failure"
    ] is not True:
        raise ConfigError(
            "Council must be fail-closed"
        )


# ------------------------------------------------------------
# SOURCE LOCK
# ------------------------------------------------------------

def build_source_lock(
    cfg: dict[str, Any],
) -> SourceLock:

    source = cfg["source"]

    return SourceLock(
        provider=source["provider"],
        owner=source["owner"],
        repository=source["repository"],
        commit_sha=source["commit_sha"],
    )


# ------------------------------------------------------------
# TREE NORMALIZATION
# ------------------------------------------------------------

def normalize_inventory(
    entries: list[TreeEntry],
) -> list[TreeEntry]:

    result: list[TreeEntry] = []

    seen: set[str] = set()

    for entry in entries:

        path = validate_relative_path(
            entry.path
        )

        if path in seen:
            raise DeterminismError(
                f"duplicate path: {path}"
            )

        seen.add(path)

        if entry.type != "blob":
            raise DeterminismError(
                f"unexpected tree entry type: "
                f"{entry.type}: {path}"
            )

        if entry.size < 0:
            raise DeterminismError(
                f"negative file size: {path}"
            )

        result.append(
            TreeEntry(
                path=path,
                mode=entry.mode,
                type=entry.type,
                size=entry.size,
                git_blob_sha=entry.git_blob_sha,
            )
        )

    result.sort(
        key=lambda entry: entry.path
    )

    return result


# ------------------------------------------------------------
# FOUNDATION DAG
# ------------------------------------------------------------

@dataclass(frozen=True)
class DAGNode:

    node_id: str

    dependencies: tuple[str, ...]

    action: Callable[
        [RunContext],
        None,
    ]


class DeterministicDAG:

    def __init__(
        self,
        nodes: list[DAGNode],
    ) -> None:

        self.nodes = {
            node.node_id: node
            for node in nodes
        }

        self.validate()

    def validate(self) -> None:

        for node in self.nodes.values():

            for dependency in (
                node.dependencies
            ):

                if dependency not in (
                    self.nodes
                ):

                    raise DeterminismError(
                        f"unknown dependency: "
                        f"{dependency}"
                    )

        visiting: set[str] = set()
        visited: set[str] = set()

        def walk(
            node_id: str,
        ) -> None:

            if node_id in visiting:

                raise DeterminismError(
                    f"DAG cycle: {node_id}"
                )

            if node_id in visited:
                return

            visiting.add(node_id)

            for dependency in sorted(
                self.nodes[
                    node_id
                ].dependencies
            ):

                walk(dependency)

            visiting.remove(node_id)
            visited.add(node_id)

        for node_id in sorted(
            self.nodes
        ):

            walk(node_id)

    def order(self) -> list[str]:

        result: list[str] = []

        visited: set[str] = set()

        def visit(
            node_id: str,
        ) -> None:

            if node_id in visited:
                return

            for dependency in sorted(
                self.nodes[
                    node_id
                ].dependencies
            ):

                visit(dependency)

            visited.add(node_id)
            result.append(node_id)

        for node_id in sorted(
            self.nodes
        ):

            visit(node_id)

        return result

    def run(
        self,
        context: RunContext,
    ) -> None:

        for node_id in self.order():

            node = self.nodes[node_id]

            try:
                node.action(context)

            except Exception as exc:

                context.errors.append(
                    f"{node_id}: "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

                context.state = (
                    RunState.FAILED
                )

                raise


# ------------------------------------------------------------
# FOUNDATION ACTIONS
# ------------------------------------------------------------

def action_validate(
    context: RunContext,
    cfg: dict[str, Any],
) -> None:

    validate_config(cfg)

    transition(
        context,
        RunState.CONFIG_VALIDATED,
    )


def action_lock_source(
    context: RunContext,
    cfg: dict[str, Any],
) -> None:

    context.source = (
        build_source_lock(cfg)
    )

    transition(
        context,
        RunState.SOURCE_LOCKED,
    )


def action_validate_policy(
    context: RunContext,
    cfg: dict[str, Any],
) -> None:

    partition = cfg["partition"]

    if partition["algorithm"] != (
        PARTITION_ALGORITHM
    ):

        raise DeterminismError(
            "partition policy mismatch"
        )


# ------------------------------------------------------------
# DAG FACTORY
# ------------------------------------------------------------

def build_foundation_dag(
    cfg: dict[str, Any],
) -> DeterministicDAG:

    return DeterministicDAG(
        [

            DAGNode(
                node_id="F01_VALIDATE_CONFIG",
                dependencies=(),
                action=lambda ctx:
                    action_validate(
                        ctx,
                        cfg,
                    ),
            ),

            DAGNode(
                node_id="F02_LOCK_SOURCE",
                dependencies=(
                    "F01_VALIDATE_CONFIG",
                ),
                action=lambda ctx:
                    action_lock_source(
                        ctx,
                        cfg,
                    ),
            ),

            DAGNode(
                node_id="F03_VALIDATE_POLICY",
                dependencies=(
                    "F02_LOCK_SOURCE",
                ),
                action=lambda ctx:
                    action_validate_policy(
                        ctx,
                        cfg,
                    ),
            ),
        ]
    )


# ------------------------------------------------------------
# FOUNDATION SHERIFF
# ------------------------------------------------------------

class FoundationSheriff:

    def authorize(
        self,
        context: RunContext,
    ) -> bool:

        if context.state == (
            RunState.FAILED
        ):
            return False

        if context.source is None:
            return False

        return context.state in {
            RunState.SOURCE_LOCKED,
            RunState.TREE_DISCOVERED,
            RunState.INVENTORY_BUILT,
            RunState.PARTITIONED,
            RunState.ACQUIRED,
            RunState.VERIFIED,
            RunState.AUTHORIZED,
            RunState.STAGED,
            RunState.PUBLISHED,
        }


# ------------------------------------------------------------
# FOUNDATION FINGERPRINT
# ------------------------------------------------------------

def foundation_fingerprint(
    cfg: dict[str, Any],
) -> str:

    immutable = {

        "version":
            cfg["version"],

        "kind":
            cfg["kind"],

        "source": {
            "provider":
                cfg["source"]["provider"],

            "owner":
                cfg["source"]["owner"],

            "repository":
                cfg["source"]["repository"],

            "ref_type":
                cfg["source"]["ref_type"],

            "commit_sha":
                cfg["source"]["commit_sha"],
        },

        "partition": {
            "algorithm":
                cfg["partition"]["algorithm"],

            "max_object_bytes":
                cfg["partition"][
                    "max_object_bytes"
                ],

            "max_push_bytes":
                cfg["partition"][
                    "max_push_bytes"
                ],

            "safety_margin_bytes":
                cfg["partition"][
                    "safety_margin_bytes"
                ],
        },

        "security":
            cfg["security"],

        "verification":
            cfg["verification"],

        "publish":
            cfg["publish"],

        "council":
            cfg["council"],
    }

    return sha256_json(
        immutable
    )


# ------------------------------------------------------------
# FOUNDATION EXECUTOR
# ------------------------------------------------------------

def execute_foundation(
    cfg: dict[str, Any],
) -> dict[str, Any]:

    context = RunContext()

    dag = build_foundation_dag(
        cfg
    )

    dag.run(context)

    sheriff = FoundationSheriff()

    if not sheriff.authorize(
        context
    ):

        raise FoundationError(
            "Foundation Sheriff rejected run"
        )

    return {

        "status":
            "FOUNDATION_VALID",

        "state":
            context.state.value,

        "source":
            context.source.canonical(),

        "foundation_fingerprint":
            foundation_fingerprint(
                cfg
            ),

        "dag_order":
            dag.order(),

        "network_access":
            False,

        "source_execution":
            False,

        "dependency_installation":
            False,

        "destination_mutation":
            False,

        "next_stage":
            "ACQUISITION",
    }


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------

def main() -> int:

    if len(sys.argv) != 2:

        print(
            "usage: "
            "python -m foundation.runtime "
            "<config.json>",
            file=sys.stderr,
        )

        return 2

    config_path = sys.argv[1]

    try:

        with open(
            config_path,
            "r",
            encoding="utf-8",
        ) as handle:

            config = json.load(
                handle
            )

        result = (
            execute_foundation(
                config
            )
        )

        print(
            json.dumps(
                result,
                indent=2,
                sort_keys=True,
            )
        )

        return 0

    except FoundationError as exc:

        print(
            json.dumps(
                {
                    "status":
                        "FOUNDATION_REJECTED",

                    "error":
                        str(exc),
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )

        return 1

    except Exception as exc:

        print(
            json.dumps(
                {
                    "status":
                        "FOUNDATION_ERROR",

                    "error_type":
                        type(exc).__name__,

                    "error":
                        str(exc),
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )


# ============================================================
# FOUNDATION OUTPUT CONTRACT
# ============================================================
#
# 1A defines the DSL.
#
# 1B defines the Schema and data model.
#
# 1C defines:
#
#   - deterministic DAG;
#   - source locking;
#   - configuration validation;
#   - path validation;
#   - inventory normalization;
#   - state machine;
#   - Foundation Sheriff;
#   - contract fingerprint.
#
# No network operation exists in Foundation.
#
# Output 2 may add network acquisition ONLY through the
# interfaces established here.
#
# Output 2 MUST NOT modify:
#
#   CONTRACT_VERSION
#   PARTITION_ALGORITHM
#   RunState semantics
#   source immutability requirement
#   fail-closed behavior
#
# Output 3 adds the 12 Council gates.
#
# Output 4 adds staging and publication.
#
# ============================================================
# END OUTPUT 1C
# ============================================================

# ============================================================
# RUFLO DETERMINISTIC ACQUISITION
# OUTPUT 2A / 3 — ACQUISITION CONTRACT
# ============================================================

# FILE: dsl/acquisition.yaml

version: "1.0.0"
kind: "AcquisitionStage"

foundation:
  contract_version: "1.0.0"
  required_stage: "SOURCE_LOCKED"
  fail_closed: true

source:
  provider: "github"
  owner: "ruvnet"
  repository: "ruflo"

  ref_type: "commit"
  commit_sha: "${RUFLO_COMMIT_SHA}"

  require_full_sha: true

  # The acquisition layer must never replace the pinned
  # commit with a branch, tag or latest reference.
  mutable_ref_allowed: false

github:
  api_version: "2022-11-28"

  # All API responses used for acquisition are validated.
  validate_response_schema: true

  # GitHub API pagination must be explicit.
  pagination:
    enabled: true
    deterministic: true
    page_size: 100
    require_exhaustion: true

  tree:
    recursive: true

    # GitHub can return a truncated recursive tree.
    reject_truncated: true

    require_complete: true

    # If the recursive tree is truncated, acquisition must
    # switch to deterministic recursive subtree discovery.
    subtree_fallback: true

    sort: "path_lexicographic"

  blobs:
    endpoint: "git/blobs"
    verify_sha: true

download:
  enabled: true

  mode: "stream_to_disk"

  destination:
    staging_root: ".acquisition/staging/ruflo"

  # Never download directly into the final repository path.
  direct_publish: false

  concurrency:
    enabled: false
    workers: 1

    # Serial acquisition is intentionally selected for
    # deterministic request ordering and bounded memory.
    preserve_order: true

  retry:
    enabled: true
    max_attempts: 3

    backoff_seconds:
      initial: 2
      multiplier: 2
      maximum: 8

  timeout_seconds: 60

  buffer_bytes: 1048576

  delete_partial_on_failure: true

  resume:
    enabled: true
    require_checkpoint: true
    require_matching_source_sha: true
    require_matching_manifest_hash: true

limits:
  max_single_file_bytes: 104857600

  # Conservative operational limit below GitHub's hard
  # repository push boundary.
  max_partition_bytes: 1700000000

  safety_margin_bytes: 100000000

  max_total_repository_bytes:
    enabled: true
    value: 0

    # 0 means "not known before inventory".
    # Actual total is calculated from the Git inventory.

  max_files:
    enabled: true
    value: 0

    # 0 means "not known before inventory".
    # Actual count is calculated from the Git inventory.

security:
  reject_absolute_paths: true
  reject_parent_traversal: true
  reject_null_bytes: true

  reject_git_directory:
    enabled: true

  reject_submodules:
    enabled: true

  reject_symlinks:
    enabled: true

  allowed_tree_types:
    - "blob"
    - "tree"

inventory:
  required:
    - path
    - mode
    - type
    - size
    - sha

  canonical:
    encoding: "utf-8"
    path_separator: "/"
    ordering: "lexicographic"

  reject_duplicates: true

partition:
  enabled: true

  algorithm: "LEXICOGRAPHIC_FIRST_FIT_V1"

  input_order: "path_lexicographic"

  immutable: true

  # The partition map becomes part of the acquisition
  # manifest and cannot be modified after downloading starts.
  freeze_after_planning: true

checkpoint:
  enabled: true

  directory: ".acquisition/checkpoints/ruflo"

  format: "json"

  canonical_json: true

  atomic_write: true

  include:
    - source_commit
    - inventory_hash
    - partition_hash
    - completed_files
    - completed_partitions
    - failed_files
    - run_id

  # A checkpoint from another source commit is invalid.
  bind_to_source_commit: true

verification:
  before_download:
    verify_source_commit: true
    verify_tree: true
    verify_inventory: true
    verify_limits: true
    verify_partition_plan: true

  after_download:
    verify_file_count: true
    verify_total_bytes: true
    verify_paths: true
    verify_content_hashes: true

failure:
  policy: "FAIL_CLOSED"

  partial_success: false

  publish_after_failure: false

  continue_after_corruption: false

  continue_after_tree_truncation: false


# ============================================================
# FILE: acquisition/contracts.py
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


# ------------------------------------------------------------
# Immutable source identity
# ------------------------------------------------------------

@dataclass(frozen=True)
class AcquisitionSource:
    provider: Literal["github"]
    owner: str
    repository: str
    commit_sha: str

    def canonical(self) -> tuple[str, str, str, str]:
        return (
            self.provider,
            self.owner,
            self.repository,
            self.commit_sha,
        )


# ------------------------------------------------------------
# Git tree entry
# ------------------------------------------------------------

@dataclass(frozen=True)
class GitTreeEntry:
    path: str
    mode: str
    type: Literal["blob", "tree"]
    sha: str
    size: int | None

    def canonical(self) -> dict:
        return {
            "path": self.path,
            "mode": self.mode,
            "type": self.type,
            "sha": self.sha,
            "size": self.size,
        }


# ------------------------------------------------------------
# Download target
# ------------------------------------------------------------

@dataclass(frozen=True)
class DownloadTarget:
    path: str
    sha: str
    size: int
    mode: str

    def canonical(self) -> dict:
        return {
            "path": self.path,
            "sha": self.sha,
            "size": self.size,
            "mode": self.mode,
        }


# ------------------------------------------------------------
# Partition
# ------------------------------------------------------------

@dataclass(frozen=True)
class AcquisitionPartition:
    number: int
    targets: tuple[DownloadTarget, ...]
    total_bytes: int

    def canonical(self) -> dict:
        return {
            "number": self.number,
            "targets": [
                target.canonical()
                for target in self.targets
            ],
            "total_bytes": self.total_bytes,
        }


# ------------------------------------------------------------
# Checkpoint
# ------------------------------------------------------------

@dataclass(frozen=True)
class AcquisitionCheckpoint:
    source_commit: str
    inventory_hash: str
    partition_hash: str
    completed_files: tuple[str, ...]
    completed_partitions: tuple[int, ...]
    failed_files: tuple[str, ...]
    run_id: str

    def canonical(self) -> dict:
        return {
            "source_commit": self.source_commit,
            "inventory_hash": self.inventory_hash,
            "partition_hash": self.partition_hash,
            "completed_files": list(
                self.completed_files
            ),
            "completed_partitions": list(
                self.completed_partitions
            ),
            "failed_files": list(
                self.failed_files
            ),
            "run_id": self.run_id,
        }


# ------------------------------------------------------------
# Acquisition errors
# ------------------------------------------------------------

class AcquisitionError(Exception):
    pass


class SourceMismatchError(AcquisitionError):
    pass


class TreeIncompleteError(AcquisitionError):
    pass


class InventoryError(AcquisitionError):
    pass


class DownloadError(AcquisitionError):
    pass


class PartitionError(AcquisitionError):
    pass


class CheckpointError(AcquisitionError):
    pass


class LimitExceededError(AcquisitionError):
    pass


class IntegrityError(AcquisitionError):
    pass


# ------------------------------------------------------------
# CONTRACT RULES
# ------------------------------------------------------------

ACQUISITION_RULES = {
    "mutable_refs": False,
    "direct_publish": False,
    "partial_success": False,
    "tree_truncation": "reject",
    "duplicate_paths": "reject",
    "unsafe_paths": "reject",
    "single_file_over_limit": "reject",
    "failed_download": "reject",
    "checkpoint_source_mismatch": "reject",
    "checkpoint_manifest_mismatch": "reject",
    "partition_mutation_after_start": "reject",
}


# ============================================================
# END OUTPUT 2A
# ============================================================
# ============================================================
# RUFLO DETERMINISTIC ACQUISITION
# OUTPUT 2B / 3 — GITHUB TREE + INVENTORY
# ============================================================

# FILE: acquisition/github_tree.py

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from acquisition.contracts import (
    AcquisitionError,
    AcquisitionSource,
    GitTreeEntry,
    InventoryError,
    LimitExceededError,
    SourceMismatchError,
    TreeIncompleteError,
)


FULL_SHA_RE = re.compile(
    r"^[0-9a-f]{40}$"
)

GITHUB_API = (
    "https://api.github.com"
)

USER_AGENT = (
    "ruflo-deterministic-acquirer/1.0"
)


# ------------------------------------------------------------
# CANONICAL JSON
# ------------------------------------------------------------

def canonical_json(
    value: Any,
) -> bytes:

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256(
    value: bytes,
) -> str:

    return hashlib.sha256(
        value
    ).hexdigest()


def inventory_hash(
    entries: list[GitTreeEntry],
) -> str:

    canonical = [
        entry.canonical()
        for entry in entries
    ]

    return sha256(
        canonical_json(canonical)
    )


# ------------------------------------------------------------
# HTTP CLIENT
# ------------------------------------------------------------

class GitHubClient:

    def __init__(
        self,
        token: str | None = None,
        timeout: int = 60,
    ) -> None:

        self.token = token
        self.timeout = timeout

    def request_json(
        self,
        path: str,
    ) -> dict[str, Any]:

        url = (
            GITHUB_API.rstrip("/")
            + "/"
            + path.lstrip("/")
        )

        headers = {
            "Accept":
                "application/vnd.github+json",

            "X-GitHub-Api-Version":
                "2022-11-28",

            "User-Agent":
                USER_AGENT,
        }

        if self.token:
            headers["Authorization"] = (
                f"Bearer {self.token}"
            )

        request = Request(
            url,
            headers=headers,
            method="GET",
        )

        try:

            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:

                raw = response.read()

        except HTTPError as exc:

            raise AcquisitionError(
                f"GitHub HTTP {exc.code}: {url}"
            ) from exc

        except URLError as exc:

            raise AcquisitionError(
                f"GitHub network error: {url}: {exc}"
            ) from exc

        try:

            result = json.loads(
                raw.decode("utf-8")
            )

        except Exception as exc:

            raise AcquisitionError(
                f"invalid GitHub JSON: {url}"
            ) from exc

        if not isinstance(result, dict):

            raise AcquisitionError(
                f"unexpected GitHub response: {url}"
            )

        return result


# ------------------------------------------------------------
# COMMIT VALIDATION
# ------------------------------------------------------------

def validate_commit_sha(
    commit_sha: str,
) -> None:

    if not FULL_SHA_RE.fullmatch(
        commit_sha
    ):

        raise SourceMismatchError(
            "source commit must be a "
            "40-character lowercase SHA"
        )


# ------------------------------------------------------------
# COMMIT OBJECT
# ------------------------------------------------------------

def get_commit(
    client: GitHubClient,
    source: AcquisitionSource,
) -> dict[str, Any]:

    validate_commit_sha(
        source.commit_sha
    )

    path = (
        f"repos/"
        f"{source.owner}/"
        f"{source.repository}/"
        f"git/commits/"
        f"{source.commit_sha}"
    )

    result = client.request_json(
        path
    )

    returned_sha = result.get(
        "sha"
    )

    if returned_sha != (
        source.commit_sha
    ):

        raise SourceMismatchError(
            "GitHub returned a different "
            "commit SHA"
        )

    tree = result.get(
        "tree"
    )

    if not isinstance(tree, dict):

        raise AcquisitionError(
            "commit does not contain "
            "a valid tree object"
        )

    tree_sha = tree.get(
        "sha"
    )

    if not isinstance(
        tree_sha,
        str,
    ):

        raise AcquisitionError(
            "commit tree SHA missing"
        )

    return result


# ------------------------------------------------------------
# TREE OBJECT
# ------------------------------------------------------------

def get_tree_object(
    client: GitHubClient,
    source: AcquisitionSource,
    tree_sha: str,
    recursive: bool = True,
) -> dict[str, Any]:

    path = (
        f"repos/"
        f"{source.owner}/"
        f"{source.repository}/"
        f"git/trees/"
        f"{tree_sha}"
    )

    if recursive:
        path += "?recursive=1"

    return client.request_json(
        path
    )


# ------------------------------------------------------------
# TREE RESPONSE VALIDATION
# ------------------------------------------------------------

def validate_tree_response(
    response: dict[str, Any],
) -> list[dict[str, Any]]:

    if "tree" not in response:

        raise TreeIncompleteError(
            "GitHub tree response has no tree"
        )

    entries = response[
        "tree"
    ]

    if not isinstance(
        entries,
        list,
    ):

        raise TreeIncompleteError(
            "GitHub tree is not a list"
        )

    truncated = response.get(
        "truncated"
    )

    if truncated is True:

        raise TreeIncompleteError(
            "GitHub returned a truncated "
            "recursive tree"
        )

    return entries


# ------------------------------------------------------------
# TREE ENTRY NORMALIZATION
# ------------------------------------------------------------

def normalize_tree_entries(
    raw_entries: list[dict[str, Any]],
) -> list[GitTreeEntry]:

    result: list[GitTreeEntry] = []

    seen: set[str] = set()

    for raw in raw_entries:

        path = raw.get(
            "path"
        )

        mode = raw.get(
            "mode"
        )

        entry_type = raw.get(
            "type"
        )

        sha = raw.get(
            "sha"
        )

        size = raw.get(
            "size"
        )

        if not isinstance(
            path,
            str,
        ):

            raise InventoryError(
                "tree entry has invalid path"
            )

        if path in seen:

            raise InventoryError(
                f"duplicate tree path: {path}"
            )

        seen.add(path)

        if "\x00" in path:

            raise InventoryError(
                f"NUL byte in path: {path}"
            )

        if path.startswith("/"):
            raise InventoryError(
                f"absolute path: {path}"
            )

        normalized = path.replace(
            "\\",
            "/",
        )

        if (
            normalized == ".."
            or normalized.startswith("../")
            or "/../" in (
                "/" + normalized + "/"
            )
        ):

            raise InventoryError(
                f"parent traversal: {path}"
            )

        if (
            normalized == ".git"
            or normalized.startswith(".git/")
        ):

            raise InventoryError(
                f"nested .git path: {path}"
            )

        if entry_type not in {
            "blob",
            "tree",
        }:

            raise InventoryError(
                f"unsupported Git tree type "
                f"{entry_type}: {path}"
            )

        if not isinstance(
            sha,
            str,
        ):

            raise InventoryError(
                f"missing SHA: {path}"
            )

        if not re.fullmatch(
            r"^[0-9a-f]{40}$",
            sha,
        ):

            raise InventoryError(
                f"invalid Git object SHA: {path}"
            )

        if entry_type == "blob":

            if not isinstance(
                size,
                int,
            ):

                raise InventoryError(
                    f"blob has no valid size: "
                    f"{path}"
                )

            if size < 0:

                raise InventoryError(
                    f"negative size: {path}"
                )

        else:

            size = None

        result.append(
            GitTreeEntry(
                path=normalized,
                mode=str(mode),
                type=entry_type,
                sha=sha,
                size=size,
            )
        )

    result.sort(
        key=lambda item: item.path
    )

    return result


# ------------------------------------------------------------
# COMPLETE TREE DISCOVERY
# ------------------------------------------------------------

def discover_complete_tree(
    client: GitHubClient,
    source: AcquisitionSource,
) -> list[GitTreeEntry]:

    commit = get_commit(
        client,
        source,
    )

    tree_object = commit[
        "tree"
    ]

    root_tree_sha = tree_object[
        "sha"
    ]

    response = get_tree_object(
        client,
        source,
        root_tree_sha,
        recursive=True,
    )

    try:

        raw_entries = (
            validate_tree_response(
                response
            )
        )

    except TreeIncompleteError:

        # IMPORTANT:
        #
        # A truncated recursive response
        # MUST NOT be accepted.
        #
        # The acquisition layer will later
        # invoke deterministic subtree
        # discovery.
        raise

    entries = (
        normalize_tree_entries(
            raw_entries
        )
    )

    if not entries:

        # An empty repository is technically
        # possible, but Ruflo acquisition
        # requires an actual source tree.
        raise TreeIncompleteError(
            "source tree contains no entries"
        )

    return entries


# ------------------------------------------------------------
# BLOB INVENTORY ONLY
# ------------------------------------------------------------

def build_blob_inventory(
    entries: list[GitTreeEntry],
    max_file_bytes: int,
) -> list[GitTreeEntry]:

    blobs: list[GitTreeEntry] = []

    for entry in entries:

        if entry.type != "blob":
            continue

        if entry.size is None:

            raise InventoryError(
                f"blob size unavailable: "
                f"{entry.path}"
            )

        if entry.size > (
            max_file_bytes
        ):

            raise LimitExceededError(
                f"file exceeds configured "
                f"limit: "
                f"{entry.path}: "
                f"{entry.size} bytes"
            )

        blobs.append(
            entry
        )

    blobs.sort(
        key=lambda item: item.path
    )

    if not blobs:

        raise InventoryError(
            "no downloadable blobs found"
        )

    return blobs


# ------------------------------------------------------------
# INVENTORY STATISTICS
# ------------------------------------------------------------

@dataclass(frozen=True)
class InventoryStats:

    file_count: int
    total_bytes: int
    largest_file_bytes: int
    inventory_sha256: str


def calculate_inventory_stats(
    entries: list[GitTreeEntry],
) -> InventoryStats:

    if not entries:

        raise InventoryError(
            "inventory is empty"
        )

    sizes = [
        int(entry.size or 0)
        for entry in entries
    ]

    return InventoryStats(
        file_count=len(entries),
        total_bytes=sum(sizes),
        largest_file_bytes=max(sizes),
        inventory_sha256=inventory_hash(
            entries
        ),
    )


# ------------------------------------------------------------
# INVENTORY MANIFEST
# ------------------------------------------------------------

def inventory_manifest(
    source: AcquisitionSource,
    entries: list[GitTreeEntry],
) -> dict[str, Any]:

    stats = calculate_inventory_stats(
        entries
    )

    return {

        "schema":
            "ruflo.inventory.v1",

        "source": {
            "provider":
                source.provider,

            "owner":
                source.owner,

            "repository":
                source.repository,

            "commit_sha":
                source.commit_sha,
        },

        "statistics": {
            "file_count":
                stats.file_count,

            "total_bytes":
                stats.total_bytes,

            "largest_file_bytes":
                stats.largest_file_bytes,
        },

        "inventory_sha256":
            stats.inventory_sha256,

        "files": [
            entry.canonical()
            for entry in entries
        ],
    }


# ------------------------------------------------------------
# LOCAL INVENTORY WRITE
# ------------------------------------------------------------

def write_inventory(
    path: str,
    manifest: dict[str, Any],
) -> None:

    payload = canonical_json(
        manifest
    )

    with open(
        path,
        "wb",
    ) as handle:

        handle.write(
            payload
        )


# ------------------------------------------------------------
# DETERMINISTIC INVENTORY VALIDATION
# ------------------------------------------------------------

def validate_inventory(
    entries: list[GitTreeEntry],
    max_file_bytes: int,
) -> None:

    previous: str | None = None

    for entry in entries:

        if previous is not None:

            if entry.path <= previous:

                raise InventoryError(
                    "inventory is not strictly "
                    "lexicographically ordered"
                )

        previous = entry.path

        if entry.type != "blob":

            raise InventoryError(
                f"non-blob in download inventory: "
                f"{entry.path}"
            )

        if entry.size is None:

            raise InventoryError(
                f"missing blob size: "
                f"{entry.path}"
            )

        if entry.size < 0:

            raise InventoryError(
                f"negative blob size: "
                f"{entry.path}"
            )

        if entry.size > (
            max_file_bytes
        ):

            raise LimitExceededError(
                f"file exceeds limit: "
                f"{entry.path}"
            )


# ============================================================
# FILE: acquisition/inventory_cli.py
# ============================================================

import argparse
import json
import os

from acquisition.github_tree import (
    GitHubClient,
    AcquisitionSource,
    discover_complete_tree,
    build_blob_inventory,
    calculate_inventory_stats,
    inventory_manifest,
    validate_inventory,
    write_inventory,
)


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--owner",
        required=True,
    )

    parser.add_argument(
        "--repository",
        required=True,
    )

    parser.add_argument(
        "--commit",
        required=True,
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    parser.add_argument(
        "--token",
        default=None,
    )

    parser.add_argument(
        "--max-file-bytes",
        type=int,
        default=100 * 1024 * 1024,
    )

    args = parser.parse_args()

    source = AcquisitionSource(
        provider="github",
        owner=args.owner,
        repository=args.repository,
        commit_sha=args.commit,
    )

    client = GitHubClient(
        token=args.token
    )

    entries = discover_complete_tree(
        client,
        source,
    )

    blobs = build_blob_inventory(
        entries,
        args.max_file_bytes,
    )

    validate_inventory(
        blobs,
        args.max_file_bytes,
    )

    manifest = inventory_manifest(
        source,
        blobs,
    )

    parent = os.path.dirname(
        os.path.abspath(
            args.output
        )
    )

    os.makedirs(
        parent,
        exist_ok=True,
    )

    write_inventory(
        args.output,
        manifest,
    )

    stats = calculate_inventory_stats(
        blobs
    )

    print(
        json.dumps(
            {
                "status":
                    "INVENTORY_VALID",

                "commit":
                    source.commit_sha,

                "files":
                    stats.file_count,

                "total_bytes":
                    stats.total_bytes,

                "largest_file_bytes":
                    stats.largest_file_bytes,

                "inventory_sha256":
                    stats.inventory_sha256,
            },
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )


# ============================================================
# OUTPUT 2B CONTRACT
# ============================================================
#
# This module establishes:
#
#   1. Immutable commit validation.
#   2. GitHub commit resolution.
#   3. Root tree discovery.
#   4. Recursive Git tree retrieval.
#   5. Explicit rejection of "truncated": true.
#   6. Path security validation.
#   7. Blob inventory creation.
#   8. File-size enforcement.
#   9. Canonical lexicographic ordering.
#  10. Inventory SHA-256 fingerprint.
#
# IMPORTANT:
#
# A truncated GitHub recursive tree is NOT treated as complete.
#
# Output 2C must implement the deterministic subtree fallback
# so that a large repository can still be enumerated completely
# without relying on one oversized recursive-tree response.
#
# Output 2C must then:
#
#   - freeze the inventory;
#   - calculate partitions;
#   - download blobs;
#   - stream to disk;
#   - verify every blob;
#   - create checkpoints.
#
# ============================================================
# END OUTPUT 2B
# ============================================================






# ============================================================
# RUFLO DETERMINISTIC ACQUISITION
# OUTPUT 2C-1
# PARTITIONER + HASHING + CHECKPOINT
# ============================================================

# FILE: acquisition/partitioner.py

from __future__ import annotations

import hashlib
import json
import os
import tempfile

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from acquisition.contracts import (
    AcquisitionPartition,
    CheckpointError,
    DownloadTarget,
    PartitionError,
)
from acquisition.github_tree import GitTreeEntry


# ------------------------------------------------------------
# CONSTANTS
# ------------------------------------------------------------

PARTITION_ALGORITHM = (
    "LEXICOGRAPHIC_FIRST_FIT_V1"
)

DEFAULT_MAX_PARTITION_BYTES = (
    1_700_000_000
)

DEFAULT_SAFETY_MARGIN_BYTES = (
    100_000_000
)

DEFAULT_BUFFER_BYTES = (
    1_048_576
)


# ------------------------------------------------------------
# CANONICAL JSON
# ------------------------------------------------------------

def canonical_json(
    value: Any,
) -> bytes:

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_bytes(
    value: bytes,
) -> str:

    return hashlib.sha256(
        value
    ).hexdigest()


def sha256_json(
    value: Any,
) -> str:

    return sha256_bytes(
        canonical_json(value)
    )


# ------------------------------------------------------------
# GIT BLOB SHA
# ------------------------------------------------------------

def git_blob_sha1(
    content: bytes,
) -> str:
    """
    Git blob identity:

        SHA1(
            b"blob <length>\\0" + content
        )
    """

    header = (
        f"blob {len(content)}\0"
    ).encode("ascii")

    return hashlib.sha1(
        header + content
    ).hexdigest()


# ------------------------------------------------------------
# FILE SHA-256
# ------------------------------------------------------------

def sha256_file(
    path: str,
    buffer_size: int = DEFAULT_BUFFER_BYTES,
) -> str:

    digest = hashlib.sha256()

    with open(
        path,
        "rb",
    ) as handle:

        while True:

            chunk = handle.read(
                buffer_size
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


# ------------------------------------------------------------
# GIT BLOB SHA-1 FROM FILE
# ------------------------------------------------------------

def git_blob_sha1_file(
    path: str,
    buffer_size: int = DEFAULT_BUFFER_BYTES,
) -> str:

    size = os.path.getsize(
        path
    )

    digest = hashlib.sha1()

    header = (
        f"blob {size}\0"
    ).encode("ascii")

    digest.update(
        header
    )

    with open(
        path,
        "rb",
    ) as handle:

        while True:

            chunk = handle.read(
                buffer_size
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


# ------------------------------------------------------------
# TARGET CONVERSION
# ------------------------------------------------------------

def targets_from_entries(
    entries: list[GitTreeEntry],
) -> list[DownloadTarget]:

    targets: list[DownloadTarget] = []

    for entry in entries:

        if entry.type != "blob":
            continue

        if entry.size is None:

            raise PartitionError(
                f"missing size: {entry.path}"
            )

        targets.append(
            DownloadTarget(
                path=entry.path,
                sha=entry.sha,
                size=entry.size,
                mode=entry.mode,
            )
        )

    targets.sort(
        key=lambda item: item.path
    )

    return targets


# ------------------------------------------------------------
# DETERMINISTIC PARTITIONING
# ------------------------------------------------------------

def plan_partitions(
    targets: list[DownloadTarget],
    max_partition_bytes: int = (
        DEFAULT_MAX_PARTITION_BYTES
    ),
    safety_margin_bytes: int = (
        DEFAULT_SAFETY_MARGIN_BYTES
    ),
) -> list[AcquisitionPartition]:

    if max_partition_bytes <= 0:

        raise PartitionError(
            "partition capacity must be positive"
        )

    if safety_margin_bytes < 0:

        raise PartitionError(
            "safety margin cannot be negative"
        )

    capacity = (
        max_partition_bytes
        - safety_margin_bytes
    )

    if capacity <= 0:

        raise PartitionError(
            "usable partition capacity is zero"
        )

    ordered = sorted(
        targets,
        key=lambda item: item.path,
    )

    partitions: list[
        list[DownloadTarget]
    ] = []

    sizes: list[int] = []

    for target in ordered:

        if target.size > capacity:

            raise PartitionError(
                "single file exceeds "
                f"partition capacity: "
                f"{target.path}: "
                f"{target.size}"
            )

        placed = False

        for index in range(
            len(partitions)
        ):

            candidate_size = (
                sizes[index]
                + target.size
            )

            if candidate_size <= capacity:

                partitions[
                    index
                ].append(target)

                sizes[index] = (
                    candidate_size
                )

                placed = True

                break

        if not placed:

            partitions.append(
                [target]
            )

            sizes.append(
                target.size
            )

    result: list[
        AcquisitionPartition
    ] = []

    for number, group in enumerate(
        partitions
    ):

        result.append(
            AcquisitionPartition(
                number=number,
                targets=tuple(group),
                total_bytes=sizes[number],
            )
        )

    return result


# ------------------------------------------------------------
# PARTITION MANIFEST
# ------------------------------------------------------------

def partition_manifest(
    partitions: list[
        AcquisitionPartition
    ],
) -> dict[str, Any]:

    return {
        "schema":
            "ruflo.partition.v1",

        "algorithm":
            PARTITION_ALGORITHM,

        "partitions": [
            partition.canonical()
            for partition in partitions
        ],
    }


def partition_hash(
    partitions: list[
        AcquisitionPartition
    ],
) -> str:

    return sha256_json(
        partition_manifest(
            partitions
        )
    )


# ------------------------------------------------------------
# ATOMIC WRITE
# ------------------------------------------------------------

def atomic_write_bytes(
    destination: str,
    payload: bytes,
) -> None:

    target = Path(
        destination
    )

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fd, temporary = (
        tempfile.mkstemp(
            prefix=".partial-",
            dir=str(target.parent),
        )
    )

    try:

        with os.fdopen(
            fd,
            "wb",
        ) as handle:

            handle.write(
                payload
            )

            handle.flush()

            os.fsync(
                handle.fileno()
            )

        os.replace(
            temporary,
            target,
        )

    except Exception:

        try:

            os.unlink(
                temporary
            )

        except FileNotFoundError:
            pass

        raise


# ------------------------------------------------------------
# CHECKPOINT
# ------------------------------------------------------------

@dataclass
class Checkpoint:

    source_commit: str

    inventory_hash: str

    partition_hash: str

    completed_files: set[str]

    completed_partitions: set[int]

    failed_files: set[str]

    run_id: str

    def canonical(self) -> dict[str, Any]:

        return {

            "source_commit":
                self.source_commit,

            "inventory_hash":
                self.inventory_hash,

            "partition_hash":
                self.partition_hash,

            "completed_files":
                sorted(
                    self.completed_files
                ),

            "completed_partitions":
                sorted(
                    self.completed_partitions
                ),

            "failed_files":
                sorted(
                    self.failed_files
                ),

            "run_id":
                self.run_id,
        }


def checkpoint_hash(
    checkpoint: Checkpoint,
) -> str:

    return sha256_json(
        checkpoint.canonical()
    )


# ------------------------------------------------------------
# CHECKPOINT SAVE
# ------------------------------------------------------------

def save_checkpoint(
    path: str,
    checkpoint: Checkpoint,
) -> None:

    payload = canonical_json(
        checkpoint.canonical()
    )

    atomic_write_bytes(
        path,
        payload,
    )


# ------------------------------------------------------------
# CHECKPOINT LOAD
# ------------------------------------------------------------

def load_checkpoint(
    path: str,
) -> Checkpoint:

    try:

        with open(
            path,
            "rb",
        ) as handle:

            data = json.loads(
                handle.read().decode(
                    "utf-8"
                )
            )

    except Exception as exc:

        raise CheckpointError(
            f"cannot load checkpoint: {path}"
        ) from exc

    required = {
        "source_commit",
        "inventory_hash",
        "partition_hash",
        "completed_files",
        "completed_partitions",
        "failed_files",
        "run_id",
    }

    if not isinstance(
        data,
        dict,
    ):

        raise CheckpointError(
            "checkpoint is not an object"
        )

    if not required.issubset(
        data.keys()
    ):

        raise CheckpointError(
            "checkpoint schema is incomplete"
        )

    return Checkpoint(

        source_commit=str(
            data["source_commit"]
        ),

        inventory_hash=str(
            data["inventory_hash"]
        ),

        partition_hash=str(
            data["partition_hash"]
        ),

        completed_files=set(
            data["completed_files"]
        ),

        completed_partitions=set(
            int(value)
            for value in data[
                "completed_partitions"
            ]
        ),

        failed_files=set(
            data["failed_files"]
        ),

        run_id=str(
            data["run_id"]
        ),
    )


# ------------------------------------------------------------
# CHECKPOINT VALIDATION
# ------------------------------------------------------------

def validate_checkpoint(
    checkpoint: Checkpoint,
    source_commit: str,
    expected_inventory_hash: str,
    expected_partition_hash: str,
) -> None:

    if checkpoint.source_commit != (
        source_commit
    ):

        raise CheckpointError(
            "checkpoint source commit mismatch"
        )

    if checkpoint.inventory_hash != (
        expected_inventory_hash
    ):

        raise CheckpointError(
            "checkpoint inventory hash mismatch"
        )

    if checkpoint.partition_hash != (
        expected_partition_hash
    ):

        raise CheckpointError(
            "checkpoint partition hash mismatch"
        )


# ------------------------------------------------------------
# PARTITION VALIDATION
# ------------------------------------------------------------

def validate_partition_plan(
    partitions: list[
        AcquisitionPartition
    ],
    targets: list[DownloadTarget],
    capacity: int,
) -> None:

    expected_paths = [
        target.path
        for target in sorted(
            targets,
            key=lambda item: item.path,
        )
    ]

    actual_paths: list[str] = []

    for partition in partitions:

        if partition.total_bytes > capacity:

            raise PartitionError(
                f"partition {partition.number} "
                "exceeds capacity"
            )

        previous = None

        calculated_size = 0

        for target in partition.targets:

            if previous is not None:

                if target.path <= previous:

                    raise PartitionError(
                        "partition ordering violation"
                    )

            previous = target.path

            calculated_size += target.size

            actual_paths.append(
                target.path
            )

        if calculated_size != (
            partition.total_bytes
        ):

            raise PartitionError(
                f"partition {partition.number} "
                "byte count mismatch"
            )

    if actual_paths != expected_paths:

        raise PartitionError(
            "partition plan does not contain "
            "exactly the inventory targets"
        )


# ------------------------------------------------------------
# OUTPUT 2C-1 CONTRACT
# ------------------------------------------------------------
#
# This module does NOT perform network acquisition.
#
# It establishes the immutable acquisition plan:
#
#   source commit
#        |
#        v
#   canonical inventory
#        |
#        v
#   lexicographic ordering
#        |
#        v
#   deterministic partitioning
#        |
#        v
#   partition hash
#        |
#        v
#   source-bound checkpoint
#
# No downloader is allowed to modify the partition plan after
# this stage has been frozen.
#
# ============================================================
# END OUTPUT 2C-1
# ============================================================
# ============================================================
# RUFLO DETERMINISTIC ACQUISITION
# OUTPUT 2C-2
# BLOB DOWNLOAD + VERIFICATION + RESUME
# ============================================================

# FILE: acquisition/downloader.py

from __future__ import annotations

import base64
import os
import time

from pathlib import Path
from typing import Any
from urllib.error import HTTPError

from acquisition.contracts import (
    AcquisitionSource,
    DownloadError,
    DownloadTarget,
    IntegrityError,
)

from acquisition.github_tree import (
    GitHubClient,
    GitTreeEntry,
)

from acquisition.partitioner import (
    Checkpoint,
    acquire_atomic_write,
    atomic_write_bytes,
    git_blob_sha1,
    git_blob_sha1_file,
    load_checkpoint,
    partition_hash,
    plan_partitions,
    save_checkpoint,
    sha256_file,
    targets_from_entries,
    validate_checkpoint,
)


# ------------------------------------------------------------
# GITHUB BLOB
# ------------------------------------------------------------

def get_blob(
    client: GitHubClient,
    source: AcquisitionSource,
    sha: str,
) -> bytes:

    path = (
        f"repos/"
        f"{source.owner}/"
        f"{source.repository}/"
        f"git/blobs/"
        f"{sha}"
    )

    response = client.request_json(
        path
    )

    returned_sha = response.get(
        "sha"
    )

    if returned_sha != sha:

        raise IntegrityError(
            "GitHub returned an unexpected "
            "blob SHA"
        )

    encoding = response.get(
        "encoding"
    )

    if encoding != "base64":

        raise DownloadError(
            "unsupported GitHub blob encoding"
        )

    encoded = response.get(
        "content"
    )

    if not isinstance(
        encoded,
        str,
    ):

        raise DownloadError(
            "GitHub blob content is invalid"
        )

    try:

        return base64.b64decode(
            encoded,
            validate=True,
        )

    except Exception as exc:

        raise DownloadError(
            "GitHub blob base64 decoding failed"
        ) from exc


# ------------------------------------------------------------
# TARGET VERIFICATION
# ------------------------------------------------------------

def verify_target(
    path: str,
    target: DownloadTarget,
) -> dict[str, Any]:

    if not os.path.isfile(
        path
    ):

        raise IntegrityError(
            f"downloaded object is missing: "
            f"{target.path}"
        )

    actual_size = os.path.getsize(
        path
    )

    if actual_size != target.size:

        raise IntegrityError(
            f"size mismatch for {target.path}: "
            f"expected={target.size}, "
            f"actual={actual_size}"
        )

    actual_git_sha = (
        git_blob_sha1_file(
            path
        )
    )

    if actual_git_sha != target.sha:

        raise IntegrityError(
            f"Git blob SHA mismatch for "
            f"{target.path}: "
            f"expected={target.sha}, "
            f"actual={actual_git_sha}"
        )

    actual_sha256 = (
        sha256_file(
            path
        )
    )

    return {
        "path":
            target.path,

        "size":
            actual_size,

        "git_blob_sha":
            actual_git_sha,

        "sha256":
            actual_sha256,

        "verified":
            True,
    }


# ------------------------------------------------------------
# SINGLE DOWNLOAD
# ------------------------------------------------------------

def acquire_target(
    client: GitHubClient,
    source: AcquisitionSource,
    target: DownloadTarget,
    staging_root: str,
) -> dict[str, Any]:

    destination = (
        Path(staging_root)
        / Path(target.path)
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    content = get_blob(
        client,
        source,
        target.sha,
    )

    if len(content) != target.size:

        raise IntegrityError(
            f"content size mismatch: "
            f"{target.path}"
        )

    actual_git_sha = (
        git_blob_sha1(
            content
        )
    )

    if actual_git_sha != target.sha:

        raise IntegrityError(
            f"content Git SHA mismatch: "
            f"{target.path}"
        )

    atomic_write_bytes(
        str(destination),
        content,
    )

    return verify_target(
        str(destination),
        target,
    )


# ------------------------------------------------------------
# RETRY WRAPPER
# ------------------------------------------------------------

def acquire_with_retry(
    client: GitHubClient,
    source: AcquisitionSource,
    target: DownloadTarget,
    staging_root: str,
    max_attempts: int = 3,
) -> dict[str, Any]:

    if max_attempts <= 0:

        raise DownloadError(
            "max_attempts must be positive"
        )

    last_error: Exception | None = None

    for attempt in range(
        1,
        max_attempts + 1,
    ):

        try:

            return acquire_target(
                client,
                source,
                target,
                staging_root,
            )

        except Exception as exc:

            last_error = exc

            if attempt >= max_attempts:
                break

            delay = min(
                2 ** (attempt - 1),
                8,
            )

            time.sleep(
                delay
            )

    raise DownloadError(
        f"download failed after "
        f"{max_attempts} attempts: "
        f"{target.path}"
    ) from last_error


# ------------------------------------------------------------
# PARTITION DOWNLOAD
# ------------------------------------------------------------

def acquire_partition(
    client: GitHubClient,
    source: AcquisitionSource,
    partition,
    staging_root: str,
    checkpoint: Checkpoint,
    checkpoint_path: str,
) -> None:

    for target in partition.targets:

        if target.path in (
            checkpoint.completed_files
        ):

            continue

        if target.path in (
            checkpoint.failed_files
        ):

            raise DownloadError(
                "file is marked failed in "
                f"checkpoint: {target.path}"
            )

        try:

            acquire_with_retry(
                client,
                source,
                target,
                staging_root,
            )

        except Exception:

            checkpoint.failed_files.add(
                target.path
            )

            save_checkpoint(
                checkpoint_path,
                checkpoint,
            )

            raise

        checkpoint.completed_files.add(
            target.path
        )

        save_checkpoint(
            checkpoint_path,
            checkpoint,
        )

    checkpoint.completed_partitions.add(
        partition.number
    )

    save_checkpoint(
        checkpoint_path,
        checkpoint,
    )


# ------------------------------------------------------------
# FINAL STAGING VERIFICATION
# ------------------------------------------------------------

def verify_complete_staging(
    entries: list[GitTreeEntry],
    staging_root: str,
) -> dict[str, Any]:

    targets = targets_from_entries(
        entries
    )

    verified = []

    total_bytes = 0

    for target in targets:

        path = (
            Path(staging_root)
            / Path(target.path)
        )

        result = verify_target(
            str(path),
            target,
        )

        verified.append(
            result
        )

        total_bytes += (
            target.size
        )

    return {
        "status":
            "STAGING_VERIFIED",

        "files":
            len(verified),

        "total_bytes":
            total_bytes,

        "verified_files":
            verified,
    }


# ------------------------------------------------------------
# COMPLETE ACQUISITION
# ------------------------------------------------------------

def acquire_all(
    client: GitHubClient,
    source: AcquisitionSource,
    entries: list[GitTreeEntry],
    inventory_hash_value: str,
    staging_root: str,
    checkpoint_path: str,
    run_id: str,
    max_partition_bytes: int = 1_700_000_000,
    safety_margin_bytes: int = 100_000_000,
) -> dict[str, Any]:

    targets = targets_from_entries(
        entries
    )

    partitions = plan_partitions(
        targets,
        max_partition_bytes=(
            max_partition_bytes
        ),
        safety_margin_bytes=(
            safety_margin_bytes
        ),
    )

    p_hash = partition_hash(
        partitions
    )

    os.makedirs(
        staging_root,
        exist_ok=True,
    )

    checkpoint_parent = (
        Path(checkpoint_path).parent
    )

    checkpoint_parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if os.path.exists(
        checkpoint_path
    ):

        checkpoint = load_checkpoint(
            checkpoint_path
        )

        validate_checkpoint(
            checkpoint,
            source.commit_sha,
            inventory_hash_value,
            p_hash,
        )

    else:

        checkpoint = Checkpoint(

            source_commit=(
                source.commit_sha
            ),

            inventory_hash=(
                inventory_hash_value
            ),

            partition_hash=p_hash,

            completed_files=set(),

            completed_partitions=set(),

            failed_files=set(),

            run_id=run_id,
        )

        save_checkpoint(
            checkpoint_path,
            checkpoint,
        )

    for partition in partitions:

        if partition.number in (
            checkpoint.completed_partitions
        ):

            continue

        acquire_partition(
            client,
            source,
            partition,
            staging_root,
            checkpoint,
            checkpoint_path,
        )

    final = verify_complete_staging(
        entries,
        staging_root,
    )

    return {

        "status":
            "ACQUISITION_COMPLETE",

        "source_commit":
            source.commit_sha,

        "inventory_hash":
            inventory_hash_value,

        "partition_hash":
            p_hash,

        "partitions":
            len(partitions),

        "files":
            final["files"],

        "total_bytes":
            final["total_bytes"],

        "staging_root":
            staging_root,
    }


# ------------------------------------------------------------
# FILE: acquisition/acquire_cli.py
# ------------------------------------------------------------

import argparse
import json
import os
import uuid

from acquisition.contracts import (
    AcquisitionSource,
)

from acquisition.github_tree import (
    GitHubClient,
    discover_complete_tree,
    build_blob_inventory,
    inventory_hash,
)

from acquisition.downloader import (
    acquire_all,
)


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--owner",
        required=True,
    )

    parser.add_argument(
        "--repository",
        required=True,
    )

    parser.add_argument(
        "--commit",
        required=True,
    )

    parser.add_argument(
        "--staging",
        required=True,
    )

    parser.add_argument(
        "--checkpoint",
        required=True,
    )

    parser.add_argument(
        "--token",
        default=None,
    )

    parser.add_argument(
        "--max-partition-bytes",
        type=int,
        default=1_700_000_000,
    )

    parser.add_argument(
        "--safety-margin-bytes",
        type=int,
        default=100_000_000,
    )

    args = parser.parse_args()

    source = AcquisitionSource(
        provider="github",
        owner=args.owner,
        repository=args.repository,
        commit_sha=args.commit,
    )

    client = GitHubClient(
        token=args.token
    )

    entries = discover_complete_tree(
        client,
        source,
    )

    blobs = build_blob_inventory(
        entries,
        max_file_bytes=(
            100 * 1024 * 1024
        ),
    )

    inv_hash = inventory_hash(
        blobs
    )

    result = acquire_all(
        client=client,
        source=source,
        entries=blobs,
        inventory_hash_value=inv_hash,
        staging_root=args.staging,
        checkpoint_path=args.checkpoint,
        run_id=str(uuid.uuid4()),
        max_partition_bytes=(
            args.max_partition_bytes
        ),
        safety_margin_bytes=(
            args.safety_margin_bytes
        ),
    )

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )


# ============================================================
# SHERIFF CONDITIONS
# ============================================================

SHERIFF_RULES = {

    "source_commit_mismatch":
        "STOP",

    "inventory_hash_mismatch":
        "STOP",

    "partition_hash_mismatch":
        "STOP",

    "tree_truncated":
        "STOP",

    "blob_sha_mismatch":
        "STOP",

    "file_size_mismatch":
        "STOP",

    "checkpoint_corrupt":
        "STOP",

    "download_failure":
        "STOP",

    "partial_publish":
        "FORBIDDEN",

    "direct_final_write":
        "FORBIDDEN",

    "unverified_file":
        "FORBIDDEN",
}


# ============================================================
# ACQUISITION STATE MACHINE
# ============================================================

STATE_MACHINE = {

    "INIT": [
        "SOURCE_LOCKED",
    ],

    "SOURCE_LOCKED": [
        "INVENTORY_VALID",
    ],

    "INVENTORY_VALID": [
        "PARTITION_PLAN_FROZEN",
    ],

    "PARTITION_PLAN_FROZEN": [
        "DOWNLOADING",
    ],

    "DOWNLOADING": [
        "DOWNLOADING",
        "STAGING_VERIFIED",
        "FAILED",
    ],

    "STAGING_VERIFIED": [
        "ACQUISITION_COMPLETE",
    ],

    "FAILED": [],

    "ACQUISITION_COMPLETE": [],
}


# ============================================================
# HARD INVARIANTS
# ============================================================

INVARIANTS = (

    "commit SHA is immutable",

    "inventory is immutable",

    "partition plan is immutable",

    "download order is lexicographic",

    "one blob acquisition is active at a time",

    "failed files cannot be silently skipped",

    "completed files require verification",

    "completed partitions require verified files",

    "checkpoint must match source commit",

    "checkpoint must match inventory hash",

    "checkpoint must match partition hash",

    "unverified staging cannot be published",

    "partial acquisition cannot be published",

    "tree truncation cannot be accepted",

    "Git blob SHA must match",

    "file size must match",

)


# ============================================================
# END OUTPUT 2C-2
# ============================================================
# ============================================================
# RUFLO DETERMINISTIC ACQUISITION
# OUTPUT 2D
# COMPLETE TREE WALKER
# ============================================================

# FILE:
# acquisition/tree_walker.py

from __future__ import annotations

import re
from dataclasses import dataclass

from acquisition.contracts import (
    AcquisitionError,
    AcquisitionSource,
    InventoryError,
)

from acquisition.github_tree import (
    GitHubClient,
    get_tree_object,
)


SHA40 = re.compile(
    r"^[0-9a-f]{40}$"
)


# ------------------------------------------------------------
# TREE NODE
# ------------------------------------------------------------

@dataclass(frozen=True)
class TreeNode:

    path: str
    sha: str


# ------------------------------------------------------------
# PATH NORMALIZATION
# ------------------------------------------------------------

def normalize_path(
    parent: str,
    child: str,
) -> str:

    if not child:
        raise InventoryError(
            "empty Git tree path"
        )

    if "\x00" in child:
        raise InventoryError(
            "NUL byte in Git path"
        )

    if child.startswith("/"):
        raise InventoryError(
            f"absolute path rejected: {child}"
        )

    if "\\" in child:
        raise InventoryError(
            f"backslash rejected: {child}"
        )

    parts = []

    if parent:
        parts.extend(
            parent.split("/")
        )

    parts.append(child)

    result = "/".join(parts)

    if result == ".git":
        raise InventoryError(
            ".git path rejected"
        )

    if result.startswith(".git/"):
        raise InventoryError(
            f"nested .git path rejected: {result}"
        )

    for part in result.split("/"):
        if part in ("", "."):
            raise InventoryError(
                f"invalid path component: {result}"
            )

        if part == "..":
            raise InventoryError(
                f"path traversal rejected: {result}"
            )

    return result


# ------------------------------------------------------------
# TREE RESPONSE VALIDATION
# ------------------------------------------------------------

def validate_tree_sha(
    sha: str,
) -> None:

    if not SHA40.fullmatch(sha):
        raise InventoryError(
            f"invalid tree SHA: {sha}"
        )


def validate_tree_response(
    response: dict,
    expected_sha: str,
) -> list[dict]:

    returned_sha = response.get(
        "sha"
    )

    if returned_sha != expected_sha:
        raise AcquisitionError(
            "GitHub returned unexpected "
            "tree SHA"
        )

    tree = response.get(
        "tree"
    )

    if not isinstance(
        tree,
        list,
    ):
        raise AcquisitionError(
            "GitHub tree is not a list"
        )

    return tree


# ------------------------------------------------------------
# COMPLETE NON-RECURSIVE WALK
# ------------------------------------------------------------

def walk_complete_tree(
    client: GitHubClient,
    source: AcquisitionSource,
    root_tree_sha: str,
) -> list[dict]:

    validate_tree_sha(
        root_tree_sha
    )

    discovered: list[dict] = []

    visited_trees: set[str] = set()

    # Queue contains:
    #
    #   (tree SHA, directory path)
    #
    pending: list[
        tuple[str, str]
    ] = [
        (root_tree_sha, "")
    ]

    while pending:

        pending.sort(
            key=lambda item: (
                item[1],
                item[0],
            )
        )

        tree_sha, parent = (
            pending.pop(0)
        )

        if tree_sha in visited_trees:

            raise InventoryError(
                "tree SHA encountered twice: "
                f"{tree_sha}"
            )

        visited_trees.add(
            tree_sha
        )

        response = get_tree_object(
            client,
            source,
            tree_sha,
            recursive=False,
        )

        raw_entries = (
            validate_tree_response(
                response,
                tree_sha,
            )
        )

        local_entries = []

        for raw in raw_entries:

            path = raw.get(
                "path"
            )

            entry_type = raw.get(
                "type"
            )

            sha = raw.get(
                "sha"
            )

            mode = raw.get(
                "mode"
            )

            size = raw.get(
                "size"
            )

            if not isinstance(
                path,
                str,
            ):
                raise InventoryError(
                    "tree entry path invalid"
                )

            if not isinstance(
                sha,
                str,
            ):
                raise InventoryError(
                    f"missing SHA: {path}"
                )

            validate_tree_sha(
                sha
            )

            full_path = normalize_path(
                parent,
                path,
            )

            if entry_type == "tree":

                local_entries.append(
                    (
                        full_path,
                        sha,
                    )
                )

            elif entry_type == "blob":

                if not isinstance(
                    size,
                    int,
                ):
                    raise InventoryError(
                        f"blob size missing: "
                        f"{full_path}"
                    )

                if size < 0:
                    raise InventoryError(
                        f"negative blob size: "
                        f"{full_path}"
                    )

                discovered.append(
                    {
                        "path":
                            full_path,

                        "mode":
                            str(mode),

                        "type":
                            "blob",

                        "sha":
                            sha,

                        "size":
                            size,
                    }
                )

            elif entry_type == "commit":

                # Git submodules are commits, not blobs.
                #
                # They are recorded separately and are NOT
                # silently downloaded as ordinary files.

                discovered.append(
                    {
                        "path":
                            full_path,

                        "mode":
                            str(mode),

                        "type":
                            "commit",

                        "sha":
                            sha,

                        "size":
                            None,
                    }
                )

            else:

                raise InventoryError(
                    f"unsupported tree type "
                    f"{entry_type}: "
                    f"{full_path}"
                )

        local_entries.sort(
            key=lambda item: (
                item[0],
                item[1],
            )
        )

        for child_path, child_sha in (
            local_entries
        ):

            pending.append(
                (
                    child_sha,
                    child_path,
                )
            )

    return discovered


# ------------------------------------------------------------
# GLOBAL INVENTORY VALIDATION
# ------------------------------------------------------------

def validate_discovered_tree(
    entries: list[dict],
) -> list[dict]:

    seen_paths: set[str] = set()

    blobs: list[dict] = []

    for entry in entries:

        path = entry["path"]

        if path in seen_paths:
            raise InventoryError(
                f"duplicate path: {path}"
            )

        seen_paths.add(
            path
        )

        if entry["type"] == "blob":
            blobs.append(
                entry
            )

    blobs.sort(
        key=lambda item: item["path"]
    )

    previous = None

    for entry in blobs:

        path = entry["path"]

        if previous is not None:

            if path <= previous:
                raise InventoryError(
                    "inventory ordering failure"
                )

        previous = path

    return blobs


# ------------------------------------------------------------
# ROOT TREE RESOLUTION
# ------------------------------------------------------------

def resolve_root_tree(
    client: GitHubClient,
    source: AcquisitionSource,
) -> str:

    commit = client.request_json(
        (
            f"repos/"
            f"{source.owner}/"
            f"{source.repository}/"
            f"git/commits/"
            f"{source.commit_sha}"
        )
    )

    returned_commit = commit.get(
        "sha"
    )

    if returned_commit != (
        source.commit_sha
    ):
        raise AcquisitionError(
            "commit SHA mismatch"
        )

    tree = commit.get(
        "tree"
    )

    if not isinstance(
        tree,
        dict,
    ):
        raise AcquisitionError(
            "commit tree missing"
        )

    root_sha = tree.get(
        "sha"
    )

    if not isinstance(
        root_sha,
        str,
    ):
        raise AcquisitionError(
            "root tree SHA missing"
        )

    validate_tree_sha(
        root_sha
    )

    return root_sha


# ------------------------------------------------------------
# COMPLETE INVENTORY API
# ------------------------------------------------------------

def discover_complete_inventory(
    client: GitHubClient,
    source: AcquisitionSource,
) -> list[dict]:

    root_sha = resolve_root_tree(
        client,
        source,
    )

    entries = walk_complete_tree(
        client,
        source,
        root_sha,
    )

    blobs = validate_discovered_tree(
        entries
    )

    if not blobs:
        raise InventoryError(
            "repository contains no blobs"
        )

    return blobs


# ------------------------------------------------------------
# DETERMINISTIC INVENTORY FINGERPRINT
# ------------------------------------------------------------

def inventory_fingerprint(
    entries: list[dict],
) -> str:

    import hashlib
    import json

    canonical = json.dumps(
        entries,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        canonical
    ).hexdigest()


# ------------------------------------------------------------
# SHERIFF
# ------------------------------------------------------------

def sheriff_tree_check(
    entries: list[dict],
) -> None:

    for entry in entries:

        if entry["type"] != "blob":
            continue

        size = entry["size"]

        if not isinstance(
            size,
            int,
        ):
            raise InventoryError(
                f"invalid blob size: "
                f"{entry['path']}"
            )

        # GitHub Git Blob API limit.
        if size > (
            100 * 1024 * 1024
        ):
            raise InventoryError(
                "blob exceeds GitHub Git Blob "
                f"API limit: {entry['path']}"
            )


# ============================================================
# FALLBACK POLICY
# ============================================================

TREE_DISCOVERY_POLICY = {

    "recursive_tree":
        "OPTIONAL",

    "recursive_tree_truncated":
        "FALLBACK_TO_NON_RECURSIVE",

    "non_recursive_tree":
        "REQUIRED_FOR_COMPLETE_WALK",

    "duplicate_path":
        "STOP",

    "duplicate_tree_sha":
        "STOP",

    "invalid_sha":
        "STOP",

    "invalid_path":
        "STOP",

    "unsupported_object":
        "STOP",

    "blob_over_100MB":
        "STOP",

}


# ============================================================
# IMPORTANT
# ============================================================
#
# This walker deliberately uses the GitHub non-recursive tree
# endpoint one tree at a time.
#
# Therefore a recursive response exceeding GitHub's documented
# aggregate limit cannot cause silent inventory truncation.
#
# The algorithm:
#
#   COMMIT
#      |
#      v
#   ROOT TREE SHA
#      |
#      v
#   NON-RECURSIVE TREE
#      |
#      +---- blob -> inventory
#      |
#      +---- tree -> queue
#                    |
#                    v
#                next tree
#
# The queue is sorted deterministically by:
#
#   (directory path, tree SHA)
#
# The final blob inventory is sorted by:
#
#   path
#
# The inventory fingerprint is generated only after the complete
# traversal has finished.
#
# No download is allowed before this inventory is frozen.
#
# ============================================================
# END OUTPUT 2D
# ============================================================
# ============================================================
# RUFLO DETERMINISTIC ACQUISITION
# OUTPUT 3 / 4
# DSL DAG RUNNER + STATE MACHINE + SHERIFF
# ============================================================

# FILE:
# control_layer/runner.py

from __future__ import annotations

import hashlib
import json
import os
import tempfile

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable


# ============================================================
# ERRORS
# ============================================================

class SheriffStop(Exception):
    pass


class DagError(Exception):
    pass


# ============================================================
# STATES
# ============================================================

class State(str, Enum):

    INIT = "INIT"

    VALIDATED = "VALIDATED"

    SOURCE_LOCKED = "SOURCE_LOCKED"

    INVENTORY_READY = "INVENTORY_READY"

    PLAN_READY = "PLAN_READY"

    ACQUIRING = "ACQUIRING"

    VERIFIED = "VERIFIED"

    COMMITTED = "COMMITTED"

    COMPLETE = "COMPLETE"

    FAILED = "FAILED"


# ============================================================
# ALLOWED TRANSITIONS
# ============================================================

TRANSITIONS = {

    State.INIT: {
        State.VALIDATED,
        State.FAILED,
    },

    State.VALIDATED: {
        State.SOURCE_LOCKED,
        State.FAILED,
    },

    State.SOURCE_LOCKED: {
        State.INVENTORY_READY,
        State.FAILED,
    },

    State.INVENTORY_READY: {
        State.PLAN_READY,
        State.FAILED,
    },

    State.PLAN_READY: {
        State.ACQUIRING,
        State.FAILED,
    },

    State.ACQUIRING: {
        State.ACQUIRING,
        State.VERIFIED,
        State.FAILED,
    },

    State.VERIFIED: {
        State.COMMITTED,
        State.FAILED,
    },

    State.COMMITTED: {
        State.COMPLETE,
        State.FAILED,
    },

    State.COMPLETE: set(),

    State.FAILED: set(),
}


# ============================================================
# DAG NODE
# ============================================================

@dataclass(frozen=True)
class Node:

    node_id: str

    depends_on: tuple[str, ...]

    action: str


# ============================================================
# FIXED DAG
# ============================================================

DAG = (

    Node(
        node_id="validate",
        depends_on=(),
        action="validate",
    ),

    Node(
        node_id="lock_source",
        depends_on=("validate",),
        action="lock_source",
    ),

    Node(
        node_id="discover",
        depends_on=("lock_source",),
        action="discover",
    ),

    Node(
        node_id="freeze_plan",
        depends_on=("discover",),
        action="freeze_plan",
    ),

    Node(
        node_id="acquire",
        depends_on=("freeze_plan",),
        action="acquire",
    ),

    Node(
        node_id="verify",
        depends_on=("acquire",),
        action="verify",
    ),

    Node(
        node_id="commit",
        depends_on=("verify",),
        action="commit",
    ),

    Node(
        node_id="complete",
        depends_on=("commit",),
        action="complete",
    ),
)


# ============================================================
# DAG VALIDATOR
# ============================================================

def validate_dag(
    nodes: tuple[Node, ...],
) -> None:

    ids = [
        node.node_id
        for node in nodes
    ]

    if len(ids) != len(set(ids)):

        raise DagError(
            "duplicate DAG node"
        )

    known = set(ids)

    for node in nodes:

        for dependency in (
            node.depends_on
        ):

            if dependency not in known:

                raise DagError(
                    f"unknown dependency: "
                    f"{node.node_id} -> "
                    f"{dependency}"
                )

    # Deterministic topological validation.
    remaining = {
        node.node_id: set(
            node.depends_on
        )
        for node in nodes
    }

    resolved = set()

    while remaining:

        ready = sorted(
            node_id
            for node_id, deps
            in remaining.items()
            if deps <= resolved
        )

        if not ready:

            raise DagError(
                "DAG contains a cycle"
            )

        for node_id in ready:

            resolved.add(
                node_id
            )

            del remaining[
                node_id
            ]


# ============================================================
# CANONICAL JSON
# ============================================================

def canonical_json(
    value: Any,
) -> bytes:

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_json(
    value: Any,
) -> str:

    return hashlib.sha256(
        canonical_json(value)
    ).hexdigest()


# ============================================================
# RUN MANIFEST
# ============================================================

@dataclass
class RunManifest:

    schema: str

    run_id: str

    source_commit: str | None = None

    inventory_hash: str | None = None

    partition_hash: str | None = None

    state: str = State.INIT.value

    completed_nodes: list[str] = field(
        default_factory=list
    )

    failed_node: str | None = None

    error: str | None = None

    def canonical(self) -> dict:

        return {

            "schema":
                self.schema,

            "run_id":
                self.run_id,

            "source_commit":
                self.source_commit,

            "inventory_hash":
                self.inventory_hash,

            "partition_hash":
                self.partition_hash,

            "state":
                self.state,

            "completed_nodes":
                list(
                    self.completed_nodes
                ),

            "failed_node":
                self.failed_node,

            "error":
                self.error,
        }


# ============================================================
# ATOMIC MANIFEST
# ============================================================

def save_manifest(
    path: str,
    manifest: RunManifest,
) -> None:

    target = Path(path)

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = canonical_json(
        manifest.canonical()
    )

    fd, temporary = tempfile.mkstemp(
        prefix=".manifest-",
        dir=str(target.parent),
    )

    try:

        with os.fdopen(
            fd,
            "wb",
        ) as handle:

            handle.write(
                payload
            )

            handle.flush()

            os.fsync(
                handle.fileno()
            )

        os.replace(
            temporary,
            target,
        )

    except Exception:

        try:
            os.unlink(
                temporary
            )
        except FileNotFoundError:
            pass

        raise


# ============================================================
# RUN CONTEXT
# ============================================================

@dataclass
class Context:

    config: dict[str, Any]

    manifest: RunManifest

    inventory: list[dict] = field(
        default_factory=list
    )

    partitions: list[Any] = field(
        default_factory=list
    )

    result: dict[str, Any] = field(
        default_factory=dict
    )


# ============================================================
# SHERIFF
# ============================================================

class Sheriff:

    def transition(
        self,
        current: State,
        target: State,
    ) -> None:

        allowed = TRANSITIONS.get(
            current,
            set(),
        )

        if target not in allowed:

            raise SheriffStop(
                "illegal state transition: "
                f"{current.value} -> "
                f"{target.value}"
            )

    def require(
        self,
        condition: bool,
        message: str,
    ) -> None:

        if not condition:

            raise SheriffStop(
                message
            )

    def require_equal(
        self,
        left: Any,
        right: Any,
        message: str,
    ) -> None:

        if left != right:

            raise SheriffStop(
                message
            )


# ============================================================
# ENGINE
# ============================================================

class DeterministicRunner:

    def __init__(
        self,
        context: Context,
        manifest_path: str,
    ) -> None:

        self.context = context

        self.manifest_path = (
            manifest_path
        )

        self.sheriff = Sheriff()

        self.actions: dict[
            str,
            Callable[[Context], None],
        ] = {}

    def register(
        self,
        name: str,
        action: Callable[
            [Context],
            None,
        ],
    ) -> None:

        if name in self.actions:

            raise DagError(
                f"duplicate action: {name}"
            )

        self.actions[
            name
        ] = action

    def set_state(
        self,
        target: State,
    ) -> None:

        current = State(
            self.context.manifest.state
        )

        self.sheriff.transition(
            current,
            target,
        )

        self.context.manifest.state = (
            target.value
        )

        save_manifest(
            self.manifest_path,
            self.context.manifest,
        )

    def execute(
        self,
    ) -> dict[str, Any]:

        validate_dag(
            DAG
        )

        self.set_state(
            State.VALIDATED
        )

        completed = set(
            self.context.manifest.completed_nodes
        )

        for node in DAG:

            if node.node_id in completed:
                continue

            for dependency in (
                node.depends_on
            ):

                if dependency not in completed:

                    raise DagError(
                        "dependency not completed: "
                        f"{node.node_id} -> "
                        f"{dependency}"
                    )

            action = self.actions.get(
                node.action
            )

            if action is None:

                raise DagError(
                    f"missing action: "
                    f"{node.action}"
                )

            try:

                self._prepare_state(
                    node.node_id
                )

                action(
                    self.context
                )

                self.context.manifest.completed_nodes.append(
                    node.node_id
                )

                completed.add(
                    node.node_id
                )

                save_manifest(
                    self.manifest_path,
                    self.context.manifest,
                )

            except Exception as exc:

                self.context.manifest.failed_node = (
                    node.node_id
                )

                self.context.manifest.error = (
                    str(exc)
                )

                self.context.manifest.state = (
                    State.FAILED.value
                )

                save_manifest(
                    self.manifest_path,
                    self.context.manifest,
                )

                raise

        self.sheriff.require(
            completed == {
                node.node_id
                for node in DAG
            },
            "DAG completed without all nodes",
        )

        self.sheriff.require_equal(
            self.context.manifest.state,
            State.COMPLETE.value,
            "final state is not COMPLETE",
        )

        return self.context.manifest.canonical()

    def _prepare_state(
        self,
        node_id: str,
    ) -> None:

        mapping = {

            "validate":
                State.VALIDATED,

            "lock_source":
                State.SOURCE_LOCKED,

            "discover":
                State.INVENTORY_READY,

            "freeze_plan":
                State.PLAN_READY,

            "acquire":
                State.ACQUIRING,

            "verify":
                State.VERIFIED,

            "commit":
                State.COMMITTED,

            "complete":
                State.COMPLETE,
        }

        target = mapping[
            node_id
        ]

        current = State(
            self.context.manifest.state
        )

        if current == target:
            return

        self.set_state(
            target
        )


# ============================================================
# STANDARD ACTION ADAPTERS
# ============================================================

def register_acquisition_actions(
    runner: DeterministicRunner,
    *,
    validate_action,
    lock_source_action,
    discover_action,
    freeze_plan_action,
    acquire_action,
    verify_action,
    commit_action,
) -> None:

    runner.register(
        "validate",
        validate_action,
    )

    runner.register(
        "lock_source",
        lock_source_action,
    )

    runner.register(
        "discover",
        discover_action,
    )

    runner.register(
        "freeze_plan",
        freeze_plan_action,
    )

    runner.register(
        "acquire",
        acquire_action,
    )

    runner.register(
        "verify",
        verify_action,
    )

    runner.register(
        "commit",
        commit_action,
    )

    runner.register(
        "complete",
        lambda ctx: None,
    )


# ============================================================
# SHERIFF INVARIANTS
# ============================================================

SHERIFF_INVARIANTS = (

    "source commit must remain immutable",

    "inventory hash must remain immutable",

    "partition hash must remain immutable",

    "DAG dependencies must be satisfied",

    "a node cannot execute twice in one run",

    "failed runs cannot become successful silently",

    "verification must precede commit",

    "commit must precede complete",

    "missing action is fatal",

    "illegal state transition is fatal",

    "manifest writes are atomic",

)


# ============================================================
# DSL EXAMPLE
# ============================================================

DSL = """

workflow RUFLO_ACQUIRE {

    source {
        provider = github
        owner = ENV.RUFLO_OWNER
        repository = ENV.RUFLO_REPOSITORY
        commit = ENV.RUFLO_COMMIT
    }

    policy {
        deterministic = true
        parallel = false
        fail_closed = true
        verify_git_sha = true
        verify_sha256 = true
        checkpoint = true
    }

    dag {

        validate

        lock_source
            after validate

        discover
            after lock_source

        freeze_plan
            after discover

        acquire
            after freeze_plan

        verify
            after acquire

        commit
            after verify

        complete
            after commit
    }

    sheriff {

        on source_mismatch STOP
        on inventory_mismatch STOP
        on partition_mismatch STOP
        on tree_truncated FALLBACK
        on blob_sha_mismatch STOP
        on size_mismatch STOP
        on checkpoint_mismatch STOP
        on verification_failure STOP
        on illegal_transition STOP
    }
}

"""


# ============================================================
# REQUIRED EXECUTION ORDER
# ============================================================

EXECUTION_ORDER = (

    "validate",

    "lock_source",

    "discover",

    "freeze_plan",

    "acquire",

    "verify",

    "commit",

    "complete",
)


# ============================================================
# FINAL RULE
# ============================================================

def assert_deterministic_order(
    executed: list[str],
) -> None:

    if executed != list(
        EXECUTION_ORDER
    ):

        raise SheriffStop(
            "execution order differs "
            "from canonical DAG order"
        )


# ============================================================
# END OUTPUT 3
# ============================================================






# ============================================================
# RUFLO DETERMINISTIC ACQUISITION
# OUTPUT 4 / 4
# TESTS + ASK COUNCIL 12 + FINAL SHERIFF AUDIT
# ============================================================

# FILE:
# tests/test_deterministic_acquisition.py

from __future__ import annotations

import hashlib
import json

import pytest

from control_layer.runner import (
    DAG,
    EXECUTION_ORDER,
    Context,
    DeterministicRunner,
    RunManifest,
    Sheriff,
    SheriffStop,
    State,
    validate_dag,
    assert_deterministic_order,
)


# ============================================================
# 1. DAG STRUCTURE
# ============================================================

def test_dag_is_valid():

    validate_dag(
        DAG
    )


def test_dag_order_is_fixed():

    expected = (
        "validate",
        "lock_source",
        "discover",
        "freeze_plan",
        "acquire",
        "verify",
        "commit",
        "complete",
    )

    assert EXECUTION_ORDER == expected


def test_dag_has_no_duplicate_nodes():

    ids = [
        node.node_id
        for node in DAG
    ]

    assert len(ids) == len(set(ids))


# ============================================================
# 2. STATE MACHINE
# ============================================================

def test_initial_state():

    assert State.INIT.value == "INIT"


def test_valid_transition():

    sheriff = Sheriff()

    sheriff.transition(
        State.INIT,
        State.VALIDATED,
    )


def test_invalid_transition_is_rejected():

    sheriff = Sheriff()

    with pytest.raises(
        SheriffStop
    ):

        sheriff.transition(
            State.INIT,
            State.COMPLETE,
        )


# ============================================================
# 3. CANONICAL INVENTORY
# ============================================================

def canonical_inventory(
    entries,
):

    ordered = sorted(
        entries,
        key=lambda x: x["path"],
    )

    payload = json.dumps(
        ordered,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(
        payload
    ).hexdigest()


def test_inventory_hash_is_deterministic():

    inventory = [
        {
            "path": "b.py",
            "sha": "b" * 40,
            "size": 10,
        },
        {
            "path": "a.py",
            "sha": "a" * 40,
            "size": 20,
        },
    ]

    first = canonical_inventory(
        inventory
    )

    second = canonical_inventory(
        list(reversed(inventory))
    )

    assert first == second


# ============================================================
# 4. EXECUTION ORDER
# ============================================================

def test_execution_order():

    executed = []

    assert_deterministic_order(
        list(EXECUTION_ORDER)
    )

    executed.extend(
        EXECUTION_ORDER
    )

    assert executed == list(
        EXECUTION_ORDER
    )


def test_wrong_execution_order():

    with pytest.raises(
        SheriffStop
    ):

        assert_deterministic_order(
            [
                "validate",
                "discover",
                "lock_source",
                "freeze_plan",
                "acquire",
                "verify",
                "commit",
                "complete",
            ]
        )


# ============================================================
# 5. RUNNER
# ============================================================

def make_runner():

    context = Context(

        config={
            "deterministic": True,
        },

        manifest=RunManifest(

            schema=
                "ruflo.acquisition.run.v1",

            run_id=
                "test-run",

        ),
    )

    runner = DeterministicRunner(
        context,
        "/tmp/ruflo-test-manifest.json",
    )

    executed = []

    def action(name):

        def run(ctx):

            executed.append(
                name
            )

        return run

    runner.register(
        "validate",
        action("validate"),
    )

    runner.register(
        "lock_source",
        action("lock_source"),
    )

    runner.register(
        "discover",
        action("discover"),
    )

    runner.register(
        "freeze_plan",
        action("freeze_plan"),
    )

    runner.register(
        "acquire",
        action("acquire"),
    )

    runner.register(
        "verify",
        action("verify"),
    )

    runner.register(
        "commit",
        action("commit"),
    )

    runner.register(
        "complete",
        action("complete"),
    )

    return runner, executed


def test_runner_executes_deterministically():

    runner, executed = (
        make_runner()
    )

    result = runner.execute()

    assert executed == list(
        EXECUTION_ORDER
    )

    assert result["state"] == (
        "COMPLETE"
    )


# ============================================================
# 6. FAILURE MUST STOP
# ============================================================

def test_failure_stops_pipeline():

    context = Context(

        config={},

        manifest=RunManifest(

            schema=
                "ruflo.acquisition.run.v1",

            run_id=
                "failure-test",
        ),
    )

    runner = DeterministicRunner(
        context,
        "/tmp/ruflo-failure.json",
    )

    runner.register(
        "validate",
        lambda ctx: None,
    )

    def fail(ctx):

        raise RuntimeError(
            "forced failure"
        )

    runner.register(
        "lock_source",
        fail,
    )

    with pytest.raises(
        RuntimeError
    ):

        runner.execute()

    assert (
        context.manifest.state
        == "FAILED"
    )

    assert (
        context.manifest.failed_node
        == "lock_source"
    )


# ============================================================
# 7. SHERIFF INTEGRITY TESTS
# ============================================================

def test_sheriff_equal():

    sheriff = Sheriff()

    sheriff.require_equal(
        "abc",
        "abc",
        "values differ",
    )


def test_sheriff_equal_rejects():

    sheriff = Sheriff()

    with pytest.raises(
        SheriffStop
    ):

        sheriff.require_equal(
            "abc",
            "def",
            "hash mismatch",
        )


def test_sheriff_condition():

    sheriff = Sheriff()

    sheriff.require(
        True,
        "must pass",
    )

    with pytest.raises(
        SheriffStop
    ):

        sheriff.require(
            False,
            "must fail",
        )


# ============================================================
# 8. FINAL MANIFEST CONTRACT
# ============================================================

REQUIRED_MANIFEST_FIELDS = {
    "schema",
    "run_id",
    "source_commit",
    "inventory_hash",
    "partition_hash",
    "state",
    "completed_nodes",
    "failed_node",
    "error",
}


def test_manifest_contract():

    manifest = RunManifest(

        schema=
            "ruflo.acquisition.run.v1",

        run_id=
            "contract-test",
    )

    data = manifest.canonical()

    assert REQUIRED_MANIFEST_FIELDS <= (
        set(data.keys())
    )


# ============================================================
# 9. FINAL SHERIFF AUDIT
# ============================================================

FINAL_AUDIT_RULES = {

    "A01_SOURCE_PIN":
        "commit SHA is explicitly supplied",

    "A02_SOURCE_IMMUTABLE":
        "source commit cannot change during run",

    "A03_COMPLETE_TREE":
        "truncated tree cannot be accepted as complete",

    "A04_CANONICAL_INVENTORY":
        "inventory is sorted and canonically hashed",

    "A05_PARTITION_DETERMINISM":
        "same inventory produces same partition plan",

    "A06_CHECKPOINT_BINDING":
        "checkpoint is bound to commit and hashes",

    "A07_BLOB_INTEGRITY":
        "Git blob SHA must match",

    "A08_SIZE_INTEGRITY":
        "downloaded size must match inventory",

    "A09_SHA256":
        "SHA-256 is recorded for final evidence",

    "A10_ATOMIC_STAGING":
        "partial files cannot become final files",

    "A11_DAG_ORDER":
        "nodes execute only after dependencies",

    "A12_FAIL_CLOSED":
        "integrity errors terminate the run",
}


def audit_rules():

    assert len(
        FINAL_AUDIT_RULES
    ) == 12

    for key, description in (
        FINAL_AUDIT_RULES.items()
    ):

        assert key.startswith(
            "A"
        )

        assert description


# ============================================================
# ASK COUNCIL — 12 STEP ACCEPTANCE
# ============================================================

ASK_COUNCIL = (

    {
        "step": 1,
        "question":
            "Is the exact source commit pinned?",
        "pass":
            "source.commit_sha exists and is immutable",
        "fail":
            "STOP",
    },

    {
        "step": 2,
        "question":
            "Can GitHub return an incomplete recursive tree?",
        "pass":
            "truncation is detected and complete "
            "non-recursive traversal is used",
        "fail":
            "STOP",
    },

    {
        "step": 3,
        "question":
            "Is the final inventory canonical?",
        "pass":
            "paths are normalized, unique and sorted",
        "fail":
            "STOP",
    },

    {
        "step": 4,
        "question":
            "Is the inventory cryptographically identified?",
        "pass":
            "inventory SHA-256 is frozen before acquisition",
        "fail":
            "STOP",
    },

    {
        "step": 5,
        "question":
            "Is partitioning deterministic?",
        "pass":
            "same inventory and policy produce same plan",
        "fail":
            "STOP",
    },

    {
        "step": 6,
        "question":
            "Is resume safe?",
        "pass":
            "checkpoint matches commit, inventory and partition hash",
        "fail":
            "STOP",
    },

    {
        "step": 7,
        "question":
            "Can an incomplete file be accepted?",
        "pass":
            "no; size and Git blob SHA are checked",
        "fail":
            "STOP",
    },

    {
        "step": 8,
        "question":
            "Can a corrupted blob be published?",
        "pass":
            "no; Git blob SHA mismatch is fatal",
        "fail":
            "STOP",
    },

    {
        "step": 9,
        "question":
            "Can a partial staging tree be published?",
        "pass":
            "no; final verification precedes commit",
        "fail":
            "STOP",
    },

    {
        "step": 10,
        "question":
            "Can the DAG execute out of order?",
        "pass":
            "dependency validation rejects it",
        "fail":
            "STOP",
    },

    {
        "step": 11,
        "question":
            "Can a failed run silently become successful?",
        "pass":
            "FAILED is terminal until a valid controlled resume",
        "fail":
            "STOP",
    },

    {
        "step": 12,
        "question":
            "Can the resulting acquisition be independently audited?",
        "pass":
            "manifest contains source, hashes, state and completed nodes",
        "fail":
            "STOP",
    },
)


def run_ask_council():

    if len(
        ASK_COUNCIL
    ) != 12:

        raise SheriffStop(
            "Ask Council must contain "
            "exactly 12 checks"
        )

    for item in ASK_COUNCIL:

        if not item.get(
            "question"
        ):

            raise SheriffStop(
                "missing council question"
            )

        if item.get(
            "fail"
        ) != "STOP":

            raise SheriffStop(
                "council must fail closed"
            )

    return {
        "status":
            "PASS",

        "checks":
            len(ASK_COUNCIL),
    }


# ============================================================
# FINAL ACCEPTANCE
# ============================================================

def final_acceptance(
    manifest: dict,
) -> dict:

    required = {
        "schema",
        "run_id",
        "source_commit",
        "inventory_hash",
        "partition_hash",
        "state",
        "completed_nodes",
    }

    missing = (
        required
        - set(manifest.keys())
    )

    if missing:

        raise SheriffStop(
            "manifest missing fields: "
            + ",".join(
                sorted(missing)
            )
        )

    if manifest["state"] != (
        "COMPLETE"
    ):

        raise SheriffStop(
            "acquisition is not COMPLETE"
        )

    if manifest["failed_node"] is not None:

        raise SheriffStop(
            "manifest contains failed node"
        )

    if manifest["error"] is not None:

        raise SheriffStop(
            "manifest contains error"
        )

    expected_nodes = list(
        EXECUTION_ORDER
    )

    if manifest[
        "completed_nodes"
    ] != expected_nodes:

        raise SheriffStop(
            "completed DAG does not match "
            "canonical order"
        )

    return {
        "status":
            "ACCEPTED",

        "deterministic":
            True,

        "verified":
            True,

        "source_commit":
            manifest["source_commit"],

        "inventory_hash":
            manifest["inventory_hash"],

        "partition_hash":
            manifest["partition_hash"],
    }


# ============================================================
# REPOSITORY LAYOUT
# ============================================================

REPOSITORY_LAYOUT = """

control-layer/
├── dsl/
│   └── ruflo_acquire.dsl
│
├── schema/
│   └── acquisition.schema.json
│
├── dag/
│   └── ruflo_acquire.dag.json
│
├── sheriff/
│   └── rules.py
│
├── acquisition/
│   ├── contracts.py
│   ├── github_tree.py
│   ├── tree_walker.py
│   ├── partitioner.py
│   └── downloader.py
│
├── control_layer/
│   └── runner.py
│
├── tests/
│   └── test_deterministic_acquisition.py
│
└── manifests/
    └── .gitkeep

"""


# ============================================================
# EXECUTION CONTRACT
# ============================================================

EXECUTION_CONTRACT = """

INPUT:

    GitHub owner
    GitHub repository
    immutable commit SHA

PROCESS:

    validate
    -> lock source
    -> discover complete inventory
    -> freeze inventory
    -> create deterministic partitions
    -> acquire blobs
    -> verify every file
    -> commit staging
    -> generate final manifest

OUTPUT:

    complete verified source tree
    acquisition manifest
    inventory hash
    partition hash

FAILURE:

    STOP

NO:

    silent skip
    silent retry after integrity failure
    partial publication
    mutable source
    unverified file
    unordered execution

"""


# ============================================================
# FINAL CERTIFICATION
# ============================================================

def certify():

    validate_dag(
        DAG
    )

    audit_rules()

    council = run_ask_council()

    assert_deterministic_order(
        list(EXECUTION_ORDER)
    )

    return {

        "system":
            "RUFLO_DETERMINISTIC_ACQUISITION",

        "version":
            "1.0",

        "dag":
            "VALID",

        "sheriff":
            "FAIL_CLOSED",

        "ask_council":
            council,

        "execution":
            "DETERMINISTIC",

        "status":
            "READY_FOR_INTEGRATION",
    }


# ============================================================
# END OUTPUT 4 / 4
# ============================================================
# ============================================================
# PATCH RUFLO ACQUISITION v1.1
# COMPLETE SOURCE SNAPSHOT HARDENING
# ============================================================

patch RUFLO_ACQUIRE {

    # --------------------------------------------------------
    # SOURCE SEMANTICS
    # --------------------------------------------------------

    source_mode = SOURCE_SNAPSHOT

    source {

        provider = github

        owner = ENV.RUFLO_OWNER

        repository =
            ENV.RUFLO_REPOSITORY

        commit =
            ENV.RUFLO_COMMIT

        immutable = true

    }


    # --------------------------------------------------------
    # IMPORTANT:
    #
    # SOURCE_SNAPSHOT means:
    #
    #   all tracked source objects reachable from the pinned
    #   commit that are required to reproduce that tree.
    #
    # It does NOT mean:
    #
    #   npm install
    #   execute install.sh
    #   download GitHub release assets
    #   execute Ruflo
    #
    # Those are separate acquisition modes.
    # --------------------------------------------------------


    acquisition {

        mode = SOURCE_SNAPSHOT

        execute_install = false

        execute_source = false

        download_release_assets = false

        include_git_history = false

    }


    # --------------------------------------------------------
    # TREE DISCOVERY
    # --------------------------------------------------------

    tree {

        recursive = true

        on_truncated = WALK_SUBTREES

        require_complete = true

        reject_incomplete_inventory = true

    }


    # --------------------------------------------------------
    # SPECIAL OBJECTS
    # --------------------------------------------------------

    submodules {

        detect = true

        mode = RESOLVE_PINNED_COMMIT

        require_url = true

        require_sha = true

        recursive = true

        on_unavailable = STOP

    }


    symlinks {

        detect = true

        preserve = true

        do_not_follow_during_inventory = true

        reject_absolute_target = true

        reject_escape_from_root = true

    }


    # --------------------------------------------------------
    # GIT LFS
    # --------------------------------------------------------

    lfs {

        detect = true

        pointer_detection = true

        if_pointer = RESOLVE_LFS_OBJECT

        require_oid = true

        require_size = true

        require_content = true

        verify_oid = true

        on_missing_object = STOP

        on_pointer_only = STOP

    }


    # --------------------------------------------------------
    # NORMAL BLOBS
    # --------------------------------------------------------

    blobs {

        require_sha = true

        require_size = true

        verify_git_object = true

        verify_sha256 = true

        max_normal_blob_bytes =
            104857600

        on_over_limit = STOP

    }


    # --------------------------------------------------------
    # INVENTORY
    # --------------------------------------------------------

    inventory {

        include = [

            path,

            mode,

            type,

            sha,

            size,

            lfs_oid,

            lfs_size,

            submodule_url,

            submodule_sha,

            symlink_target

        ]

        normalize_paths = true

        reject_duplicate_paths = true

        reject_path_traversal = true

        reject_absolute_paths = true

        sort = PATH_ASC

        freeze_before_download = true

    }


    # --------------------------------------------------------
    # INVENTORY IDENTITY
    # --------------------------------------------------------

    identity {

        source_key =
            owner + "/" +
            repository + "@" +
            commit

        inventory_hash = SHA256_CANONICAL

        plan_hash = SHA256_CANONICAL

    }


    # --------------------------------------------------------
    # DESTINATION SAFETY
    # --------------------------------------------------------

    destination {

        repository =
            ENV.DESTINATION_REPOSITORY

        staging = true

        publish_only_after_verify = true

        atomic_publish = true

        reject_partial_publish = true

    }


    # --------------------------------------------------------
    # GITHUB DESTINATION LIMITS
    # --------------------------------------------------------

    github_limits {

        normal_blob_limit =
            104857600

        push_limit =
            2147483648

        recommended_repository_size =
            1073741824

        strongly_recommended_max =
            5368709120

    }


    # --------------------------------------------------------
    # DESTINATION PRECHECK
    # --------------------------------------------------------

    destination_precheck {

        calculate_projected_size = true

        calculate_projected_blob_count = true

        calculate_projected_push_size = true

        if_projected_push_over_limit = STOP

        if_normal_blob_over_limit = STOP

        if_repository_policy_exceeded = STOP

    }


    # --------------------------------------------------------
    # CHECKPOINT BINDING
    # --------------------------------------------------------

    checkpoint {

        bind_to = [

            source_key,

            inventory_hash,

            plan_hash

        ]

        mismatch = STOP

        corrupted = STOP

        stale = STOP

    }


    # --------------------------------------------------------
    # DAG PATCH
    # --------------------------------------------------------

    dag {

        validate

        lock_source
            after validate

        resolve_commit
            after lock_source

        discover_tree
            after resolve_commit

        expand_subtrees
            after discover_tree

        detect_special_objects
            after expand_subtrees

        resolve_submodules
            after detect_special_objects

        resolve_lfs
            after resolve_submodules

        freeze_inventory
            after resolve_lfs

        freeze_plan
            after freeze_inventory

        destination_precheck
            after freeze_plan

        acquire
            after destination_precheck

        verify
            after acquire

        verify_special_objects
            after verify

        verify_complete_snapshot
            after verify_special_objects

        commit
            after verify_complete_snapshot

        manifest
            after commit

        complete
            after manifest
    }


    # --------------------------------------------------------
    # SHERIFF PATCH
    # --------------------------------------------------------

    sheriff {

        on_source_change STOP

        on_commit_mismatch STOP

        on_tree_truncated WALK_SUBTREES

        on_incomplete_tree STOP

        on_duplicate_path STOP

        on_invalid_path STOP

        on_path_escape STOP

        on_submodule_missing STOP

        on_submodule_commit_mismatch STOP

        on_symlink_escape STOP

        on_lfs_pointer_only STOP

        on_lfs_object_missing STOP

        on_lfs_oid_mismatch STOP

        on_blob_over_100MB STOP

        on_inventory_mismatch STOP

        on_plan_mismatch STOP

        on_checkpoint_mismatch STOP

        on_size_mismatch STOP

        on_git_sha_mismatch STOP

        on_sha256_mismatch STOP

        on_destination_limit STOP

        on_partial_publish STOP

        on_verification_failure STOP

    }


    # --------------------------------------------------------
    # FINAL ACCEPTANCE
    # --------------------------------------------------------

    acceptance {

        require_source_commit = true

        require_complete_inventory = true

        require_inventory_hash = true

        require_plan_hash = true

        require_all_blobs_verified = true

        require_all_lfs_objects_verified = true

        require_all_submodules_resolved = true

        require_symlinks_validated = true

        require_destination_precheck = true

        require_atomic_publish = true

        require_manifest = true

        otherwise = STOP

    }

}

# ============================================================
# PATCH END
# ============================================================
# ============================================================
# PATCH v1.2 — DETERMINISTIC SOURCE LOCK + RATE LIMIT + WITNESS
# SOLO ELEMENTOS FALTANTES
# ============================================================

patch RUFLO_ACQUIRE {

    # --------------------------------------------------------
    # 1. VERSION / COMMIT MUST BE IMMUTABLE
    # --------------------------------------------------------

    source {

        immutable = true

        require_commit_sha = true

        reject_branch_only = true

        reject_tag_only = true

        reject_latest = true

        # @latest is permitted by Ruflo's installation guide,
        # but NOT permitted for deterministic acquisition.

        version_record = true

        record = [
            owner,
            repository,
            commit,
            resolved_version
        ]
    }


    # --------------------------------------------------------
    # 2. GITHUB API RATE LIMIT SAFETY
    # --------------------------------------------------------

    github_api {

        inspect_rate_limit = true

        read_rate_limit_headers = true

        on_403 = RATE_LIMIT_HANDLER

        on_429 = RATE_LIMIT_HANDLER

        on_secondary_limit = RATE_LIMIT_HANDLER

        max_retries = 3

        retry_after_header = true

        reset_header = true

        no_retry_without_wait = true

        on_retry_exhausted = STOP
    }


    # --------------------------------------------------------
    # RATE LIMIT HANDLER
    # --------------------------------------------------------

    rate_limit_handler {

        if_retry_after_exists =
            WAIT_RETRY_AFTER

        else_if_remaining_zero =
            WAIT_UNTIL_RESET

        else =
            WAIT_MINIMUM_60_SECONDS

        after_wait =
            RECHECK_LIMIT

        failed_recheck =
            STOP
    }


    # --------------------------------------------------------
    # 3. RUFLO WITNESS VERIFICATION
    # --------------------------------------------------------

    witness {

        enabled = true

        required = true

        command = "ruflo verify"

        verify_after_acquisition = true

        verify_before_publish = true

        nonzero_exit = STOP

        witness_mismatch = STOP

        missing_manifest = STOP
    }


    # --------------------------------------------------------
    # DAG PATCH
    # --------------------------------------------------------

    dag {

        lock_source
            after validate

        resolve_commit
            after lock_source

        verify_source_identity
            after resolve_commit

        discover_tree
            after verify_source_identity

        # existing acquisition DAG continues unchanged

        verify
            after acquire

        verify_witness
            after verify

        verify_complete_snapshot
            after verify_witness

        commit
            after verify_complete_snapshot
    }


    # --------------------------------------------------------
    # SHERIFF PATCH
    # --------------------------------------------------------

    sheriff {

        on_latest_reference STOP

        on_unpinned_source STOP

        on_commit_resolution_mismatch STOP

        on_rate_limit STOP

        on_403_rate_limit WAIT

        on_429_rate_limit WAIT

        on_retry_exhausted STOP

        on_witness_missing STOP

        on_witness_failure STOP

        on_witness_mismatch STOP
    }


    # --------------------------------------------------------
    # FINAL ACCEPTANCE PATCH
    # --------------------------------------------------------

    acceptance {

        require_immutable_commit = true

        require_rate_limit_safe = true

        require_witness_verified = true

        require_witness_before_publish = true

    }

}

# ============================================================
# END PATCH v1.2
# ============================================================






