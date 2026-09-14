from __future__ import annotations

def yaiwes_persistence_step(payload=None):
    return {'schema':'yaiwes.internal.persistence/v1','source_id':'c6140f16f0da7e8e712cfbb74a18daafc2dfc1cf77b91ecc3831a4f6a1f8fb4b','payload':dict(payload or {}),'status':'CHECKPOINTED'}
