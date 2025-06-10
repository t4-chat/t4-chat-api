from typing import Optional, AsyncGenerator

from openai import OpenAI

from src.services.inference.models_shared import TextGenerationProvider
from src.services.inference.config import TextGenerationOptions


class OpenAIProvider(TextGenerationProvider):
    """OpenAI model provider implementation"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = OpenAI(api_key=api_key)
    
    async def generate_text(self, model: str, prompt: str, 
                           options: Optional[TextGenerationOptions] = None, **kwargs) -> str:
        """Generate text using OpenAI models"""
        if options is None:
            options = TextGenerationOptions()
            
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=options.temperature,
            max_tokens=options.max_tokens,
            **kwargs
        )
        
        return response.choices[0].message.content
    
    async def generate_text_stream(self, model: str, prompt: str, 
                                  options: Optional[TextGenerationOptions] = None, **kwargs) -> AsyncGenerator[str, None]:
        """Generate text using OpenAI models with streaming"""
        if options is None:
            options = TextGenerationOptions()
            
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=options.temperature,
            max_tokens=options.max_tokens,
            stream=True,
            **kwargs
        )
        
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content 