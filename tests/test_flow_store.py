import tempfile
from pathlib import Path

from services.api.core.flow_builder.publishing import LazyFlowRepository, SQLiteFlowRepository


def test_vercel_relative_flow_store_path_uses_tmp(monkeypatch) -> None:
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("TELLUS_AI_RUNTIME_WRITABLE_DIR", raising=False)

    repository = SQLiteFlowRepository("./data/vercel_test.sqlite3")

    assert repository.db_path == (
        Path(tempfile.gettempdir()) / "tellus_ai_model_platform" / "vercel_test.sqlite3"
    )
    assert repository.db_path.exists()


def test_runtime_writable_dir_overrides_relative_flow_store_path(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("TELLUS_AI_RUNTIME_WRITABLE_DIR", str(tmp_path))

    repository = SQLiteFlowRepository("./data/custom_test.sqlite3")

    assert repository.db_path == tmp_path / "data" / "custom_test.sqlite3"
    assert repository.db_path.exists()


def test_lazy_repository_does_not_initialize_on_construction() -> None:
    repository = LazyFlowRepository()

    assert repository._repository is None
