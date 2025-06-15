import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Optional

import jwt

from src.storage.models.user import User

from src.config import settings


class TokenService:
    def __init__(self):
        self.jwt_secret = settings.JWT_SECRET_KEY
        self.jwt_algorithm = "HS256"
        self.jwt_expiration = settings.JWT_EXPIRATION_MINUTES

    def create_token_from_user(self, user: User) -> str:
        dict = {
            "admin": user.email in settings.ADMIN_EMAILS,
            "sub": str(user.id),
            "email": user.email,
        }
        return self.create_token(dict)

    def create_token(self, data: dict) -> str:
        to_encode = data.copy()
        expiration = datetime.now(UTC) + timedelta(minutes=self.jwt_expiration)
        to_encode["exp"] = expiration
        to_encode["iat"] = datetime.now(UTC)
        encoded_jwt = jwt.encode(
            to_encode, self.jwt_secret, algorithm=self.jwt_algorithm
        )
        return encoded_jwt

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(
                token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )
            return payload
        except jwt.PyJWTError:
            return None

    def get_user_id_from_token(self, token: str) -> Optional[uuid.UUID]:
        payload = self.validate_token(token)
        if not payload or "sub" not in payload:
            return None

        try:
            return uuid.UUID(payload["sub"])
        except ValueError:
            return None
