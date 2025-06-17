from typing import Any, Dict, Optional
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import StreamingResponse
import json

from src.api.schemas.admin import AdminSendMessageRequestSchema, AdminSendMessageResponseSchema
from src.api.schemas.chat import CompletionOptionsRequestSchema
from src.containers.container import InferenceServiceDep, AiModelServiceDep, PromptsServiceDep


router = APIRouter(prefix="/api/admin/messages", tags=["Admin"])

@router.post("", response_model=AdminSendMessageResponseSchema)
async def send_message(
    send_message_schema: AdminSendMessageRequestSchema,
    inference_service: InferenceServiceDep,
    ai_model_service: AiModelServiceDep,
    prompts_service: PromptsServiceDep,
    background_tasks: BackgroundTasks,
):
    model = await ai_model_service.get_model(send_message_schema.model_id)
    params = _get_prompt_params(send_message_schema.options)
    messages = [
        {
            "role": "system",
            "content": await prompts_service.get_prompt(model.prompt_path, params=params),
        },
        {
            "role": "user",
            "content": send_message_schema.message.content,
        }
    ]

    response = await inference_service.generate_response(model=model, messages=messages, background_tasks=background_tasks)
    return response


@router.post("/stream", response_class=StreamingResponse)
async def generate_response_stream(
    send_message_schema: AdminSendMessageRequestSchema,
    inference_service: InferenceServiceDep,
    ai_model_service: AiModelServiceDep,
    prompts_service: PromptsServiceDep,
    background_tasks: BackgroundTasks,
):
    model = await ai_model_service.get_model(send_message_schema.model_id)
    params = _get_prompt_params(send_message_schema.options)
    messages = [
        {
            "role": "system",
            "content": await prompts_service.get_prompt(model.prompt_path, params=params),
        },
        {
            "role": "user",
            "content": send_message_schema.message.content,
        }
    ]
    
    async def stream_formatter():
        """
        Internal helper function that converts StreamGenerationDTO objects
        to properly formatted strings for the StreamingResponse.
        """
        try:
            async for chunk in inference_service.generate_response_stream(
                model=model, 
                messages=messages, 
                background_tasks=background_tasks
            ):
                if chunk.text:
                    yield f"data: {json.dumps({'text': chunk.text})}\n\n"
                if chunk.reasoning:
                    yield f"data: {json.dumps({'reasoning': chunk.reasoning})}\n\n"
                if chunk.thinking and len(chunk.thinking) > 0:
                    for thinking_chunk in chunk.thinking:
                        yield f"data: {json.dumps({'thinking': thinking_chunk.thinking, 'signature': thinking_chunk.signature, 'type': thinking_chunk.type})}\n\n"
                if chunk.usage:
                    yield f"data: {json.dumps({'usage': {'prompt_tokens': chunk.usage.prompt_tokens, 'completion_tokens': chunk.usage.completion_tokens, 'total_tokens': chunk.usage.total_tokens}})}\n\n"
            # Send a done event
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        stream_formatter(),
        media_type="text/event-stream",
    )


def _get_prompt_params(options: Optional[CompletionOptionsRequestSchema]) -> Dict[str, Any]:
    if not options:
        return {}

    return {
        "web_search": options.tools and "web_search" in options.tools
    }