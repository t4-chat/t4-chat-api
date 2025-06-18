import json
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

from src.services.inference.dto import ToolCallResultDTO
from src.services.inference.tools.base_tool import BaseTool
from src.services.usage_tracking.dto import TokenUsageDTO

from src.logging.logging_config import get_logger


class WebSearchTool(BaseTool):
    def __init__(self):
        self.description = "Search the web for real-time information."
        self.logger = get_logger(__name__)
        
    @property
    def name(self) -> str:
        """Override the name property from BaseTool."""
        return "web_search"
        
    def get_schema(self) -> Dict[str, Any]:
        """Return the schema for the web search tool."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to look up on the web"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of search results to return. Max value is 4.",
                            "default": 2
                        }
                    },
                    "required": ["query"]
                }
            }
        }

    async def invoke(self, query: str, num_results: int = 2) -> ToolCallResultDTO:
        """Execute a web search and return the results."""
        self.logger.debug(f"Performing web search for: {query}")
        
        try:
            num_results = min(num_results, 4)
            results = DDGS().text(query, max_results=num_results)
            
            if results:
                results = self._parse_url_content(results)

            self.logger.debug(f"Web search results: {results}")

            return ToolCallResultDTO(
                content=results,
                usage=TokenUsageDTO(
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                ),
            )
        except Exception as e:
            self.logger.error(f"Error during web search: {str(e)}")
            return ToolCallResultDTO(
                error={"message": f"Web search failed: {str(e)}"}
            )
            
    def _parse_url_content(self, search_results: List[Dict]) -> List[Dict]:
        """Fetch and parse content from URLs in search results."""
        for result in search_results:
            if "href" in result:
                try:
                    url = result["href"]
                    self.logger.debug(f"Fetching content from: {url}")
                    
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                    response = requests.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    page_title = soup.title.text.strip() if soup.title else "No title found"
                    
                    for tag in soup(['script', 'style', 'noscript', 'iframe', 'svg', 'meta', 'link']):
                        tag.decompose()
 
                    text = soup.get_text(separator=' ', strip=True)
                    main_content = text[:2000]
                    
                    # Add parsed data to the result
                    result["parsed_content"] = {
                        "title": page_title,
                        "main_content": main_content,
                    }
                    
                except Exception as e:
                    self.logger.error(f"Error parsing content from {result.get('href', 'unknown URL')}: {str(e)}")
                    result["parsed_content"] = {"error": f"Failed to parse content: {str(e)}"}
        
        return search_results 