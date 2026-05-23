from pathlib import Path

from app.code.parser import CodeParser
from app.rag.chunker import CodeChunker
from app.rag.retriever import InMemoryRetriever


def test_parser_extracts_python_symbols_and_imports(tmp_path: Path):
    source = tmp_path / "sample.py"
    source.write_text(
        "import os\n\nclass Greeter:\n    pass\n\ndef hello(name):\n    return f'hi {name}'\n",
        encoding="utf-8",
    )

    document = CodeParser().parse_file(source, repo_root=tmp_path)

    assert document.path == "sample.py"
    assert [symbol.name for symbol in document.symbols] == ["Greeter", "hello"]
    assert document.imports == ["os"]


def test_chunker_keeps_path_line_metadata(tmp_path: Path):
    source = tmp_path / "sample.ts"
    source.write_text(
        "import x from 'x'\n\nexport function add(a: number, b: number) {\n  return a + b\n}\n",
        encoding="utf-8",
    )
    document = CodeParser().parse_file(source, repo_root=tmp_path)

    chunks = CodeChunker(max_lines=3).chunk(document)

    assert chunks
    assert chunks[0].path == "sample.ts"
    assert chunks[0].start_line == 1
    assert chunks[0].end_line >= chunks[0].start_line


def test_retriever_returns_relevant_chunks_with_evidence():
    retriever = InMemoryRetriever()
    retriever.add_chunks(
        repo_id="repo_1",
        chunks=[
            {
                "path": "src/math.py",
                "start_line": 10,
                "end_line": 12,
                "content": "def add(a, b):\n    return a + b",
            },
            {
                "path": "README.md",
                "start_line": 1,
                "end_line": 3,
                "content": "A small web application.",
            },
        ],
    )

    results = retriever.search("how does add work", repo_id="repo_1", limit=1)

    assert results[0].path == "src/math.py"
    assert results[0].start_line == 10
