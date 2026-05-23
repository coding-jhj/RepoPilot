import hashlib


class HashEmbedder:
    """Deterministic local placeholder used for cache keys and offline tests."""

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [byte / 255 for byte in digest[:16]]
