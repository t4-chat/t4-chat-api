from fastapi import APIRouter, HTTPException

from src.api.models.inference import ResponseGenerationRequest, ResponseGenerationResponse
from src.services.inference.inference_service import inference_service
from src.services.inference.models_shared.model_provider import DefaultResponseGenerationOptions

router = APIRouter(prefix="/api/inference", tags=["inference"])


@router.post("", response_model=ResponseGenerationResponse)
async def inference(request: ResponseGenerationRequest, service: inference_service):
    """Generate text using the specified provider and model"""
    try:
        options = request.options if request.options else DefaultResponseGenerationOptions()

        text = await service.generate_response(provider_id=request.provider_id, model_id=request.model_id, prompt=request.prompt, options=options)
        return ResponseGenerationResponse(text=text)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
