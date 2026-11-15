"""Which control counts as a composer OPENER, and which must never be clicked as one.

The rule was exact names only ("Comment", "Message", ...), for a stated reason: a paid upsell like
"Send InMail" must never be reachable. That exactness also made it blind to every opener whose label
is a sentence. Measured live 2026-08-02: tiktok labels its button `Read or add comments 526
comments`, the match missed, and the site scored 0/4 while the aux model clicked at that very button
for 27.8s.

So the second half matches VERB + NOUN anywhere in the label, which keeps what exactness was buying:
a bare count has no verb, and an upsell has the wrong noun. Neither can reach a click through here.
"""

from backend.apps.agents.browser import browser_send_parse as sp


def test_an_opener_labelled_as_a_whole_sentence_is_still_an_opener():
    """tiktok, verbatim from the 2026-08-02 perception."""
    hit = sp.opener_index_in_state('[12]<button "Read or add comments 526 comments">')
    assert hit is not None and hit[0] == 12


def test_a_count_is_not_an_opener():
    """"526 comments" is a label on a number. Clicking things because they say "comments" is how a
    read turns into an action."""
    assert sp.opener_index_in_state('[12]<button "526 comments">') is None


def test_an_upsell_is_still_unreachable():
    """The reason the rule was exact in the first place. "Send InMail" costs money and is not a
    composer; the noun list is what keeps it out, so this test guards the noun list."""
    assert sp.opener_index_in_state('[4]<button "Send InMail">') is None
    assert sp.opener_index_in_state('[4]<button "Send gift">') is None
    assert sp.opener_index_in_state('[4]<button "Send tip">') is None


def test_a_destructive_control_is_not_an_opener():
    """"Delete comment" carries the noun but the wrong verb, and the verb list is what stops it."""
    assert sp.opener_index_in_state('[3]<button "Delete comment">') is None
    assert sp.opener_index_in_state('[3]<button "Report comment">') is None


def test_exact_names_still_win_unchanged():
    assert sp.opener_index_in_state('[3]<button "Comment">') is not None
    assert sp.opener_index_in_state('[3]<link "Message">') is not None


def test_two_candidates_stay_ambiguous():
    """A singleton or nothing. Picking one of two openers is a coin flip on which surface gets
    written to, and that is the class of bug that once filled a stranger's DM box."""
    assert sp.opener_index_in_state(
        '[3]<button "Add a comment">\n[9]<button "Write a reply">') is None


def test_the_exact_rule_is_preferred_over_the_phrase_rule():
    """A page carrying one exact opener AND other sentence-shaped candidates resolves to the exact
    one, instead of collapsing to ambiguous and losing a composer it could name precisely."""
    hit = sp.opener_index_in_state(
        '[3]<button "Comment">\n[9]<button "Read or add comments 526 comments">')
    assert hit is not None and hit[0] == 3
