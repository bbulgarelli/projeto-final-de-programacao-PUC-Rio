from fastapi import APIRouter, status
from typing import List

from .models import LLMModel
from .routes_schemas import AvailableModelsSchema

models_router = APIRouter()

@models_router.get(
    '/available-models',
    status_code=status.HTTP_200_OK,
    response_model=List[AvailableModelsSchema],
    tags=['Models']
)
async def available_models():
    """Return the catalog of available language models and their capabilities."""
    return LLMModel.get_available_models()