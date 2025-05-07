

from fastapi import APIRouter
from pydantic import BaseModel

from fastapi_backend.app.services.classifier.service import ClassifierService

router = APIRouter(tags=["classify"])


class ClassifyResult(BaseModel):
    result: str


@router.get("/", response_model=list[ClassifyResult])
async def classify(
    text: str
):
    classifier_service = ClassifierService()
    return [ClassifyResult(result="test")]