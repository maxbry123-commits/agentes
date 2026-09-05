Resumen JSON para IA (DSL / MAXBRY / YAIWES / NCT) este es el enchufe de todas las fichas de code del sofware el primer jason es indicacion para Ai y luego texto libre para mí y luego el Jason code del enchufe 🔌 🔌 🔌 🔌 🔌 🔌 🔌 🔌 🔌 🔌 🔌 

{
  "concepto": "Contrato universal de módulos",
  "objetivo": "Permitir conectar fichas de código, prompts DSL, APIs, MCP, bases de datos, herramientas y LLMs externos mediante una interfaz común.",
  "funcion": "Cada ficha declara qué consume, qué produce, cómo se ejecuta y bajo qué reglas puede conectarse.",
  "conexion": {
    "codigo": true,
    "llm": true,
    "dsl_prompt": true,
    "api": true,
    "mcp": true,
    "db": true,
    "tools": true
  },
  "compatibilidad": "Las fichas se unen automáticamente si sus entradas y salidas son compatibles.",
  "seguridad": "Define permisos, límites, sandbox y recuperación.",
  "resultado": "Construye pipelines DAG donde cada módulo es una neurona reutilizable.",
  "ecosistema": [
    "MAXBRY",
    "YAIWES",
    "NCT Neuronas Code Turbo"
  ]
}


---

Resumen en lenguaje normal

Este JSON es el enchufe universal de MAXBRY, YAIWES y NCT Neuronas Code Turbo.

Su función es convertir cualquier pieza de código, prompt DSL, agente IA, API, MCP, herramienta o base de datos en una ficha conectable.

Cada ficha indica:

Qué información recibe.

Qué información entrega.

Cómo se ejecuta.

Qué permisos necesita.

Con qué otras fichas puede conectarse.


Gracias a este contrato, el sistema puede unir automáticamente módulos de Python, DSL, LLMs locales o externos, APIs y MCP para formar redes de neuronas funcionales y pipelines completos sin depender de un lenguaje específico.

En una frase:

Es el estándar que permite conectar todas las neuronas de software de MAXBRY como bloques LEGO inteligentes, independientemente de si son código, prompts DSL o capas externas de IA. 🧠⚡


