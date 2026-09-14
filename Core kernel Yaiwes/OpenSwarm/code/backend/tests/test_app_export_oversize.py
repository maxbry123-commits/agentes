"""Regression guard for the oversize-file corruption fix (PR #106).

The bug: the workspace poll read substituted any file over the per-file cap with
a `// [openswarm] file truncated...` marker; the frontend treated that marker as
real content and round-tripped it back into storage on save/export/snapshot,
permanently destroying the real source of oversize files. These tests pin the
three layers of the fix: omit-on-read (no stub), refuse-shrink-on-write (disk
boundary), and a full read->write round-trip that proves the bytes survive.
"""

from pathlib import Path

from backend.apps.outputs.workspace_io import (
    walk_directory,
    would_shrink_oversize_file,
)

MARKER = "// [openswarm] file truncated"
# Comfortably above the workspace poll cap (currently 2 MB) without importing the
# module-private constant. If the cap is ever raised past this, bump it here too.
OVERSIZE = 3 * 1024 * 1024


def test_walk_omits_oversize_and_never_stubs_content(tmp_path: Path) -> None:
    small = tmp_path / "app.py"
    small.write_text("print('hi')\n")
    big = tmp_path / "bundle.js"
    big.write_text("x" * OVERSIZE)

    files, truncated = walk_directory(str(tmp_path))

    assert files["app.py"] == "print('hi')\n"
    # Oversize file is reported out-of-band, NOT substituted with a stub.
    assert "bundle.js" not in files
    assert truncated["bundle.js"] >= OVERSIZE
    # The corrupting marker must never appear as content anywhere.
    assert all(MARKER not in c for c in files.values())


def test_would_shrink_guard_refuses_only_a_shrinking_oversize_write(tmp_path: Path) -> None:
    big = tmp_path / "bundle.js"
    big.write_text("y" * OVERSIZE)

    # A small marker/stub write would shrink a known-oversize file -> refuse.
    assert would_shrink_oversize_file(str(big), MARKER) is True
    # A legitimately larger rewrite is allowed.
    assert would_shrink_oversize_file(str(big), "z" * (OVERSIZE + 4096)) is False
    # A normal under-cap file is never guarded.
    small = tmp_path / "app.py"
    small.write_text("print('hi')")
    assert would_shrink_oversize_file(str(small), "x") is False
    # A nonexistent path is never guarded.
    assert would_shrink_oversize_file(str(tmp_path / "nope.js"), "x") is False


def test_oversize_bytes_survive_read_then_writeback_roundtrip(tmp_path: Path) -> None:
    big = tmp_path / "bundle.js"
    original = "A" * OVERSIZE
    big.write_text(original)

    # READ leg: the poll omits it, so a client never even holds the bytes.
    files, truncated = walk_directory(str(tmp_path))
    assert "bundle.js" not in files and "bundle.js" in truncated

    # WRITE leg: a client that round-trips a stub is refused at the disk boundary.
    if not would_shrink_oversize_file(str(big), MARKER):
        big.write_text(MARKER)

    assert big.read_text() == original
    assert len(big.read_text()) == OVERSIZE
