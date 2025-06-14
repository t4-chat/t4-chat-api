from typing import Any, Dict

from google.auth.transport import requests
from google.oauth2 import id_token

from src.services.auth.token_service import TokenService
from src.services.user.user_service import UserService

from src.storage.models.user import User

from src.config import settings


class AuthService:
    def __init__(self, token_service: TokenService, user_service: UserService):
        self.token_service = token_service
        self.user_service = user_service
        self.google_client_id = settings.GOOGLE_CLIENT_ID

    def verify_google_token(self, token: str) -> Dict[str, Any]:
        try:
            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), self.google_client_id
            )

            if idinfo["iss"] not in [
                "accounts.google.com",
                "https://accounts.google.com",
            ]:
                raise ValueError("Invalid issuer")

            return idinfo
        except Exception as e:
            raise ValueError(f"Invalid token: {str(e)}")

    async def authenticate_with_google(self, google_token: str) -> str:
        google_user_info = self.verify_google_token(google_token)
        user = User(
            email=google_user_info["email"],
            first_name=google_user_info.get("given_name"),
            last_name=google_user_info.get("family_name"),
            profile_image_url=google_user_info.get("picture"),
        )

        user = await self.user_service.create_if_not_exists(user=user)
        return self.token_service.create_token_from_user(user=user)
