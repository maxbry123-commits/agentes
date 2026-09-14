"""Unit tests for the learn-on-first-write / replay-on-repeat recipe module.
Network mocked at route_write.issue_request; disk redirected to tmp_path."""

import json
from typing import Any, Dict

import pytest

from backend.apps.agents.browser import browser_write_recipes as wr
from backend.apps.agents.browser import route_write


@pytest.fixture(autouse=True)
def recipes_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(wr, "p_dir", lambda: str(tmp_path))


P_X_BODY = {
    "variables": {"tweet_text": "hello from the test", "dark_request": False,
                  "media": {"media_entities": [], "possibly_sensitive": False}},
    "features": {"tweetypie_unmention_optimization_enabled": True, "longform_notetweets_consumption_enabled": True},
    "queryId": "AbCdEf123456",
}


def p_routes(body: Dict[str, Any]) -> list:
    return [
        {"method": "GET", "template": "https://x.com/i/api/graphql/{id}/HomeTimeline", "example": "", "lastBody": ""},
        {"method": "POST", "template": "https://x.com/i/api/graphql/{id}/CreateTweet",
         "example": "https://x.com/i/api/graphql/AbCdEf123456/CreateTweet", "lastBody": json.dumps(body)},
    ]


def test_learn_finds_payload_slot_and_saves():
    r = wr.learn_recipe("x.com", "hello from the test", p_routes(P_X_BODY))
    assert r is not None
    assert r.payload_path == "$.variables.tweet_text"
    assert wr.SENTINEL in r.body_template
    assert "hello from the test" not in r.body_template
    assert wr.recipe_for("x.com") is not None


def test_learn_refuses_substring_and_short_payloads():
    body = {"variables": {"tweet_text": "prefix hello from the test suffix"}}
    assert wr.learn_recipe("x.com", "hello from the test", p_routes(body)) is None
    assert wr.learn_recipe("x.com", "hi", p_routes(P_X_BODY)) is None


def test_learn_redacts_secret_leaves_but_keeps_structure():
    body = {"variables": {"tweet_text": "hello from the test"}, "csrfish": "a1B2c3D4e5F6g7H8i9J0kk"}
    r = wr.learn_recipe("x.com", "hello from the test", p_routes(body))
    parsed = json.loads(r.body_template)
    assert parsed["csrfish"] == "<redacted>"
    assert parsed["variables"]["tweet_text"] == wr.SENTINEL


def test_build_body_substitutes_new_payload_only():
    r = wr.learn_recipe("x.com", "hello from the test", p_routes(P_X_BODY))
    body = wr.build_body(r, "a brand new tweet")
    assert body["variables"]["tweet_text"] == "a brand new tweet"
    assert body["queryId"] == "AbCdEf123456"
    r.body_template = json.dumps({"variables": {"tweet_text": "no sentinel here"}})
    assert wr.build_body(r, "x") is None


@pytest.mark.asyncio
async def test_replay_ok_bumps_wins_and_returns_receipt(monkeypatch):
    monkeypatch.setenv("OSW_ROUTE_WRITE", "1")
    r = wr.learn_recipe("x.com", "hello from the test", p_routes(P_X_BODY))
    monkeypatch.setattr(route_write, "get_session", lambda d: ("auth=1; ct0=abc", "UA"))
    monkeypatch.setattr(route_write, "issue_request",
                        lambda m, u, b, h: (200, json.dumps({"data": {"rest_id": "999"}})))
    out = await wr.replay_recipe(r, "new text", "https://x.com")
    assert out["ok"] is True and out["receipt"] == "999"
    assert wr.recipe_for("x.com").wins == 1


@pytest.mark.asyncio
async def test_replay_miss_bumps_and_drops_after_cap(monkeypatch):
    monkeypatch.setenv("OSW_ROUTE_WRITE", "1")
    wr.learn_recipe("x.com", "hello from the test", p_routes(P_X_BODY))
    monkeypatch.setattr(route_write, "get_session", lambda d: ("auth=1", "UA"))
    monkeypatch.setattr(route_write, "issue_request", lambda m, u, b, h: (404, "gone"))
    for i in range(wr.MAX_MISSES):
        r = wr.recipe_for("x.com")
        assert r is not None, f"recipe gone before miss {i + 1}"
        out = await wr.replay_recipe(r, "t", "https://x.com")
        assert out["ok"] is False
    assert wr.recipe_for("x.com") is None  # stale recipe self-evicted


@pytest.mark.asyncio
async def test_replay_respects_flag_off(monkeypatch):
    monkeypatch.delenv("OSW_ROUTE_WRITE", raising=False)
    r = wr.learn_recipe("x.com", "hello from the test", p_routes(P_X_BODY))
    out = await wr.replay_recipe(r, "t", "https://x.com")
    assert out["ok"] is False and "disarmed" in out["error"]
