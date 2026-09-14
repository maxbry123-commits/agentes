"""Coverage-Tests fuer ingest.py -- fehlende Pfade abdecken."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.memory.ingest import (
    IngestConfig,
    IngestPipeline,
    IngestResult,
    TextExtractor,
)

if TYPE_CHECKING:
    from pathlib import Path

# ============================================================================
# IngestResult
# ============================================================================


class TestIngestResult:
    def test_success_summary(self) -> None:
        r = IngestResult(
            file_path="/test.md",
            file_name="test.md",
            success=True,
            chunks_created=5,
            text_length=1000,
        )
        assert "test.md" in r.summary
        assert "5 Chunks" in r.summary

    def test_error_summary(self) -> None:
        r = IngestResult(
            file_path="/test.md",
            file_name="test.md",
            error="Format unknown",
        )
        assert "test.md" in r.summary
        assert "Format unknown" in r.summary


# ============================================================================
# TextExtractor
# ============================================================================


class TestTextExtractor:
    @pytest.fixture
    def extractor(self) -> TextExtractor:
        with patch.object(TextExtractor, "_init_media_pipeline"):
            ext = TextExtractor()
            ext._media_pipeline = None
            return ext

    @pytest.mark.asyncio
    async def test_extract_md(self, extractor: TextExtractor, tmp_path: Path) -> None:
        f = tmp_path / "test.md"
        f.write_text("# Hello", encoding="utf-8")
        result = await extractor.extract(f)
        assert "# Hello" in result

    @pytest.mark.asyncio
    async def test_extract_txt(self, extractor: TextExtractor, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello world", encoding="utf-8")
        result = await extractor.extract(f)
        assert "hello world" in result

    @pytest.mark.asyncio
    async def test_extract_csv(self, extractor: TextExtractor, tmp_path: Path) -> None:
        f = tmp_path / "data.csv"
        f.write_text("a,b,c\n1,2,3", encoding="utf-8")
        result = await extractor.extract(f)
        assert "a,b,c" in result

    @pytest.mark.asyncio
    async def test_extract_json(self, extractor: TextExtractor, tmp_path: Path) -> None:
        f = tmp_path / "data.json"
        f.write_text('{"key": "value"}', encoding="utf-8")
        result = await extractor.extract(f)
        assert "key" in result

    @pytest.mark.asyncio
    async def test_extract_xml(self, extractor: TextExtractor, tmp_path: Path) -> None:
        f = tmp_path / "data.xml"
        f.write_text("<root>hello</root>", encoding="utf-8")
        result = await extractor.extract(f)
        assert "root" in result

    @pytest.mark.asyncio
    async def test_unsupported_format(self, extractor: TextExtractor, tmp_path: Path) -> None:
        f = tmp_path / "test.xyz"
        f.write_text("data", encoding="utf-8")
        with pytest.raises(ValueError, match="Nicht unterstützt"):
            await extractor.extract(f)

    @pytest.mark.asyncio
    async def test_extract_html(self, extractor: TextExtractor, tmp_path: Path) -> None:
        f = tmp_path / "page.html"
        f.write_text(
            "<html><head><style>body{}</style></head>"
            "<body><script>alert(1)</script><p>Hello World</p></body></html>",
            encoding="utf-8",
        )
        try:
            result = await extractor.extract(f)
            assert "Hello World" in result
            assert "script" not in result
            assert "style" not in result
        except ImportError:
            pytest.skip("bs4 not installed")

    @pytest.mark.asyncio
    async def test_extract_pdf_no_pipeline_no_fitz(
        self, extractor: TextExtractor, tmp_path: Path
    ) -> None:
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF-1.4")
        with patch.dict("sys.modules", {"fitz": None}):
            with pytest.raises(IOError, match="PyMuPDF"):
                await extractor.extract(f)

    @pytest.mark.asyncio
    async def test_extract_docx_no_pipeline_no_docx(
        self, extractor: TextExtractor, tmp_path: Path
    ) -> None:
        f = tmp_path / "doc.docx"
        f.write_bytes(b"PK")
        with patch.dict("sys.modules", {"docx": None}):
            with pytest.raises(IOError, match="python-docx"):
                await extractor.extract(f)


# ============================================================================
# IngestPipeline
# ============================================================================


@pytest.fixture
def ingest_config(tmp_path: Path) -> IngestConfig:
    return IngestConfig(
        watch_dir=tmp_path / "ingest",
        processed_dir=tmp_path / "ingest" / "processed",
        failed_dir=tmp_path / "ingest" / "failed",
    )


@pytest.fixture
def pipeline(ingest_config: IngestConfig) -> IngestPipeline:
    with patch.object(TextExtractor, "_init_media_pipeline"):
        return IngestPipeline(config=ingest_config)


class TestIngestPipeline:
    def test_init_creates_dirs(self, ingest_config: IngestConfig) -> None:
        with patch.object(TextExtractor, "_init_media_pipeline"):
            IngestPipeline(config=ingest_config)
        assert ingest_config.watch_dir.exists()
        assert ingest_config.processed_dir.exists()
        assert ingest_config.failed_dir.exists()

    def test_file_hash(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")
        h = IngestPipeline._file_hash(f)
        assert isinstance(h, str)
        assert len(h) == 16

    @pytest.mark.asyncio
    async def test_ingest_file_not_found(self, pipeline: IngestPipeline, tmp_path: Path) -> None:
        result = await pipeline.ingest_file(tmp_path / "nonexistent.txt")
        assert not result.success
        assert "not_found" in result.error or "nicht gefunden" in result.error

    @pytest.mark.asyncio
    async def test_ingest_unsupported_format(
        self, pipeline: IngestPipeline, ingest_config: IngestConfig
    ) -> None:
        f = ingest_config.watch_dir / "test.xyz"
        f.write_text("data", encoding="utf-8")
        result = await pipeline.ingest_file(f)
        assert not result.success
        assert "Nicht unterstützt" in result.error

    @pytest.mark.asyncio
    async def test_ingest_too_large(
        self, pipeline: IngestPipeline, ingest_config: IngestConfig
    ) -> None:
        ingest_config.max_file_size_bytes = 10
        f = ingest_config.watch_dir / "big.txt"
        f.write_text("x" * 100, encoding="utf-8")
        result = await pipeline.ingest_file(f)
        assert not result.success
        assert "zu gro" in result.error.lower() or "file_too_large" in result.error

    @pytest.mark.asyncio
    async def test_ingest_duplicate(
        self, pipeline: IngestPipeline, ingest_config: IngestConfig
    ) -> None:
        f = ingest_config.watch_dir / "dup.md"
        f.write_text("content", encoding="utf-8")
        content_hash = IngestPipeline._file_hash(f)
        pipeline._processed_hashes.add(content_hash)
        result = await pipeline.ingest_file(f)
        assert not result.success
        assert "Bereits verarbeitet" in result.error

    @pytest.mark.asyncio
    async def test_ingest_success_no_memory(
        self, pipeline: IngestPipeline, ingest_config: IngestConfig
    ) -> None:
        f = ingest_config.watch_dir / "test.md"
        f.write_text("# Hello World\nContent here.", encoding="utf-8")
        result = await pipeline.ingest_file(f)
        assert result.success
        assert result.chunks_created >= 1

    @pytest.mark.asyncio
    async def test_ingest_success_with_memory(
        self, pipeline: IngestPipeline, ingest_config: IngestConfig
    ) -> None:
        mock_memory = MagicMock()
        mock_memory.index_text.return_value = 3
        pipeline._memory = mock_memory

        f = ingest_config.watch_dir / "test2.md"
        f.write_text("# Test\nSome content.", encoding="utf-8")
        result = await pipeline.ingest_file(f)
        assert result.success
        assert result.chunks_created == 3

    @pytest.mark.asyncio
    async def test_ingest_empty_text(
        self, pipeline: IngestPipeline, ingest_config: IngestConfig
    ) -> None:
        f = ingest_config.watch_dir / "empty.md"
        f.write_text("   ", encoding="utf-8")
        result = await pipeline.ingest_file(f)
        assert not result.success
        assert result.error is not None
        assert (
            "Kein Text" in result.error
            or "empty" in result.error.lower()
            or "kein" in result.error.lower()
        )

    @pytest.mark.asyncio
    async def test_ingest_extraction_error(
        self, pipeline: IngestPipeline, ingest_config: IngestConfig
    ) -> None:
        f = ingest_config.watch_dir / "bad.md"
        f.write_text("content", encoding="utf-8")
        pipeline._extractor.extract = AsyncMock(side_effect=RuntimeError("extract fail"))
        result = await pipeline.ingest_file(f)
        assert not result.success
        assert "extract fail" in result.error

    @pytest.mark.asyncio
    async def test_scan_and_ingest_empty(self, pipeline: IngestPipeline) -> None:
        results = await pipeline.scan_and_ingest()
        assert results == []

    @pytest.mark.asyncio
    async def test_scan_and_ingest_with_files(
        self, pipeline: IngestPipeline, ingest_config: IngestConfig
    ) -> None:
        (ingest_config.watch_dir / "a.md").write_text("# A", encoding="utf-8")
        (ingest_config.watch_dir / "b.txt").write_text("B content", encoding="utf-8")
        results = await pipeline.scan_and_ingest()
        assert len(results) == 2

    def test_stop(self, pipeline: IngestPipeline) -> None:
        pipeline._running = True
        pipeline.stop()
        assert not pipeline._running

    def test_stats(self, pipeline: IngestPipeline, ingest_config: IngestConfig) -> None:
        (ingest_config.watch_dir / "pending.md").write_text("x", encoding="utf-8")
        stats = pipeline.stats()
        assert stats["pending"] >= 1
        assert "watch_dir" in stats
        assert isinstance(stats["supported_formats"], list)
