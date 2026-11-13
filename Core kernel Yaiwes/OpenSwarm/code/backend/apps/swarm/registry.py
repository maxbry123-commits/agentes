"""Maps an EntityType to the Exportable that handles it, and the leaves-first
order import walks. Adding a shareable type is one entry here plus its module."""
from backend.apps.swarm.entities.apps import AppExportable
from backend.apps.swarm.entities.dashboards import DashboardExportable
from backend.apps.swarm.entities.modes import ModeExportable
from backend.apps.swarm.entities.SessionExportable import SessionExportable
from backend.apps.swarm.entities.skills import SkillExportable
from backend.apps.swarm.entities.workflows import WorkflowExportable
from backend.apps.swarm.models import EntityType

REGISTRY: dict[EntityType, type] = {
    EntityType.skill: SkillExportable,
    EntityType.app: AppExportable,
    EntityType.workflow: WorkflowExportable,
    EntityType.mode: ModeExportable,
    EntityType.session: SessionExportable,
    EntityType.dashboard: DashboardExportable,
}

# Leaves first: a dependency must import before whatever references it.
IMPORT_ORDER = [
    EntityType.skill,
    EntityType.mode,
    EntityType.session,
    EntityType.app,
    EntityType.workflow,
    EntityType.dashboard,
]


def get_exportable(etype: EntityType) -> type | None:
    return REGISTRY.get(etype)
