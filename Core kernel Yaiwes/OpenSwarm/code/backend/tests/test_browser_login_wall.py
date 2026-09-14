"""The login-wall gate: what it must catch, and what it must stop catching.

This gate exists because the reveal finder once filled an Instagram login form and armed the page's
own submit as a "send". It is load-bearing and it fails safe, so the temptation is to leave it broad.

Broad turned out to have its own cost. Measured live 2026-07-31, substack.com declined as an auth
wall while the account was demonstrably signed in, which takes an entire site out of the write path
for as long as nobody notices. Sites print "Sign in to ..." in footers, upsells and embedded content
strips, and that copy is not evidence of a wall on a page that is also showing you your own account
menu. So the copy half is overridable by a signed-in affordance.

The password half used to be absolute, on the stated theory that "a real composer never shares a
page with a password field". The 2026-08-02 holdout run disproved it on the first site it tried:
pastebin.com serves `textbox "New Paste"` and a header `textbox "Password"` together, and this gate
refused the composer sitting right beside it. Every site with a header sign-in box was losing its
whole write path the same way. So the password half is overridable too, but only by the one thing
that actually disproves a wall: a reachable composer. The URL half stays absolute.
"""

from backend.apps.agents.browser import browser_send_parse as sp

SIGNED_IN = ('[1]<button "Account menu">\n'
             '[4]<link "Sign in to read more">\n'
             '[7]<textbox "Write a note">')


def test_a_signed_in_page_is_not_a_wall_just_because_it_says_sign_in():
    """The substack shape: login copy sitting next to proof you are already logged in."""
    assert not sp.looks_like_login_wall("https://substack.com/", SIGNED_IN)


def test_a_password_box_convicts_when_there_is_nowhere_to_write():
    """A signed-in affordance does NOT clear a password field. Whatever a password form is for, a
    post does not go in it, and 'but the user is logged in' is not a reason to start typing into
    one. Only a real composer clears it, and there is none here."""
    assert sp.looks_like_login_wall(
        "https://site.com/x", '[1]<button "Sign out">\n[3]<textbox "Password">')


PASTEBIN = ('[3]<textbox "New Paste">\n'
            '[9]<textbox "Password">\n'
            '[11]<button "Create New Paste">')


def test_a_header_login_box_does_not_wall_off_the_composer_beside_it():
    """Live on pastebin.com, 2026-08-02, the first holdout site ever run. The page hands anonymous
    users a paste box AND a login widget, and this gate declined the whole site. The composer is the
    disproof: if the thing the task needs is right there, nothing is walled off."""
    assert not sp.looks_like_login_wall("https://pastebin.com/", PASTEBIN)
    assert sp.login_wall_reason("https://pastebin.com/", PASTEBIN) == ""


def test_a_composer_never_overrides_the_login_url_itself():
    """The dangerous direction. A page AT the login URL is a wall even if something on it scans as a
    composer, because that something is a login field and filling it types credentials."""
    assert sp.looks_like_login_wall("https://accounts.google.com/v3/signin/identifier", PASTEBIN)
    assert "url:" in sp.login_wall_reason("https://x.com/i/flow/login", PASTEBIN)


def test_login_copy_still_convicts_with_nothing_to_weigh_against_it():
    """Without a signed-in affordance the copy is the only evidence there is, and it stands."""
    assert sp.looks_like_login_wall("https://site.com/x", '[4]<link "Log in to X to continue">')


def test_login_urls_are_still_walls_outright():
    """Unchanged, and not overridable: a login URL is the page's own declaration of what it is."""
    assert sp.looks_like_login_wall("https://x.com/i/flow/login", SIGNED_IN)
    assert sp.looks_like_login_wall("https://accounts.google.com/v3/signin/identifier", SIGNED_IN)


def test_the_decline_names_its_own_trigger():
    """The bool alone left a whole site declining with nothing to debug against: no amount of
    re-reading the regexes reproduced substack, because the reason was never written down."""
    assert "url:" in sp.login_wall_reason("https://x.com/i/flow/login", "")
    assert "password field:" in sp.login_wall_reason("https://site.com/x", '[3]<textbox "Password">')
    assert "copy:" in sp.login_wall_reason("https://site.com/x", "Log in to X to continue")
    assert sp.login_wall_reason("https://substack.com/", SIGNED_IN) == ""


def test_a_real_login_form_is_still_a_wall_even_though_email_is_not_a_password():
    """The dangerous direction for the structural veto. A sign-in page has TWO boxes, and only one
    is the password; if 'any non-password box clears the wall' were the rule, every login page on
    the internet would clear it and the agent would type a post into the email field. Auth-shaped
    names do not count as somewhere to write."""
    for form in (
        '[1]<textbox "Email">\n[2]<textbox "Password">',
        '[1]<textbox "Username">\n[2]<textbox "Password">',
        '[1]<textbox "Phone number">\n[2]<textbox "Password">\n[3]<textbox "Verification code">',
    ):
        assert sp.looks_like_login_wall("https://site.com/x", form), form
