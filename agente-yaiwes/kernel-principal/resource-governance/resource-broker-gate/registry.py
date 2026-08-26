from wordflow_kernel.models import Resource


class ResourceRegistry:
    def __init__(self):
        self._items = {}

    def register(self, name, meta=None):
        if isinstance(name, Resource):
            resource = name
        else:
            meta = dict(meta or {})
            resource = Resource(
                resource_id=str(name),
                kind=str(meta.get("kind") or "generic"),
                source=str(meta.get("source") or ""),
                version=meta.get("version"),
                sha=meta.get("sha"),
                license=meta.get("license"),
                capabilities=tuple(meta.get("capabilities") or ()),
                metadata=meta,
            )
        if resource.resource_id in self._items:
            raise ValueError("resource already registered")
        self._items[resource.resource_id] = resource
        return resource

    def resolve(self, capability, kinds=None):
        kinds = set(kinds or [])
        candidates = []
        for r in self._items.values():
            if kinds and r.kind not in kinds:
                continue
            if capability in r.capabilities:
                candidates.append(r)
        return sorted(candidates, key=lambda x: (x.version or "", x.resource_id), reverse=True)

    def get(self, resource_id):
        return self._items.get(resource_id)

    def list(self):
        return self.list_ids()

    def list_ids(self):
        return sorted(self._items.keys())


class SkillResolver:
    def __init__(self, registry):
        self.registry = registry

    def resolve(self, capability):
        return self.registry.resolve(capability, ["skill"])


class DatasetResolver:
    def __init__(self, registry):
        self.registry = registry

    def resolve(self, capability):
        return self.registry.resolve(capability, ["dataset"])


class AdapterResolver:
    def __init__(self, registry):
        self.registry = registry

    def resolve(self, capability):
        return self.registry.resolve(capability, ["adapter", "connector"])


if __name__ == "__main__":
    reg = ResourceRegistry()
    reg.register("alpha", {"kind": "skill"})
    reg.register("beta", {"kind": "dataset"})
    assert len(reg.list()) == 2
    assert reg.get("alpha") is not None
    assert reg.get("missing") is None
    print("ok", reg.list())
