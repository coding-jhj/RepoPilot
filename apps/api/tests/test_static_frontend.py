from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import mount_frontend


def test_mount_frontend_serves_exported_index(tmp_path: Path):
    static_dir = tmp_path / "out"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<h1>RepoPilot</h1>", encoding="utf-8")

    app = FastAPI()
    mount_frontend(app, static_dir)

    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert "RepoPilot" in response.text
