from typing import Optional, AsyncGenerator

from anthropic import Anthropic

from src.services.inference.models_shared import TextGenerationProvider
from src.services.inference.config import TextGenerationOptions


class AnthropicProvider(TextGenerationProvider):
    """Anthropic model provider implementation"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = Anthropic(api_key=api_key)
    
    async def generate_text(self, model: str, prompt: str, 
                           options: Optional[TextGenerationOptions] = None, **kwargs) -> str:
        """Generate text using Anthropic models"""
        if options is None:
            options = TextGenerationOptions()
            
        response = self.client.messages.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=options.temperature,
            max_tokens=options.max_tokens,
            **kwargs
        )
        
        return response.content[0].text
        
    async def generate_text_stream(self, model: str, prompt: str, 
                                  options: Optional[TextGenerationOptions] = None, **kwargs) -> AsyncGenerator[str, None]:
        """Generate text using Anthropic models with streaming"""
        if options is None:
            options = TextGenerationOptions()
            
        # Use Anthropic's streaming context manager
        with self.client.messages.stream(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=options.temperature,
            max_tokens=options.max_tokens,
            **kwargs
        ) as stream:
            # text_stream is the preferred way to access streaming text content
            async for text_chunk in stream.text_stream:
                yield text_chunk 