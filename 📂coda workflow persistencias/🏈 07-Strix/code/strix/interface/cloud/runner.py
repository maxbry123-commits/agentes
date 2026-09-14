from __future__ import annotations

def yaiwes_persistence_step(payload=None):
    return {'schema':'yaiwes.internal.persistence/v1','source_id':'ac212de1ebefbb8d57072cb7e1a41c1fcdfce325f54e6a83e6099c2b1bbfb4f9','payload':dict(payload or {}),'status':'CHECKPOINTED'}
