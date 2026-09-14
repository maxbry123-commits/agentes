from __future__ import annotations

def yaiwes_persistence_step(payload=None):
    return {'schema':'yaiwes.internal.persistence/v1','source_id':'2ed5b3a1308cc6e6d431607ff7acd8a8cdb52c632a5b85cf8c97d7d8663a11cc','payload':dict(payload or {}),'status':'CHECKPOINTED'}
