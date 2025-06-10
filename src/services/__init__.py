from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.services.chat_service import ChatService
from src.services.inference import get_inference_service
from src.storage.db import get_db


def get_chat_service(
    db: Session = Depends(get_db),
    inference_service = Depends(get_inference_service)
) -> ChatService:
    return ChatService(db=db, inference_service=inference_service)


chat_service = Annotated[ChatService, Depends(get_chat_service)]
