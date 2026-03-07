"""Tests for JWT auth: password hashing, token creation/verification."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ankithis_api.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        pw = "test-password-123"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed)

    def test_wrong_password(self):
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)

    def test_different_hashes(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # Different salts

    def test_hash_format(self):
        hashed = hash_password("test")
        assert "$" in hashed
        salt, dk = hashed.split("$", 1)
        assert len(salt) == 32  # hex of 16 bytes


class TestJWT:
    def test_create_and_decode(self):
        token = create_access_token("user-123")
        payload = decode_access_token(token)
        assert payload["sub"] == "user-123"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid token format"):
            decode_access_token("not.a.valid.token.too.many.parts")

    def test_tampered_payload(self):
        token = create_access_token("user-123")
        parts = token.split(".")
        # Tamper with payload
        parts[1] = parts[1][::-1]
        tampered = ".".join(parts)
        with pytest.raises(ValueError):
            decode_access_token(tampered)

    def test_tampered_signature(self):
        token = create_access_token("user-123")
        parts = token.split(".")
        parts[2] = "AAAA" + parts[2][4:]
        tampered = ".".join(parts)
        with pytest.raises(ValueError):
            decode_access_token(tampered)


class TestAuthEndpoints:
    """Auth endpoint tests using a mock DB session.

    We mock the DB to avoid asyncpg event loop conflicts with TestClient.
    """

    @pytest.fixture(autouse=True)
    def setup_mock_db(self, client):
        """Override get_db with a mock that stores users in-memory."""
        from ankithis_api.app import app
        from ankithis_api.db import get_db
        from ankithis_api.models.user import User

        self._users: dict[str, User] = {}
        self._client = client

        mock_session = AsyncMock()

        # Mock execute to return users from in-memory store
        def make_execute(session):
            async def execute(stmt):
                result = MagicMock()
                # Extract email from the compiled query
                email = None
                if hasattr(stmt, "whereclause"):
                    clause = stmt.whereclause
                    if hasattr(clause, "right") and hasattr(clause.right, "value"):
                        email = clause.right.value

                if email and email in self._users:
                    result.scalar_one_or_none.return_value = self._users[email]
                else:
                    result.scalar_one_or_none.return_value = None
                return result

            return execute

        mock_session.execute = make_execute(mock_session)

        # Mock add to store users
        def mock_add(obj):
            if isinstance(obj, User):
                self._users[obj.email] = obj

        mock_session.add = mock_add
        mock_session.commit = AsyncMock()

        async def override():
            yield mock_session

        app.dependency_overrides[get_db] = override
        yield
        app.dependency_overrides.pop(get_db, None)

    def test_register(self):
        resp = self._client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["email"] == "test@example.com"
        assert data["token_type"] == "bearer"

    def test_register_short_password(self):
        resp = self._client.post(
            "/api/auth/register",
            json={"email": "test2@example.com", "password": "short"},
        )
        assert resp.status_code == 422

    def test_register_duplicate_email(self):
        self._client.post(
            "/api/auth/register",
            json={
                "email": "dup@example.com",
                "password": "password123",
            },
        )
        resp = self._client.post(
            "/api/auth/register",
            json={
                "email": "dup@example.com",
                "password": "password456",
            },
        )
        assert resp.status_code == 409

    def test_login(self):
        self._client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "password": "password123",
            },
        )
        resp = self._client.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "password123",
            },
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self):
        self._client.post(
            "/api/auth/register",
            json={
                "email": "wrong@example.com",
                "password": "password123",
            },
        )
        resp = self._client.post(
            "/api/auth/login",
            json={
                "email": "wrong@example.com",
                "password": "wrongpassword",
            },
        )
        assert resp.status_code == 401

    def test_login_nonexistent(self):
        resp = self._client.post(
            "/api/auth/login",
            json={
                "email": "nobody@example.com",
                "password": "password123",
            },
        )
        assert resp.status_code == 401

    def test_protected_endpoint_no_token(self):
        resp = self._client.post("/api/upload")
        assert resp.status_code in (401, 422)

    def test_protected_endpoint_invalid_token(self):
        resp = self._client.post(
            "/api/upload",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == 401
