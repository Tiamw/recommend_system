from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone

from api.config.settings import AppSettings
from api.db.database import get_db_connection


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}")


class AuthService:
    """负责用户注册、密码校验和 JWT 签发。"""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def hash_password(self, password: str) -> str:
        # 这里使用 PBKDF2 生成带盐摘要，当前阶段不额外引入第三方加密依赖。
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return f"{salt.hex()}${digest.hex()}"

    def verify_password(self, password: str, stored_hash: str) -> bool:
        salt_hex, digest_hex = stored_hash.split("$", maxsplit=1)
        salt = bytes.fromhex(salt_hex)
        expected_digest = bytes.fromhex(digest_hex)
        actual_digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(actual_digest, expected_digest)

    def create_access_token(self, user_id: int, username: str) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.settings.jwt_expire_minutes)
        payload = {
            "sub": str(user_id),
            "username": username,
            "exp": int(expires_at.timestamp()),
        }

        encoded_header = _b64url_encode(
            json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        )
        encoded_payload = _b64url_encode(
            json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        )
        signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
        signature = hmac.new(
            self.settings.jwt_secret.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        encoded_signature = _b64url_encode(signature)
        return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

    def decode_access_token(self, token: str) -> dict[str, object]:
        try:
            encoded_header, encoded_payload, encoded_signature = token.split(".")
        except ValueError as exc:
            raise ValueError("Invalid token format.") from exc

        signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
        expected_signature = hmac.new(
            self.settings.jwt_secret.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        actual_signature = _b64url_decode(encoded_signature)
        if not hmac.compare_digest(actual_signature, expected_signature):
            raise ValueError("Invalid token signature.")

        payload = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))
        if int(payload["exp"]) < int(datetime.now(timezone.utc).timestamp()):
            raise ValueError("Token has expired.")
        return payload

    def get_current_user_from_token(self, token: str) -> dict[str, object]:
        payload = self.decode_access_token(token)
        user_id = int(payload["sub"])

        with get_db_connection(self.settings.database_path) as connection:
            user = connection.execute(
                """
                SELECT id, username
                FROM users
                WHERE id = ?
                """,
                (user_id,),
            ).fetchone()

        if user is None:
            raise ValueError("User not found.")

        return dict(user)

    def register_user(self, username: str, password: str) -> dict[str, object]:
        normalized_username = username.strip()
        with get_db_connection(self.settings.database_path) as connection:
            existing_user = connection.execute(
                "SELECT id FROM users WHERE username = ?",
                (normalized_username,),
            ).fetchone()
            if existing_user is not None:
                raise ValueError("Username already exists.")

            password_hash = self.hash_password(password)
            cursor = connection.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
                """,
                (normalized_username, password_hash),
            )
            connection.commit()
            user_id = cursor.lastrowid
            user = connection.execute(
                """
                SELECT id, username, created_at
                FROM users
                WHERE id = ?
                """,
                (user_id,),
            ).fetchone()

        return dict(user)

    def login_user(self, username: str, password: str) -> dict[str, object]:
        normalized_username = username.strip()
        with get_db_connection(self.settings.database_path) as connection:
            user = connection.execute(
                """
                SELECT id, username, password_hash, created_at
                FROM users
                WHERE username = ?
                """,
                (normalized_username,),
            ).fetchone()

        if user is None or not self.verify_password(password, user["password_hash"]):
            raise ValueError("Invalid username or password.")

        token = self.create_access_token(user["id"], user["username"])
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "created_at": user["created_at"],
            },
        }
