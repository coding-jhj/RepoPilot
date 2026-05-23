from __future__ import annotations

from app.domain.models import CodeChunk, CodeDocument


class CodeChunker:
    def __init__(self, max_lines: int = 80) -> None:
        self.max_lines = max_lines

    def chunk(self, document: CodeDocument) -> list[CodeChunk]:
        lines = document.content.splitlines()
        chunks: list[CodeChunk] = []
        for start in range(0, len(lines), self.max_lines):
            selected = lines[start : start + self.max_lines]
            if not selected:
                continue
            chunks.append(
                CodeChunk(
                    path=document.path,
                    start_line=start + 1,
                    end_line=start + len(selected),
                    content="\n".join(selected),
                )
            )
        return chunks
