#!/usr/bin/env python3
"""Extract a local PDF manual into searchable Markdown chunks for a Codex skill."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def read_pdf_with_pypdf(pdf_path: Path) -> list[str]:
    from pypdf import PdfReader  # type: ignore

    reader = PdfReader(str(pdf_path))
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return pages


def read_pdf_with_pymupdf(pdf_path: Path) -> list[str]:
    import fitz  # type: ignore

    doc = fitz.open(str(pdf_path))
    return [page.get_text("text") or "" for page in doc]


def read_pdf(pdf_path: Path) -> list[str]:
    try:
        return read_pdf_with_pypdf(pdf_path)
    except ModuleNotFoundError:
        try:
            return read_pdf_with_pymupdf(pdf_path)
        except ModuleNotFoundError:
            raise SystemExit(
                "Install one PDF parser first: python -m pip install pypdf"
            )


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_pages(pages: list[str], pages_per_chunk: int) -> list[tuple[int, int, str]]:
    chunks: list[tuple[int, int, str]] = []
    for start in range(0, len(pages), pages_per_chunk):
        end = min(len(pages), start + pages_per_chunk)
        body = "\n\n".join(
            f"## Page {idx + 1}\n\n{clean_text(pages[idx])}" for idx in range(start, end)
        ).strip()
        chunks.append((start + 1, end, body))
    return chunks


def write_chunks(
    chunks: list[tuple[int, int, str]], out_dir: Path, prefix: str, source: Path
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    index_lines = [
        "# Extracted SProcess Manual Index",
        "",
        f"- Source PDF: `{source}`",
        f"- Chunks: {len(chunks)}",
        "",
    ]

    for number, (start, end, body) in enumerate(chunks, start=1):
        filename = f"{prefix}-{number:03d}-pages-{start:04d}-{end:04d}.md"
        path = out_dir / filename
        title = f"# {prefix} pages {start}-{end}"
        path.write_text(f"{title}\n\n{body}\n", encoding="utf-8")
        index_lines.append(f"- `{filename}`: pages {start}-{end}")

    (out_dir / "INDEX.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, help="Path to local PDF manual")
    parser.add_argument("--out", required=True, help="Output directory for Markdown chunks")
    parser.add_argument("--prefix", default="sprocess", help="Chunk filename prefix")
    parser.add_argument("--pages-per-chunk", type=int, default=8)
    args = parser.parse_args()

    pdf_path = Path(args.pdf).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 2

    pages = read_pdf(pdf_path)
    chunks = chunk_pages(pages, max(1, args.pages_per_chunk))
    write_chunks(chunks, out_dir, args.prefix, pdf_path)
    print(f"Wrote {len(chunks)} chunks to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
