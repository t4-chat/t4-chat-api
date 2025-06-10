from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.storage import db
from src.storage.db import get_db
from src.storage.models import AiProvider, AiProviderModel


class AiProviderService:
    def __init__(self, db: Session):
        self.db = db

    def get_ai_providers(self):
        return self.db.query(AiProvider).all()


def get_ai_provider_service(db: Session = Depends(get_db)) -> AiProviderService:
    return AiProviderService(db)


ai_provider_service = Annotated[AiProviderService, Depends(get_ai_provider_service)]
