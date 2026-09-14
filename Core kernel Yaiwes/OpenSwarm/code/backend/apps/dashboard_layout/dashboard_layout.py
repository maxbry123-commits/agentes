import json
import os
import logging
from contextlib import asynccontextmanager
from backend.config.Apps import SubApp
from backend.apps.dashboard_layout.models import DashboardLayout, DashboardLayoutUpdate

logger = logging.getLogger(__name__)

from backend.config.paths import DASHBOARD_LAYOUT_DIR as DATA_DIR

LAYOUT_FILE = os.path.join(DATA_DIR, "layout.json")


@asynccontextmanager
async def dashboard_layout_lifespan():
    os.makedirs(DATA_DIR, exist_ok=True)
    yield


dashboard_layout = SubApp("dashboard_layout", dashboard_layout_lifespan)


def p_default_layout() -> DashboardLayout:
    return DashboardLayout(cards={})


def load() -> DashboardLayout:
    if not os.path.exists(LAYOUT_FILE):
        return p_default_layout()
    try:
        with open(LAYOUT_FILE) as f:
            data = json.load(f)
        if "columns" in data and "cards" not in data:
            logger.info("Detected old column-based layout format, resetting to empty canvas")
            return p_default_layout()
        return DashboardLayout(**data)
    except Exception:
        logger.exception("Failed to load dashboard layout, returning default")
        return p_default_layout()


def save(layout: DashboardLayout):
    with open(LAYOUT_FILE, "w") as f:
        json.dump(layout.model_dump(), f, indent=2)


@dashboard_layout.router.get("")
async def get_layout():
    layout = load()
    return layout.model_dump()


@dashboard_layout.router.put("")
async def update_layout(body: DashboardLayoutUpdate):
    layout = DashboardLayout(cards=body.cards, view_cards=body.view_cards)
    save(layout)
    return layout.model_dump()
