from typing import List

from sqlalchemy.orm import Session

from src.storage.models import AiProvider


class AiProviderService:
    def __init__(self, db: Session):
        self.db = db

    def get_ai_providers(self) -> List[AiProvider]:
        return self.db.query(AiProvider).all()
