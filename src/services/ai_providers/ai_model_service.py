from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.storage import db
from src.storage.db import get_db
from src.storage.models import AiProviderModel


class AiModelService:
    def __init__(self, db: Session):
        self.db = db

    def get_ai_models(self):
        return self.db.query(AiProviderModel).all()


def get_ai_model_service(db: Session = Depends(get_db)) -> AiModelService:
    return AiModelService(db)

ai_model_service = Annotated[AiModelService, Depends(get_ai_model_service)]
