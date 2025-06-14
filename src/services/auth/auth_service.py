from typing import Any, Dict

from google.auth.transport import requests
from google.oauth2 import id_token

from src.services.auth.token_service import TokenService
from src.services.common.errors import ForbiddenError
from src.services.user.user_service import UserService

from src.storage.base_repo import BaseRepository
from src.storage.models.user import User

from src.config import settings
from src.storage.models.white_list import WhiteList


class AuthService:
    def __init__(self, token_service: TokenService, user_service: UserService, white_list_repo: BaseRepository[WhiteList]):
        self.token_service = token_service
        self.user_service = user_service
        self.google_client_id = settings.GOOGLE_CLIENT_ID
        self.white_list_repo = white_list_repo

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

        if not await self._is_in_white_list(google_user_info["email"]):
            raise ForbiddenError("Forbidden")

        user = User(
            email=google_user_info["email"],
            first_name=google_user_info.get("given_name"),
            last_name=google_user_info.get("family_name"),
            profile_image_url=google_user_info.get("picture"),
        )

        user = await self.user_service.create_if_not_exists(user=user)
        return self.token_service.create_token_from_user(user=user)
    
    async def _is_in_white_list(self, email: str) -> bool:
        return await self.white_list_repo.exists(filter=WhiteList.email == email)
