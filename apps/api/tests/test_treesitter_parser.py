from pathlib import Path

import pytest

from app.code import treesitter_parser
from app.code.parser import CodeParser

pytestmark = pytest.mark.skipif(
    not treesitter_parser.AVAILABLE,
    reason="tree-sitter grammars not installed; parser falls back to regex",
)


def _parse(tmp_path: Path, name: str, source: str):
    file = tmp_path / name
    file.write_text(source, encoding="utf-8")
    return CodeParser().parse_file(file, repo_root=tmp_path)


def test_typescript_captures_methods_interfaces_and_arrow_functions(tmp_path: Path):
    document = _parse(
        tmp_path,
        "service.ts",
        "import { foo } from './a'\n"
        "export class Service {\n"
        "  fetchData() { return 1 }\n"
        "  async save() {}\n"
        "}\n"
        "export const handler = () => 42\n"
        "export interface User { id: number }\n",
    )

    symbols = {(symbol.kind, symbol.name) for symbol in document.symbols}

    # Regex scanner used to miss every one of these.
    assert ("class", "Service") in symbols
    assert ("method", "fetchData") in symbols
    assert ("method", "save") in symbols
    assert ("interface", "User") in symbols
    # Arrow-function binding is classified as a callable, not a plain constant.
    assert ("function", "handler") in symbols
    assert document.imports == ["./a"]


def test_javascript_class_methods_and_const_distinction(tmp_path: Path):
    document = _parse(
        tmp_path,
        "widget.js",
        "import x from 'x'\n"
        "class Widget {\n"
        "  render() {}\n"
        "}\n"
        "const API_URL = 'https://example.com'\n"
        "const run = function () {}\n",
    )

    symbols = {(symbol.kind, symbol.name) for symbol in document.symbols}

    assert ("class", "Widget") in symbols
    assert ("method", "render") in symbols
    assert ("constant", "API_URL") in symbols
    assert ("function", "run") in symbols
    assert document.imports == ["x"]
