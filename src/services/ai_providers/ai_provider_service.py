from typing import List, Optional

from src.services.common.context import Context
from src.services.common.decorators import convert_to_dto

from src.services.ai_providers.dto import AiProviderDTO

from src.storage.base_repo import BaseRepository
from src.storage.models import AiProvider


class AiProviderService:
    def __init__(self, context: Context, ai_provider_repo: BaseRepository[AiProvider]):
        self.context = context
        self.ai_provider_repo = ai_provider_repo

    @convert_to_dto
    async def get_ai_providers(self) -> List[AiProviderDTO]:
        return await self.ai_provider_repo.select(includes=[AiProvider.models])

    @convert_to_dto
    async def get_provider(self, provider_id: int) -> Optional[AiProviderDTO]:
        return await self.ai_provider_repo.get(
            filter=AiProvider.id == provider_id, includes=[AiProvider.models]
        )
