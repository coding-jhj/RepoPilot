from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RepoPilot"
    workspace_root: Path = Path(".repopilot-workspaces")
    frontend_static_dir: Path = Path("../web/out")
    max_files_indexed: int = 500
    max_file_bytes: int = 200_000
    max_repo_bytes: int = 50_000_000
    clone_timeout_seconds: int = 45
    # Off by default: the lean deterministic path uses keyword retrieval. Set
    # REPOPILOT_USE_EMBEDDINGS=true to load the MiniLM embedder (needs the
    # [embeddings] extra) for semantic search.
    use_embeddings: bool = False
    llm_provider: str = "fake"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_prefix="REPOPILOT_")


@lru_cache
def get_settings() -> Settings:
    return Settings()
