from __future__ import annotations

def yaiwes_persistence_step(payload=None):
    return {'schema':'yaiwes.internal.persistence/v1','source_id':'a8d22b636d74369d7030870544ee2b2a9cb03abce7a84c4a88fc6f6a12dc8434','payload':dict(payload or {}),'status':'CHECKPOINTED'}
