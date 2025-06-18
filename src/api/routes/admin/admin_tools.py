from fastapi import APIRouter

from src.services.inference.tools.web_search_tool import WebSearchTool

router = APIRouter(prefix="/api/admin/tools", tags=["Admin"])

@router.post("/web-search")
async def web_search(
    query: str,
    num_results: int = 3,
):
    web_search_tool = WebSearchTool()
    return web_search_tool.invoke(query, num_results)
