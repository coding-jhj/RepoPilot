from app.domain.models import CodeDocument


def build_dependency_graph(documents: list[CodeDocument]) -> dict[str, list[str]]:
    return {document.path: document.imports for document in documents}
