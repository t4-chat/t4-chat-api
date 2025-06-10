from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.storage.db import get_db
from src.storage.models import User

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_if_not_exists(self, user: User) -> User:
        existing_user = self.db.query(User).filter(User.email == user.email).first()
        if existing_user:
            return existing_user

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)

user_service = Annotated[UserService, Depends(get_user_service)]
