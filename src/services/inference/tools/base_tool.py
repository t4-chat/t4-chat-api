from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """Base abstract class for all tools."""
    
    @abstractmethod
    def invoke(self, **kwargs) -> str:
        """Execute the tool's logic with the provided arguments."""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Return the tool's JSON schema for LLM function calling."""
        pass
    
    @property
    def name(self) -> str:
        """Return the tool's name."""
        return self.__class__.__name__.lower() 