{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://maxbry.dev/schemas/universal_module_contract.v1.5.json",
  "title": "MAXBRY Universal Module Contract v1.5",
  "_versioning_policy": {
    "contract_version": "versión del schema/spec (quién manda en compatibilidad)",
    "artifact_version": "versión del módulo/implementación",
    "_version":         "versión del meta-spec (solo docs)",
    "build_id_fuente":  "gobernanza_ref.build_id — única fuente de verdad"
  },
  "type": "object",
  "additionalProperties": false,
  "required": ["artifact_id","artifact_version","contract_version","contract_hash",
    "hash_algorithm","estado","ciclo_vida","registry_metadata","contrato",
    "naturaleza","seguridad","ejecucion","resultado","dependencias","versioning","gobernanza_ref"],

  "definitions": {
    "semver":       { "type":"string", "pattern":"^\\d+\\.\\d+\\.\\d+$" },
    "artifact_id":  { "type":"string", "pattern":"^[a-z0-9_]+(\\.[a-z0-9_]+)+$" },
    "artifact_ref": { "type":"string", "pattern":"^[a-z0-9_]+(\\.[a-z0-9_]+)+@\\d+\\.\\d+\\.\\d+$" },
    "datatype": {
      "type":"object", "additionalProperties":false,
      "required":["family","type","version"],
      "properties": {
        "family":  { "type":"string", "pattern":"^[a-z0-9_]+$" },
        "type":    { "type":"string", "pattern":"^[a-z0-9_]+$" },
        "version": { "type":"integer", "minimum":1 }
      }
    },
    "io": {
      "type":"object",
      "required":["datatype","schema_uri","intent"],
      "properties": {
        "datatype":     { "$ref":"#/definitions/datatype" },
        "schema_uri":   { "type":"string", "format":"uri-reference" },
        "content_type": { "type":"string" },
        "intent":       { "type":"array", "minItems":1, "items":{"type":"string"} },
        "required":     { "type":"array", "items":{"type":"string"} },
        "constraints":  { "type":"object" },
        "guarantees":   { "type":"array", "items":{"type":"string"} }
      }
    },
    "io_or_null": {
      "oneOf": [ {"$ref":"#/definitions/io"}, {"type":"null"} ]
    },
    "error": {
      "type":"object", "additionalProperties":false,
      "required":["code","retryable"],
      "properties": {
        "code":        { "type":"string", "pattern":"^E[0-9]{3}$" },
        "retryable":   { "type":"boolean" },
        "max_retries": { "type":"integer", "minimum":0 },
        "backoff_ms":  { "type":"array", "items":{"type":"integer","minimum":0} },
        "fatal":       { "type":"boolean" }
      }
    },
    "ref_list": {
      "type":"array",
      "items":{ "type":"object", "required":["family"],
        "properties":{"family":{"type":"string"},"type":{"type":"string"}} }
    }
  },

  "properties": {
    "_spec":             { "type":"string" },
    "_version":          { "type":"string" },
    "_versioning_policy":{ "type":"object" },

    "artifact_id":      { "$ref":"#/definitions/artifact_id" },
    "artifact_version": { "$ref":"#/definitions/semver" },
    "contract_version": { "type":"string", "pattern":"^\\d+\\.\\d+$" },
    "contract_hash":    { "type":"string", "pattern":"^sha256:([a-f0-9]{64}|\\.\\.\\.)$" },
    "hash_algorithm":   { "enum":["sha256"] },
    "estado":           { "enum":["draft","testing","active","deprecated","blocked"] },

    "ciclo_vida": {
      "type":"object", "additionalProperties":false, "required":["creado"],
      "properties": {
        "creado":        { "type":"string", "format":"date-time" },
        "deployed_at":   { "type":["string","null"], "format":"date-time" },
        "deprecated_at": { "type":["string","null"], "format":"date-time" },
        "blocked_at":    { "type":["string","null"], "format":"date-time" },
        "replaces":      { "type":"array", "items":{"$ref":"#/definitions/artifact_ref"} }
      }
    },

    "registry_metadata": {
      "type":"object", "additionalProperties":false,
      "required":["slot","priority","domain","capa"],
      "properties": {
        "slot":     { "type":"string" },
        "priority": { "type":"integer", "minimum":0 },
        "domain":   { "type":"string" },
        "capa":     { "enum":["KERNEL","RUNTIME","VERIFICATION","STATE"] }
      }
    },

    "contrato": {
      "type":"object", "additionalProperties":false,
      "required":["rol","errores","restricciones"],
      "properties": {
        "rol":     { "enum":["transform","source","sink"] },
        "consume": { "$ref":"#/definitions/io_or_null" },
        "expone":  { "$ref":"#/definitions/io_or_null" },
        "errores": { "type":"object", "minProperties":1,
          "additionalProperties":{"$ref":"#/definitions/error"} },
        "restricciones": {
          "type":"object", "additionalProperties":false,
          "properties": {
            "cannot_follow":      { "$ref":"#/definitions/ref_list" },
            "cannot_precede":     { "$ref":"#/definitions/ref_list" },
            "requires_preceding": { "$ref":"#/definitions/ref_list" },
            "requires_following": { "$ref":"#/definitions/ref_list" }
          }
        }
      },
      "allOf": [
        { "if":{"properties":{"rol":{"const":"source"}}},
          "then":{"required":["expone"],"properties":{"consume":{"type":"null"}}} },
        { "if":{"properties":{"rol":{"const":"sink"}}},
          "then":{"required":["consume"],"properties":{"expone":{"type":"null"}}} },
        { "if":{"properties":{"rol":{"const":"transform"}}},
          "then":{"required":["consume","expone"],
            "properties":{"consume":{"type":"object"},"expone":{"type":"object"}}} }
      ]
    },

    "transform": {
      "type":"object", "additionalProperties":false,
      "properties": {
        "input_map":  { "type":"object" },
        "output_map": { "type":"object" }
      }
    },

    "naturaleza": {
      "type":"object", "additionalProperties":false,
      "required":["determinista","idempotente","efectos"],
      "properties": {
        "determinista": { "type":"boolean" },
        "idempotente":  { "type":"boolean" },
        "puro":         { "type":"boolean" },
        "efectos": {
          "type":"object", "additionalProperties":false,
          "required":["escribe_db","llama_api","irreversible"],
          "properties": {
            "escribe_db":        { "type":"boolean" },
            "llama_api":         { "type":"boolean" },
            "irreversible":      { "type":"boolean" },
            "side_effects_list": { "type":"array", "items":{"type":"string"} }
          }
        }
      }
    },

    "seguridad": {
      "type":"object", "additionalProperties":false,
      "required":["permisos","limites","sandbox"],
      "properties": {
        "permisos":         { "type":"array", "items":{"type":"string"} },
        "deny_permissions": { "type":"array", "items":{"type":"string"} },
        "limites": {
          "type":"object", "additionalProperties":false,
          "required":["timeout_ms","deadline_ms"],
          "properties": {
            "timeout_ms":     { "type":"integer", "minimum":1 },
            "deadline_ms":    { "type":"integer", "minimum":1 },
            "memoria_max_mb": { "type":"integer", "minimum":1 },
            "cpu_max_percent":{ "type":"integer", "minimum":1, "maximum":100 }
          }
        },
        "sandbox": { "enum":["container","process","none"] }
      }
    },

    "ejecucion": {
      "type":"object", "additionalProperties":false,
      "required":["kind","transport","config"],
      "properties": {
        "kind":      { "enum":["code","llm","db","api","tool"] },
        "transport": { "enum":["stdio","importlib","http","sdk","prompt","mcp"] },
        "config":    { "type":"object" },
        "fallback": {
          "type":"object", "additionalProperties":false,
          "required":["transport","config"],
          "properties": {
            "transport": { "enum":["stdio","importlib","http","sdk","prompt","mcp"] },
            "config":    { "type":"object" }
          }
        },
        "requires_env": { "type":"array", "items":{"type":"string"} },
        "healthcheck": {
          "type":"object", "additionalProperties":false,
          "required":["interval_ms"],
          "properties":{ "interval_ms":{"type":"integer","minimum":1000} }
        }
      }
    },

    "resultado": {
      "type":"object", "additionalProperties":false,
      "required":["success_schema_uri","error_schema_uri","trace_id_format"],
      "properties": {
        "success_schema_uri": { "type":"string", "format":"uri-reference" },
        "error_schema_uri":   { "type":"string", "format":"uri-reference" },
        "trace_id_format":    { "enum":["uuid","ulid","snowflake"] },
        "metrics_schema_uri": { "type":"string", "format":"uri-reference" }
      }
    },

    "dependencias": {
      "type":"object", "additionalProperties":false,
      "required":["runtime_min"],
      "properties": {
        "libs": { "type":"array", "items":{
          "type":"object", "additionalProperties":false,
          "required":["name","version","source"],
          "properties":{"name":{"type":"string"},"version":{"type":"string"},"source":{"type":"string"}}
        }},
        "runtime_min": { "type":"string" }
      }
    },

    "versioning": {
      "type":"object", "additionalProperties":false,
      "required":["min","max","mode"],
      "properties": {
        "min":  { "$ref":"#/definitions/semver" },
        "max":  { "$ref":"#/definitions/semver" },
        "mode": { "enum":["semver_strict","semver_loose","exact"] }
      }
    },

    "gobernanza_ref": {
      "type":"object", "additionalProperties":false,
      "required":["build_id","ledger"],
      "properties": {
        "build_id": { "type":"string", "pattern":"^BUILD-" },
        "ledger": {
          "type":"object", "additionalProperties":false,
          "required":["artifact_id","version"],
          "properties": {
            "artifact_id": { "$ref":"#/definitions/artifact_id" },
            "version":     { "$ref":"#/definitions/semver" },
            "ledger_uri":  { "type":"string", "format":"uri" }
          }
        }
      }
    },

    "recovery": {
      "type":"object", "additionalProperties":false,
      "properties": {
        "rollback_to":    { "type":"string" },
        "recovery_mode":  { "type":"string" },
        "state_preserve": { "type":"boolean" }
      }
    },

    "_meta_edicion": { "type":"object" }
  },

  "allOf": [
    {
      "if":   { "properties":{ "contrato":{ "properties":{"rol":{"const":"transform"}}, "required":["rol"] } } },
      "then": { "required":["transform"] }
    },
    {
      "if":   { "properties":{ "estado":{ "enum":["active","deprecated","blocked"] } } },
      "then": { "properties":{ "contract_hash":{ "pattern":"^sha256:[a-f0-9]{64}$" } } }
    }
  ]
}




