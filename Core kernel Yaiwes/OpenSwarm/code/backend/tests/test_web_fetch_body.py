"""WebFetch must never post raw binary into the model's context.

The field bug: fetching a PDF handed the model megabytes of `%PDF-1.5`
gibberish, which cost real money, told it nothing, and pushed real content out
of the window. Same class for images and any other binary body.
"""

import pytest

import backend.apps.agents.tools.fetch.wayback as WB
from backend.apps.agents.tools.fetch.page_text import (
    MAX_PDF_PAGES,
    body_to_text,
    extract_pdf_text,
    looks_like_pdf,
)
from backend.apps.agents.tools.browser_http import HttpReply
from backend.apps.agents.tools.fetch.wayback import fetch_wayback, snapshot_date


def p_minimal_pdf(text: str = "Hello from a real PDF") -> bytes:
    """A genuine 600-byte one-page PDF with a real font resource and xref table."""
    stream = f"BT /F1 18 Tf 20 100 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode() + b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


# ------------------------------------------------------------------ PDF


def test_pdf_is_detected_by_magic_bytes_not_just_the_header():
    # Servers mislabel PDFs as text/html constantly.
    assert looks_like_pdf("text/html", b"%PDF-1.7\n...") is True
    assert looks_like_pdf("application/pdf", b"") is True
    assert looks_like_pdf("text/html", b"<!doctype html>") is False


def test_a_real_pdf_yields_its_text_not_its_bytes():
    raw = p_minimal_pdf("Attention Is All You Need")
    out = body_to_text("application/pdf", raw, raw.decode("latin-1"))
    assert out.kind == "pdf"
    assert "Attention Is All You Need" in out.text
    assert "%PDF" not in out.text


def test_a_pdf_with_no_text_layer_says_so_instead_of_dumping_it():
    fake = b"%PDF-1.4\n" + b"\x00\x01\x02" * 500
    out = body_to_text("application/pdf", fake, "ignored")
    assert out.kind == "pdf_unreadable"
    assert "no extractable text layer" in out.text
    assert "\x00" not in out.text


def test_extract_returns_none_rather_than_raising_on_garbage():
    assert extract_pdf_text(b"not a pdf at all") is None


def test_page_cap_is_bounded():
    assert 0 < MAX_PDF_PAGES <= 500


# ------------------------------------------------------------------ other binaries


def test_an_image_is_refused_with_a_description_not_its_bytes():
    png = b"\x89PNG\r\n\x1a\n" + bytes(range(256)) * 40
    out = body_to_text("image/png", png, png.decode("latin-1"))
    assert out.kind == "binary"
    assert "image/png" in out.text
    assert "\x89PNG" not in out.text
    assert len(out.text) < 400


def test_json_and_plain_text_still_pass_through_verbatim():
    payload = '{"stars": 68000, "name": "cpython"}'
    out = body_to_text("application/json", payload.encode(), payload)
    assert out.kind == "text"
    assert out.text == payload


def test_mislabelled_text_is_still_treated_as_text():
    # application/octet-stream on a plain-text file is common; the bytes get the final say.
    payload = "name,value\nalpha,1\nbeta,2\n"
    out = body_to_text("application/octet-stream", payload.encode(), payload)
    assert out.kind == "text"
    assert out.text == payload


# ------------------------------------------------------------------ wayback


def p_wayback_reply(monkeypatch, status: int, text: str, url: str):
    async def p_req(target, **kw):
        return HttpReply(status=status, text=text, content=text.encode(),
                         content_type="text/html", url=url)
    monkeypatch.setattr(WB, "browser_request", p_req)


P_ARCHIVED = "<html><body><article>" + ("The original article text. " * 40) + "</article></body></html>"


def test_snapshot_date_is_read_from_the_archive_url():
    assert snapshot_date("https://web.archive.org/web/20260728200922/https://x.example/") == "2026-07-28"
    assert snapshot_date("https://web.archive.org/web/2/https://x.example/") is None


@pytest.mark.asyncio
async def test_a_dead_link_is_answered_from_the_archive(monkeypatch):
    p_wayback_reply(monkeypatch, 200, P_ARCHIVED,
                    "https://web.archive.org/web/20260508082837/https://gone.example/post")
    out = await fetch_wayback("https://gone.example/post")
    assert out is not None
    assert "The original article text." in out
    # the model must know it is reading a snapshot, and from when
    assert "2026-05-08" in out
    assert "Archived copy" in out


@pytest.mark.asyncio
async def test_no_snapshot_reads_as_no_answer(monkeypatch):
    p_wayback_reply(monkeypatch, 404, "not archived",
                    "https://web.archive.org/web/2/https://gone.example/post")
    assert await fetch_wayback("https://gone.example/post") is None


@pytest.mark.asyncio
async def test_a_stub_snapshot_is_not_passed_off_as_the_page(monkeypatch):
    p_wayback_reply(monkeypatch, 200, "<html><body>tiny</body></html>",
                    "https://web.archive.org/web/20260101000000/https://x.example/")
    assert await fetch_wayback("https://x.example/") is None


@pytest.mark.asyncio
async def test_a_redirect_off_the_archive_is_refused(monkeypatch):
    """We hand the archive a caller-supplied URL, so we confirm where we landed."""
    p_wayback_reply(monkeypatch, 200, P_ARCHIVED, "http://127.0.0.1:8324/api/settings")
    assert await fetch_wayback("https://x.example/") is None
