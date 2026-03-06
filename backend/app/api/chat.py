import json
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.services.nlp_engine import nlp_engine
from app.services.llm import llm_pipeline
from app.core.database import get_db
from app.models.communication import CommunicationLog

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/")
async def process_chat(request: ChatRequest, db: Session = Depends(get_db)):
    # Step 1: Communication Analysis
    analysis = await nlp_engine.analyze(request.message)

    # Step 2: Translation & Verification Pipeline
    translation = await llm_pipeline.translate_to_structured(request.message, analysis)

    # Step 3: Persist to database
    try:
        log = CommunicationLog(
            original_text=request.message,
            translated_text=translation.get("meaning", ""),
            intent=analysis.get("intent", ""),
            tone=analysis.get("tone", ""),
            clarity_score=translation.get("clarity_score", 0),
            analysis_json=json.dumps(analysis),
            action=translation.get("action", ""),
            urgency=translation.get("urgency", ""),
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"[Chat] DB save error (non-fatal): {e}")
        db.rollback()

    return {
        "original_message": request.message,
        "analysis": analysis,
        "structured_translation": translation,
    }


@router.get("/history")
async def get_history(
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    """Return recent conversation history."""
    logs = (
        db.query(CommunicationLog)
        .order_by(CommunicationLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": log.id,
            "original_text": log.original_text,
            "translated_text": log.translated_text,
            "intent": log.intent,
            "tone": log.tone,
            "clarity_score": log.clarity_score,
            "action": log.action,
            "urgency": log.urgency,
            "created_at": str(log.created_at) if log.created_at else None,
        }
        for log in logs
    ]
