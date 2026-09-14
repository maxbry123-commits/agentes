from __future__ import annotations

def yaiwes_persistence_step(payload=None):
    return {'schema':'yaiwes.internal.persistence/v1','source_id':'0013ad83d6fd45510f28a4a5a40d5cccdae61ced1a62907f6f4eb2efb8713aec','payload':dict(payload or {}),'status':'CHECKPOINTED'}
