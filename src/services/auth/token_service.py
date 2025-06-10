import os
from datetime import datetime, timedelta, UTC
from fastapi import Depends
import jwt
from typing import Annotated, Dict, Any, Optional
import uuid

from src.storage.models.user import User
from src.config import settings

class TokenService:
    def __init__(self):
        self.jwt_secret = settings.JWT_SECRET_KEY
        self.jwt_algorithm = "HS256"
        self.jwt_expiration = settings.JWT_EXPIRATION_MINUTES

    def create_token_from_user(self, user: User) -> str:
        dict = {
            "sub": str(user.id),
            "email": user.email,
        }
        return self.create_token(dict)

    def create_token(self, data: dict) -> str:
        to_encode = data.copy()
        expiration = datetime.now(UTC) + timedelta(minutes=self.jwt_expiration)
        to_encode["exp"] = expiration
        to_encode["iat"] = datetime.now(UTC)
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)
        return encoded_jwt

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
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


def get_token_service() -> TokenService:
    return TokenService()

token_service = Annotated[TokenService, Depends(get_token_service)]