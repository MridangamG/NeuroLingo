from fastapi import APIRouter
from pydantic import BaseModel
from app.services.nlp_engine import nlp_engine

router = APIRouter()

class AnalyzeRequest(BaseModel):
    message: str

@router.post("/")
async def analyze_communication(request: AnalyzeRequest):
    analysis = await nlp_engine.analyze(request.message)
    return analysis
