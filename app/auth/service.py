# File: app/auth/service.py

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv


load_dotenv()


JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "medscan-ai-hackathon-secret-key-2026",
)

JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "1440",
    )
)


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plain-text password using bcrypt.
        """

        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()

        hashed_password = bcrypt.hashpw(
            password_bytes,
            salt,
        )

        return hashed_password.decode("utf-8")

    @staticmethod
    def verify_password(
        plain_password: str,
        hashed_password: str,
    ) -> bool:
        """
        Compare a plain-text password with a bcrypt hash.
        """

        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )

        except (
            ValueError,
            TypeError,
            AttributeError,
        ):
            return False

    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create a signed JWT access token.
        """

        payload = data.copy()

        if expires_delta is None:
            expires_delta = timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )

        expire_time = (
            datetime.now(timezone.utc)
            + expires_delta
        )

        payload.update(
            {
                "exp": expire_time,
            }
        )

        return jwt.encode(
            payload,
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )

    @staticmethod
    def decode_access_token(
        token: str,
    ) -> dict | None:
        """
        Decode and validate a JWT access token.
        """

        try:
            return jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
            )

        except jwt.PyJWTError:
            return None