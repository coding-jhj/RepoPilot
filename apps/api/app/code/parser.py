from __future__ import annotations

import ast
import re
from pathlib import Path

from app.code import treesitter_parser
from app.code.language_registry import language_for_path
from app.domain.models import CodeDocument, CodeSymbol


class CodeParser:
    def parse_file(self, path: Path, repo_root: Path) -> CodeDocument:
        content = path.read_text(encoding="utf-8", errors="replace")
        relative_path = path.relative_to(repo_root).as_posix()
        language = language_for_path(relative_path)

        if language == "python":
            imports, symbols = self._parse_python(content)
        elif language in {"typescript", "javascript"}:
            imports, symbols = self._parse_js_like(content, language, relative_path)
        else:
            imports, symbols = [], []

        return CodeDocument(
            path=relative_path,
            language=language,
            content=content,
            imports=imports,
            symbols=symbols,
        )

    def _parse_python(self, content: str) -> tuple[list[str], list[CodeSymbol]]:
        tree = ast.parse(content)
        imports: list[str] = []
        symbols: list[CodeSymbol] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
            elif isinstance(node, ast.ClassDef):
                symbols.append(CodeSymbol(name=node.name, kind="class", line=node.lineno))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.append(CodeSymbol(name=node.name, kind="function", line=node.lineno))

        symbols.sort(key=lambda symbol: symbol.line)
        return imports, symbols

    def _parse_js_like(
        self, content: str, language: str, path: str
    ) -> tuple[list[str], list[CodeSymbol]]:
        if treesitter_parser.AVAILABLE:
            try:
                return treesitter_parser.parse(content, language, path)
            except Exception:
                # Any grammar/parse hiccup falls through to the regex scanner below.
                pass
        return self._parse_js_like_regex(content)

    def _parse_js_like_regex(self, content: str) -> tuple[list[str], list[CodeSymbol]]:
        imports = re.findall(r"import\s+(?:.+?\s+from\s+)?['\"](.+?)['\"]", content)
        symbols: list[CodeSymbol] = []

        for index, line in enumerate(content.splitlines(), start=1):
            function_match = re.search(
                r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)",
                line,
            )
            class_match = re.search(
                r"(?:export\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)",
                line,
            )
            const_match = re.search(
                r"(?:export\s+)?const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=",
                line,
            )
            if function_match:
                symbols.append(
                    CodeSymbol(name=function_match.group(1), kind="function", line=index)
                )
            elif class_match:
                symbols.append(
                    CodeSymbol(name=class_match.group(1), kind="class", line=index)
                )
            elif const_match:
                symbols.append(
                    CodeSymbol(name=const_match.group(1), kind="constant", line=index)
                )

        return imports, symbols
