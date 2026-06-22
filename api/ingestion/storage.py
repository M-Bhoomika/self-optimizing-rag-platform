"""Raw file storage abstraction with S3 and local filesystem backends."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional, Protocol
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class RawFileStorage(Protocol):
    def read_bytes(self, location: str) -> bytes: ...
    def write_bytes(self, location: str, payload: bytes) -> str: ...


class LocalFileStorage:
    """Read/write files under a base directory."""

    def __init__(self, base_dir: Optional[str] = None) -> None:
        self.base_dir = Path(base_dir or os.getenv("LOCAL_UPLOAD_DIR", "./data/uploads")).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, location: str) -> Path:
        path = Path(location)
        if path.is_absolute():
            return path
        return self.base_dir / location

    def read_bytes(self, location: str) -> bytes:
        path = self._resolve(location)
        if not path.exists():
            raise FileNotFoundError(f"Local file not found: {path}")
        return path.read_bytes()

    def write_bytes(self, location: str, payload: bytes) -> str:
        path = self._resolve(location)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return str(path)


class S3RawFileStorage:
    """S3-backed storage when boto3 is installed."""

    def __init__(self, bucket: Optional[str] = None) -> None:
        try:
            import boto3  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "boto3 is required for S3RawFileStorage. Install with: pip install boto3"
            ) from exc
        self._bucket = bucket or os.getenv("S3_BUCKET", "")
        if not self._bucket:
            raise ValueError("S3_BUCKET must be set for S3RawFileStorage.")
        self._client = boto3.client("s3")

    def read_bytes(self, location: str) -> bytes:
        key = self._normalize_key(location)
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()

    def write_bytes(self, location: str, payload: bytes) -> str:
        key = self._normalize_key(location)
        self._client.put_object(Bucket=self._bucket, Key=key, Body=payload)
        return f"s3://{self._bucket}/{key}"

    @staticmethod
    def _normalize_key(location: str) -> str:
        if location.startswith("s3://"):
            parsed = urlparse(location)
            return parsed.path.lstrip("/")
        return location.lstrip("/")


def get_raw_file_storage(prefer_s3: bool = False) -> RawFileStorage:
    """Return S3 storage when configured, otherwise local filesystem storage."""
    bucket = os.getenv("S3_BUCKET", "").strip()
    if prefer_s3 and bucket:
        try:
            return S3RawFileStorage(bucket=bucket)
        except ImportError:
            logger.warning("S3 requested but boto3 unavailable; using local storage.")
    return LocalFileStorage()
