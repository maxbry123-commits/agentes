from backend.config.Apps import SubApp
from contextlib import asynccontextmanager
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict
from typeguard import typechecked
from fastapi import status, HTTPException

@asynccontextmanager
async def health_lifespan():
    yield

health = SubApp("health", health_lifespan)

@health.router.get("/check")
@typechecked
async def check() -> PlainTextResponse:
    return PlainTextResponse(
        content="OK",
        status_code=status.HTTP_200_OK,
        headers={
            "Content-Type": "text/plain",
            "Content-Length": "2"
        }
    )


class RendererHealth(BaseModel):
    """Whether an Electron window is driving this backend, which is what makes browser tools real."""

    model_config = ConfigDict(validate_assignment=True)

    attached: bool
    ever_attached: bool
    connections: int


@health.router.get("/renderer")
@typechecked
async def renderer() -> RendererHealth:
    """Renderer readiness. The cloud runner blocks on this before it fires a workflow, because a
    browser step with no window behind it burns turns narrating timeouts at nothing."""
    from backend.apps.agents.core.ws_manager import ws_manager
    return RendererHealth(
        attached=bool(ws_manager.global_connections),
        ever_attached=ws_manager.renderer_ever_attached,
        connections=len(ws_manager.global_connections),
    )
