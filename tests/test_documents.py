from pathlib import Path

from src.config import AppConfig
from src.documents import load_documents


def test_load_documents_updates_text_for_current_llamaindex(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "sample.txt").write_text("  Hola   mundo.\n\n\n", encoding="utf-8")

    config = AppConfig(data_dir=data_dir, versions_dir=tmp_path / "versions", manifest_path=tmp_path / "manifest.json")

    documents = load_documents(config)

    assert len(documents) == 1
    assert documents[0].text == "Hola mundo."
