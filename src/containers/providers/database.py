from dependency_injector import providers
from src.storage.db import get_db

db_provider = providers.Resource(get_db) 