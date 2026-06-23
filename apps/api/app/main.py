from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.agents.graph import RepoPilotAgent
from app.api.routes import analyses, chat, github, patches, repos
from app.core.config import get_settings
from app.core.errors import install_error_handlers
from app.core.llm import build_llm_provider
from app.core.logging import configure_logging
from app.rag.embedder import build_embedder
from app.rag.qdrant_store import LocalQdrantLikeStore
from app.services.analysis_service import AnalysisService
from app.services.github_service import GitHubService
from app.services.indexing_service import IndexingService
from app.services.patch_service import PatchService
from app.services.repo_service import RepoService


def mount_frontend(app: FastAPI, static_dir: Path) -> None:
    index_file = static_dir / "index.html"
    if index_file.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    embedder = build_embedder() if settings.use_embeddings else None
    retriever = LocalQdrantLikeStore(embedder=embedder)
    llm = build_llm_provider(settings.llm_provider)
    agent = RepoPilotAgent(llm=llm)

    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_error_handlers(app)
    app.state.services = {
        "repo_service": RepoService(
            settings.workspace_root,
            clone_timeout_seconds=settings.clone_timeout_seconds,
        ),
        "indexing_service": IndexingService(
            store=retriever,
            max_files=settings.max_files_indexed,
            max_file_bytes=settings.max_file_bytes,
        ),
        "retriever": retriever,
        "analysis_service": AnalysisService(agent=agent, retriever=retriever),
        "patch_service": PatchService(),
        "github_service": GitHubService(),
    }

    @app.get("/health")
    def health():
        return {"status": "ok", "app": settings.app_name}

    app.include_router(repos.router)
    app.include_router(analyses.router)
    app.include_router(chat.router)
    app.include_router(patches.router)
    app.include_router(github.router)
    mount_frontend(app, settings.frontend_static_dir)
    return app


app = create_app()
