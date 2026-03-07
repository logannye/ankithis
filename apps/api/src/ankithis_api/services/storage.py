"""Storage abstraction: local filesystem or S3."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from pathlib import Path

import boto3

from ankithis_api.config import settings


class StorageBackend(ABC):
    @abstractmethod
    def save(self, content: bytes, filename: str) -> str: ...

    @abstractmethod
    def read(self, path: str) -> bytes: ...

    @abstractmethod
    def delete(self, path: str) -> None: ...


class LocalStorage(StorageBackend):
    def __init__(self, base_dir: str = settings.storage_local_path):
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, filename: str) -> str:
        ext = Path(filename).suffix
        storage_name = f"{uuid.uuid4().hex}{ext}"
        path = self._base / storage_name
        path.write_bytes(content)
        return str(path)

    def read(self, path: str) -> bytes:
        return Path(path).read_bytes()

    def delete(self, path: str) -> None:
        p = Path(path)
        if p.exists():
            p.unlink()


class S3Storage(StorageBackend):
    def __init__(self):
        kwargs = {"region_name": "us-east-1"}
        if settings.s3_endpoint:
            kwargs["endpoint_url"] = settings.s3_endpoint
        if settings.s3_access_key:
            kwargs["aws_access_key_id"] = settings.s3_access_key
            kwargs["aws_secret_access_key"] = settings.s3_secret_key
        self._client = boto3.client("s3", **kwargs)
        self._bucket = settings.s3_bucket

    def save(self, content: bytes, filename: str) -> str:
        ext = Path(filename).suffix
        key = f"uploads/{uuid.uuid4().hex}{ext}"
        self._client.put_object(Bucket=self._bucket, Key=key, Body=content)
        return key

    def read(self, path: str) -> bytes:
        resp = self._client.get_object(Bucket=self._bucket, Key=path)
        return resp["Body"].read()

    def delete(self, path: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=path)


def get_storage() -> StorageBackend:
    if settings.storage_backend == "s3":
        return S3Storage()
    return LocalStorage()


# Convenience wrappers (backwards compatible)
def save_upload(content: bytes, filename: str) -> str:
    return get_storage().save(content, filename)


def read_file(storage_path: str) -> bytes:
    return get_storage().read(storage_path)


def delete_file(storage_path: str) -> None:
    return get_storage().delete(storage_path)
