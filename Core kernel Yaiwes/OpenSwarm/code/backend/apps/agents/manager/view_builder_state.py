"""Cross-call view-builder render state, shared between the agent loop (which runs the
capped render-retry) and the post-tool hook (which marks a session dirty after a frontend
write/install). Module-level singletons on purpose: the retry counter and dirty set must
persist across turns and be the SAME objects both readers mutate."""

from typing import Dict, Set

VIEW_BUILDER_RENDER_MAX_RETRIES = 2
# session_id -> consecutive view-builder render attempts (capped, then it gives up).
view_builder_render_retry_counts: Dict[str, int] = {}
# session_ids whose view-builder workspace was written/installed since the last render.
view_builder_dirty_sessions: Set[str] = set()
