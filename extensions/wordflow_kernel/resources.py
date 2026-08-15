from .models import Resource


class ResourceRegistry:
    def __init__(self):
        self._items = {}

    def register(self, resource: Resource):
        if resource.resource_id in self._items:
            raise ValueError("resource already registered")
        self._items[resource.resource_id] = resource

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
        return self._items[resource_id]

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
