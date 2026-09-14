"""A send must land on the surface the task asked for, or not at all.

Getting this wrong is not a failed action. Measured live 2026-07-31 in a dry-run sweep: the task
"write a comment on the first post" walked to instagram.com/<someone>/, took that profile's
"Message" opener and filled "Message...". The only reason it did not DM a stranger the text is that
the run was armed with OSW_SENDSCRIPT_DRYRUN=1.

So the real phrasings from that sweep are pinned here, both the ones that must be refused and the
ones that must keep working, because a guard this blunt breaks whole sites when it drifts.
"""

from backend.apps.agents.browser import browser_send_parse as sp

# Verbatim from the coverage harness, which is what actually reaches the send script.
X = 'Go to x.com and post this tweet, exactly: "coverage probe alpha"'
LINKEDIN = 'Go to linkedin.com and create a post with exactly this text: "coverage probe alpha"'
INSTAGRAM = 'Go to instagram.com and write a comment "coverage probe alpha" on the first post'
GMAIL = 'Go to gmail and start a new email with the body "coverage probe alpha"'
TWITCH = 'Go to twitch.tv, open the first live channel, and write "coverage probe alpha" in chat'
YOUTUBE = 'Go to youtube.com, open the first video, and write the comment "coverage probe alpha"'


def test_the_instagram_dm_that_started_this():
    assert sp.surface_mismatch(INSTAGRAM, "Message") is True
    assert sp.surface_mismatch(INSTAGRAM, "Message...") is True


def test_no_task_that_never_mentions_messaging_may_reach_a_dm_box():
    for task in (X, LINKEDIN, INSTAGRAM, YOUTUBE):
        for surface in ("Message", "Message...", "Direct message", "Send a DM", "New message"):
            assert sp.surface_mismatch(task, surface) is True, (task, surface)


def test_a_task_that_does_ask_to_message_still_gets_its_composer():
    # Gmail's box is literally named "Message Body" and twitch's chat input is "Send a message";
    # refusing those would take both sites out of the write path entirely.
    assert sp.surface_mismatch(GMAIL, "Message Body") is False
    assert sp.surface_mismatch(TWITCH, "Send a message") is False
    assert sp.surface_mismatch("DM @someone \"hi\"", "Message...") is False
    assert sp.surface_mismatch("text tyler hello", "Write a message") is False
    # "reply" reads as public, so this one needs the word inbox to survive.
    assert sp.surface_mismatch("Reply to her inbox thread with \"hi\"", "Message") is False


def test_the_original_post_versus_comment_rule_is_untouched():
    assert sp.surface_mismatch(LINKEDIN, "Text editor for creating comment") is True
    assert sp.surface_mismatch(X, "Add a comment") is True
    # A task that ASKS to comment keeps its comment box.
    assert sp.surface_mismatch(YOUTUBE, "Add a comment") is False
    assert sp.surface_mismatch(INSTAGRAM, "Add a comment...") is False


def test_the_composers_we_actually_want_are_never_refused():
    assert sp.surface_mismatch(X, "Post text") is False
    assert sp.surface_mismatch(LINKEDIN, "Share") is False
    assert sp.surface_mismatch(LINKEDIN, "start a post") is False
    assert sp.surface_mismatch(TWITCH, "Chat") is False


def test_a_task_asking_for_neither_a_post_nor_a_comment_is_left_alone():
    # Nothing to contradict, so the guard stays out of it rather than guessing.
    for surface in ("Message", "Message...", "New message"):
        assert sp.surface_mismatch("send tyler hello", surface) is False, surface


def test_empty_inputs_never_refuse():
    assert sp.surface_mismatch("", "") is False
    assert sp.surface_mismatch(X, "") is False
    assert sp.surface_mismatch("", "Message") is False
