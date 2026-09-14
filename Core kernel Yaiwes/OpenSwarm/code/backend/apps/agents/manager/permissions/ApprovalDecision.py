"""The user's resolution of a tool-approval request, sent back from the frontend over the
websocket. A fixed-shape record (not an open-ended map), so it's a model, not a dict."""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class ApprovalDecision(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    # 'allow' or 'deny'. The rest only refine an allow.
    behavior: Optional[str] = None
    # The tool input the user may have edited before allowing.
    updated_input: Optional[object] = None
    # A one-off reason shown when the user denies.
    message: Optional[str] = None
    # Persist this sensitive-path pattern as trusted so it stops prompting.
    trust_pattern: Optional[bool] = None
    # Persist the tool's policy as always-allow for the rest of the run.
    set_always_allow: Optional[bool] = None
