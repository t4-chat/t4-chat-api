from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class ModelType(str, Enum):
    TEXT = "text"
    # We can add more modalities in the future
    # IMAGE = "image"
    # AUDIO = "audio"
    # MULTIMODAL = "multimodal"


class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    # We can add more providers in the future


class ProviderInterface(ABC):
    """Generic interface for model providers"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def supports_model_type(self, model_type: ModelType) -> bool:
        """Check if the provider supports a specific model type"""
        return False 