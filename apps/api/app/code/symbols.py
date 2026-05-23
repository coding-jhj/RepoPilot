from app.domain.models import CodeDocument, CodeSymbol


def collect_symbols(documents: list[CodeDocument]) -> dict[str, list[CodeSymbol]]:
    return {document.path: document.symbols for document in documents}
