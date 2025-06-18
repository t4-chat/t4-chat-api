import json
import traceback
from typing import Any, Dict, List, Optional

from src.services.common.context import Context
from src.services.inference.dto import ToolCallResultDTO
from src.services.inference.tools.base_tool import BaseTool
from src.services.inference.tools.image_generation_tool import ImageGenerationTool
from src.services.inference.tools.web_search_tool import WebSearchTool
from src.services.usage_tracking.dto import TokenUsageDTO

from src.logging.logging_config import get_logger


class ToolsService:
    def __init__(self, context: Context):
        self.context = context
        self.logger = get_logger(__name__)
        self.tools: Dict[str, BaseTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        self.register_tool(WebSearchTool())
        self.register_tool(ImageGenerationTool())
        
    def register_tool(self, tool: BaseTool) -> None:
        self.tools[tool.name] = tool
        
    def get_function_schemas(self, skip_tools: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        skip_tools = skip_tools or []
        return [tool.get_schema() for name, tool in self.tools.items() if name not in skip_tools]

    async def execute_function(self, function_name: str, arguments: Dict[str, Any]) -> ToolCallResultDTO:
        if function_name not in self.tools:
            error_message = f"Function '{function_name}' not found"
            self.logger.warning(error_message)
            return ToolCallResultDTO(
                error={"message": error_message}
            )
            
        try:
            tool = self.tools[function_name]
            self.logger.info(f"Executing function '{function_name}' with args: {arguments}")

            result = await tool.invoke(**arguments)
            
            self.logger.info(f"Function '{function_name}' executed successfully")
            return result
            
        except Exception as e:
            error_message = f"Error executing function '{function_name}': {str(e)}"
            self.logger.error(error_message)
            self.logger.error(traceback.format_exc())
            return ToolCallResultDTO(
                error={"message": error_message}
            )
