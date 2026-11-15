"""Write operations: the things a logged-in human does on Reddit.

Posts, comments, edits, deletes, votes, saves, subscriptions, and DMs, all via
the user's own session. Each call goes through the rate limiter's write buckets.
"""

import json
import re
from typing import Any, Dict, Optional

from backend.apps.reddit_mcp_shim.reddit_http import RedditError, api

# Reddit's own id shapes echoed back in a write response: a "fullname" (t1_ comment,
# t3_ post, ...) and a comment/post permalink. Used to recover a real receipt when the
# structured envelope is absent (the legacy "jquery" response shape, see p_receipt).
P_FULLNAME_RE = re.compile(r"t[1-6]_[0-9a-z]+", re.I)
P_PERMALINK_RE = re.compile(r"/r/[A-Za-z0-9_]+/comments/[A-Za-z0-9_/\-]+")


def p_check(resp: dict) -> dict:
    """Raise on Reddit's json.errors envelope; return the inner data otherwise."""
    j = (resp or {}).get("json", resp or {})
    errors = j.get("errors") if isinstance(j, dict) else None
    if errors:
        raise RedditError("; ".join(" ".join(str(p) for p in e) for e in errors))
    return j.get("data", {}) if isinstance(j, dict) else {}


def p_receipt(resp: Any, kind: str, exclude: str = "") -> Dict[str, Optional[str]]:
    """The just-created thing's own fullname + permalink, robust to Reddit's TWO write
    response shapes. Modern api_type=json returns data.things[0].data (comment) or the
    fields at data top-level (submit); the LEGACY web endpoint returns a 'jquery' command
    array with neither, so the naive parse came back empty = the receipt='ok' bug. Prefer
    the structured field; else scan the echoed response for a fullname of the right kind
    (t1 comment / t3 post), never the parent id we're replying to."""
    data = p_check(resp)  # raises on Reddit's real error envelope
    d: Dict[str, Any] = {}
    if isinstance(data, dict):
        things = data.get("things")
        if things and isinstance(things[0], dict):
            d = things[0].get("data", {}) or {}
        elif data.get("name") or data.get("id") or data.get("url"):
            d = data
    if d.get("name") or d.get("permalink") or d.get("url"):
        return {"id": d.get("name") or d.get("id"),
                "permalink": d.get("permalink") or d.get("url")}
    blob = json.dumps(resp, default=str)
    ex = (exclude or "").lower()
    name = next((m for m in P_FULLNAME_RE.findall(blob)
                 if m.lower().startswith(kind.lower()) and m.lower() != ex), None)
    pm = P_PERMALINK_RE.search(blob)
    return {"id": name, "permalink": pm.group(0) if pm else None}


def p_dir(direction: str) -> int:
    return {"up": 1, "upvote": 1, "down": -1, "downvote": -1, "clear": 0, "none": 0, "unvote": 0}.get(
        (direction or "").lower(), 0
    )


def submit(subreddit: str, title: str, kind: str, text: str, url: str, nsfw: bool, spoiler: bool, send_replies: bool) -> dict:
    form = {
        "sr": subreddit,
        "title": title,
        "kind": "self" if kind != "link" else "link",
        "nsfw": "true" if nsfw else "false",
        "spoiler": "true" if spoiler else "false",
        "sendreplies": "true" if send_replies else "false",
        "resubmit": "true",
        "api_type": "json",
    }
    form["url" if kind == "link" else "text"] = url if kind == "link" else text
    r = p_receipt(api("POST", "/api/submit", form=form, action="submit"), kind="t3")
    return {"id": r["id"], "url": r["permalink"]}


def comment(parent_id: str, text: str) -> dict:
    resp = api("POST", "/api/comment", form={"thing_id": parent_id, "text": text, "api_type": "json"}, action="comment")
    r = p_receipt(resp, kind="t1", exclude=parent_id)
    return {"id": r["id"], "permalink": r["permalink"]}


def edit(thing_id: str, text: str) -> dict:
    resp = api("POST", "/api/editusertext", form={"thing_id": thing_id, "text": text, "api_type": "json"}, action="comment")
    r = p_receipt(resp, kind=(thing_id[:2] or "t1"), exclude="")
    return {"id": r["id"] or thing_id, "edited": True}


def delete(thing_id: str) -> dict:
    api("POST", "/api/del", form={"id": thing_id}, action="save")
    return {"id": thing_id, "deleted": True}


def vote(thing_id: str, direction: str) -> dict:
    d = p_dir(direction)
    api("POST", "/api/vote", form={"id": thing_id, "dir": d}, action="vote")
    return {"id": thing_id, "dir": d}


def save(thing_id: str, unsave: bool) -> dict:
    api("POST", "/api/unsave" if unsave else "/api/save", form={"id": thing_id}, action="save")
    return {"id": thing_id, "saved": not unsave}


def subscribe(subreddit: str, unsubscribe: bool) -> dict:
    api("POST", "/api/subscribe", form={"sr_name": subreddit, "action": "unsub" if unsubscribe else "sub"}, action="subscribe")
    return {"subreddit": subreddit, "subscribed": not unsubscribe}


def compose(to: str, subject: str, text: str) -> dict:
    p_check(api("POST", "/api/compose", form={"to": to, "subject": subject, "text": text, "api_type": "json"}, action="compose"))
    return {"to": to, "sent": True}
