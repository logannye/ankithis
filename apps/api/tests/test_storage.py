"""Tests for storage abstraction."""

import tempfile
from pathlib import Path

from ankithis_api.services.storage import LocalStorage


class TestLocalStorage:
    def test_save_and_read(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_dir=tmpdir)
            content = b"Hello, world!"

            path = storage.save(content, "test.txt")
            assert Path(path).exists()
            assert storage.read(path) == content

    def test_save_preserves_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_dir=tmpdir)
            path = storage.save(b"data", "document.pdf")
            assert path.endswith(".pdf")

    def test_delete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_dir=tmpdir)
            path = storage.save(b"data", "test.txt")
            assert Path(path).exists()

            storage.delete(path)
            assert not Path(path).exists()

    def test_delete_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_dir=tmpdir)
            storage.delete("/nonexistent/file.txt")  # Should not raise

    def test_unique_filenames(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_dir=tmpdir)
            p1 = storage.save(b"a", "test.txt")
            p2 = storage.save(b"b", "test.txt")
            assert p1 != p2
