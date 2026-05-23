LANGUAGE_BY_SUFFIX = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".md": "markdown",
}


def language_for_path(path: str) -> str:
    for suffix, language in LANGUAGE_BY_SUFFIX.items():
        if path.endswith(suffix):
            return language
    return "text"
