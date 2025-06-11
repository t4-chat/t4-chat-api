from dependency_injector import providers
from src.config import get_settings

settings_provider = providers.Singleton(get_settings) 