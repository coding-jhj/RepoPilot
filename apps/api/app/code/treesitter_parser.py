"""Tree-sitter backed parsing for JS/TS family.

Python keeps using the stdlib ``ast`` module in :mod:`app.code.parser` because it
is the canonical, exact parser for the language. Tree-sitter is used here for the
JavaScript / TypeScript family, where the previous regex scanner missed methods,
arrow-function bindings, multi-line imports and TS-only declarations.

The whole module degrades gracefully: if the optional ``tree-sitter`` grammars are
not installed (e.g. a minimal deployment image), :data:`AVAILABLE` is ``False`` and
the caller falls back to the legacy regex scanner. Nothing here raises on import.
"""

from __future__ import annotations

from app.domain.models import CodeSymbol

try:  # optional dependency — never break import if grammars are missing
    from tree_sitter import Language, Node, Parser
    import tree_sitter_javascript as _ts_js
    import tree_sitter_typescript as _ts_ts

    _JS = Language(_ts_js.language())
    _TS = Language(_ts_ts.language_typescript())
    _TSX = Language(_ts_ts.language_tsx())
    AVAILABLE = True
except Exception:  # pragma: no cover - exercised only without the grammars
    AVAILABLE = False


# Languages we delegate to tree-sitter. Python stays on the stdlib ``ast``.
TREESITTER_LANGUAGES = {"javascript", "typescript"}


def _language_for(language: str, path: str):
    if language == "javascript":
        return _JS
    # ``language_for_path`` collapses .ts/.tsx into "typescript"; pick the right grammar.
    if path.endswith(".tsx") or path.endswith(".jsx"):
        return _TSX
    return _TS


# Node types that name a declaration, mapped to the symbol "kind" we expose.
_DECLARATION_KINDS = {
    "function_declaration": "function",
    "generator_function_declaration": "function",
    "class_declaration": "class",
    "abstract_class_declaration": "class",
    "method_definition": "method",
    "interface_declaration": "interface",
    "type_alias_declaration": "type",
    "enum_declaration": "enum",
}


def _text(node: "Node") -> str:
    return node.text.decode("utf-8", errors="replace")


def _line(node: "Node") -> int:
    return node.start_point[0] + 1


def parse(content: str, language: str, path: str) -> tuple[list[str], list[CodeSymbol]]:
    """Return ``(imports, symbols)`` using tree-sitter.

    Raises only if tree-sitter itself fails; callers guard with :data:`AVAILABLE`
    and fall back to the regex scanner on any error.
    """

    parser = Parser(_language_for(language, path))
    tree = parser.parse(bytes(content, "utf-8"))

    imports: list[str] = []
    symbols: list[CodeSymbol] = []

    def visit(node: "Node") -> None:
        node_type = node.type

        if node_type == "import_statement":
            source = node.child_by_field_name("source")
            if source is not None:
                imports.append(_text(source).strip("'\"`"))

        elif node_type in _DECLARATION_KINDS:
            name = node.child_by_field_name("name")
            if name is not None:
                symbols.append(
                    CodeSymbol(name=_text(name), kind=_DECLARATION_KINDS[node_type], line=_line(node))
                )

        elif node_type in {"lexical_declaration", "variable_declaration"}:
            # const/let/var bindings: arrow functions and function expressions count
            # as callables, everything else is treated as a top-level constant.
            for declarator in node.named_children:
                if declarator.type != "variable_declarator":
                    continue
                name = declarator.child_by_field_name("name")
                value = declarator.child_by_field_name("value")
                if name is None or name.type != "identifier":
                    continue
                if value is not None and value.type in {"arrow_function", "function_expression", "function"}:
                    kind = "function"
                else:
                    kind = "constant"
                symbols.append(CodeSymbol(name=_text(name), kind=kind, line=_line(declarator)))

        for child in node.children:
            visit(child)

    visit(tree.root_node)

    # Stable, line-ordered output to match the rest of the pipeline.
    symbols.sort(key=lambda symbol: symbol.line)
    # De-duplicate imports while preserving first-seen order.
    imports = list(dict.fromkeys(imports))
    return imports, symbols
