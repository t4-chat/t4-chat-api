from abc import abstractmethod
from typing import Optional, Any, AsyncGenerator

from src.services.inference.models_shared.provider_interface import ProviderInterface, ModelType
from src.services.inference.config.text_options import TextGenerationOptions


class TextGenerationProvider(ProviderInterface):
    """Interface for text generation model providers"""
    
    @abstractmethod
    async def generate_text(self, model: str, prompt: str, options: Optional[TextGenerationOptions] = None, **kwargs) -> str:
        """Generate text based on the prompt (non-streaming)"""
        pass
    
    @abstractmethod
    async def generate_text_stream(self, model: str, prompt: str, options: Optional[TextGenerationOptions] = None, **kwargs) -> AsyncGenerator[str, None]:
        """Generate text based on the prompt with streaming"""
        pass
    
    def supports_model_type(self, model_type: ModelType) -> bool:
        """Check if the provider supports a specific model type"""
        return model_type == ModelType.TEXT 