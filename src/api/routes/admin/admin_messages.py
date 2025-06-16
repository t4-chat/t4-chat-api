from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import StreamingResponse
import json

from src.api.schemas.admin import AdminSendMessageRequestSchema, AdminSendMessageResponseSchema
from src.containers.container import InferenceServiceDep, AiModelServiceDep


router = APIRouter(prefix="/api/admin/messages", tags=["Admin"])

@router.post("", response_model=AdminSendMessageResponseSchema)
async def send_message(
    send_message_schema: AdminSendMessageRequestSchema,
    inference_service: InferenceServiceDep,
    ai_model_service: AiModelServiceDep,
    background_tasks: BackgroundTasks,
):
    model = await ai_model_service.get_model(send_message_schema.model_id)
    messages = [{"role": "user", "content": send_message_schema.message.content}]
    response = await inference_service.generate_response(model=model, messages=messages, background_tasks=background_tasks)
    return response


@router.post("/stream", response_class=StreamingResponse)
async def generate_response_stream(
    send_message_schema: AdminSendMessageRequestSchema,
    inference_service: InferenceServiceDep,
    ai_model_service: AiModelServiceDep,
    background_tasks: BackgroundTasks,
):
    model = await ai_model_service.get_model(send_message_schema.model_id)
    messages = [{"role": "user", "content": send_message_schema.message.content}]
    
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