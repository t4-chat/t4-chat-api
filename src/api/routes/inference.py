from fastapi import APIRouter, HTTPException

from src.api.models.inference import TextGenerationRequest, TextGenerationResponse
from src.services.inference.inference_service import inference_service
from src.services.inference.models_shared.text_provider import TextGenerationOptions

router = APIRouter(prefix="/api/inference", tags=["inference"])


@router.post("", response_model=TextGenerationResponse)
async def inference(request: TextGenerationRequest, service: inference_service):
    """Generate text using the specified provider and model"""
    try:
        options = request.options if request.options else TextGenerationOptions()

        text = await service.generate_text(provider=request.provider, model=request.model, prompt=request.prompt, options=options)
        return TextGenerationResponse(text=text)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
