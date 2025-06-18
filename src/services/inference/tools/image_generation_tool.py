import json
from typing import Any, Dict

from litellm import aimage_generation

from src.services.inference.dto import ToolCallResultDTO
from src.services.inference.tools.base_tool import BaseTool
from src.services.usage_tracking.dto import TokenUsageDTO

from src.logging.logging_config import get_logger


class ImageGenerationTool(BaseTool):
    def __init__(self):
        self.description = "Generate images from text prompts using AI models"
        self.logger = get_logger(__name__)

    @property
    def name(self) -> str:
        return "image_generation"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "The text prompt describing the image to generate"},
                    },
                    "required": ["prompt"],
                },
            },
        }

    async def invoke(self, prompt: str, model: str) -> ToolCallResultDTO:
        self.logger.info(f"Generating image with prompt: {prompt}")

        try:
            # Prepare parameters, filtering out None values
            params = {
                "prompt": prompt,
                "model": model,
                # reasonable defaults for now
                "n": 1,
                "response_format": "url",
            }

            response = await aimage_generation(**params)

            results = []
            for image_data in response.data:
                image_info = {"url": image_data.url, "revised_prompt": image_data.revised_prompt}
                results.append(image_info)
            return ToolCallResultDTO(
                content=results,
                usage=TokenUsageDTO(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                ),
            )

        except Exception as e:
            self.logger.error(f"Error during image generation: {str(e)}")
            return ToolCallResultDTO(
                error={"message": f"Image generation failed: {str(e)}"}
            )
