from sqlalchemy.orm import Session

from src.storage.models import AiProviderModel


class AiModelService:
    def __init__(self, db: Session):
        self.db = db

    def get_ai_models(self):
        return self.db.query(AiProviderModel).all()
