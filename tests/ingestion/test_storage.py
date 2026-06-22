"""Local filesystem raw file storage tests."""

from __future__ import annotations

from api.ingestion.storage import LocalFileStorage


def test_local_storage_roundtrip(tmp_path) -> None:
    storage = LocalFileStorage(base_dir=str(tmp_path))
    uri = storage.write_bytes("tenant/doc.txt", b"hello storage")
    assert storage.read_bytes(uri) == b"hello storage"
