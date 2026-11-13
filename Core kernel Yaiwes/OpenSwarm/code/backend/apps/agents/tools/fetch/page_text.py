"""Turn a fetched response body into text a model can actually read.

WebFetch used to hand anything non-HTML straight to the model as `resp.text`,
so fetching a PDF posted ~173KB-2MB of `%PDF-1.5` binary into the context
window: pure cost, zero information, and it pushed real content out. PDFs now
get their text layer extracted, and anything else that isn't textual is refused
with a message that says what it was instead of dumping its bytes."""

import io
from typing import Optional

from pydantic import BaseModel, ConfigDict
from typeguard import typechecked

# A 2.2MB, 15-page paper extracts to ~40K chars in 0.8s; this bounds a pathological book-sized PDF.
MAX_PDF_PAGES = 100
P_PDF_MAGIC = b"%PDF"
P_TEXTUAL_HINTS = ("text/", "json", "xml", "javascript", "csv", "yaml", "markdown")


class PageText(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    text: str
    kind: str


@typechecked
def looks_like_pdf(content_type: str, content: bytes) -> bool:
    """Servers mislabel PDFs constantly, so the magic bytes get the final say."""
    return "pdf" in content_type.lower() or content[:4].startswith(P_PDF_MAGIC)


@typechecked
def p_is_textual(content_type: str, content: bytes) -> bool:
    if any(hint in content_type.lower() for hint in P_TEXTUAL_HINTS):
        return True
    sample = content[:4096]
    if not sample:
        return True
    if b"\x00" in sample:
        return False
    printable = sum(1 for byte in sample if byte >= 32 or byte in (9, 10, 13))
    return printable / len(sample) > 0.9


@typechecked
def p_describe_size(content: bytes) -> str:
    kb = len(content) / 1024
    return f"{kb:.0f} KB" if kb < 1024 else f"{kb / 1024:.1f} MB"


@typechecked
def extract_pdf_text(content: bytes) -> Optional[str]:
    """The PDF's text layer, or None when there isn't one we can read."""
    try:
        from pypdf import PdfReader
    except Exception:
        return None
    try:
        reader = PdfReader(io.BytesIO(content))
        pages = reader.pages[:MAX_PDF_PAGES]
        chunks = [(page.extract_text() or "").strip() for page in pages]
    except Exception:
        return None
    body = "\n\n".join(chunk for chunk in chunks if chunk).strip()
    if not body:
        return None
    if len(reader.pages) > MAX_PDF_PAGES:
        body += f"\n\n... (first {MAX_PDF_PAGES} of {len(reader.pages)} pages)"
    return body


@typechecked
def body_to_text(content_type: str, content: bytes, raw_text: str) -> PageText:
    """Readable text plus what it came from; never raw binary."""
    if looks_like_pdf(content_type, content):
        extracted = extract_pdf_text(content)
        if extracted:
            return PageText(text=extracted, kind="pdf")
        return PageText(
            text=(
                f"This URL is a PDF ({p_describe_size(content)}) with no extractable text layer; "
                "it is probably a scan or is encrypted. Nothing was read from it."
            ),
            kind="pdf_unreadable",
        )
    if p_is_textual(content_type, content):
        return PageText(text=raw_text, kind="text")
    return PageText(
        text=(
            f"This URL is not a readable document: {content_type or 'unknown type'}, "
            f"{p_describe_size(content)} of binary data. Nothing was read from it."
        ),
        kind="binary",
    )
