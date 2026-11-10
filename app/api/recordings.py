from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.aws_service import aws_service
from app.models.models import VideoRecording
from app.schemas.schemas import RecordingResponse, PresignedUrlResponse, StorageTransitionRequest
from app.services.s3_lifecycle import S3LifecycleManager

router = APIRouter(prefix="/recordings", tags=["Recordings & S3 Storage"])

@router.get("/", response_model=List[RecordingResponse])
def get_recordings(
    camera_id: Optional[int] = None,
    storage_class: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(VideoRecording)
    if camera_id:
        query = query.filter(VideoRecording.camera_id == camera_id)
    if storage_class:
        query = query.filter(VideoRecording.storage_class == storage_class.upper())
    return query.order_by(VideoRecording.recorded_at.desc()).limit(limit).all()

@router.get("/{recording_id}/presigned-url", response_model=PresignedUrlResponse)
def get_secure_playback_url(recording_id: int, db: Session = Depends(get_db)):
    """
    AWS S3 Security: Generates a temporary Presigned URL using AWS Signature Version 4.
    Ensures recordings are never stored in public buckets.
    """
    rec = db.query(VideoRecording).filter(VideoRecording.id == recording_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Grabación no encontrada")
    
    url = aws_service.generate_presigned_url(rec.s3_key, expiration_seconds=900)
    return {
        "recording_id": rec.id,
        "s3_key": rec.s3_key,
        "presigned_url": url,
        "expires_in_seconds": 900,
        "security_protocol": "AWS Signature Version 4 (SigV4) with KMS Encryption"
    }

@router.post("/{recording_id}/transition")
def transition_recording_tier(
    recording_id: int,
    transition_in: StorageTransitionRequest,
    db: Session = Depends(get_db)
):
    """
    Executes an S3 tier transition (e.g. from STANDARD to GLACIER_FLEXIBLE)
    to demonstrate AWS S3 storage cost reduction.
    """
    rec = db.query(VideoRecording).filter(VideoRecording.id == recording_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Grabación no encontrada")
    
    result = aws_service.simulate_lifecycle_transition(rec.s3_key, transition_in.target_tier)
    rec.storage_class = transition_in.target_tier
    db.commit()
    db.refresh(rec)
    
    return {
        "message": f"Grabación {rec.filename} migrada a tier {rec.storage_class}",
        "aws_s3_result": result,
        "recording": rec
    }

@router.post("/run-lifecycle-policy")
def run_s3_lifecycle_sweep(db: Session = Depends(get_db)):
    """
    Triggers the automated S3 Lifecycle sweep to transition aged videos
    to Infrequent Access and Glacier.
    """
    return S3LifecycleManager.evaluate_and_apply_lifecycle(db)

@router.get("/storage-summary")
def get_s3_storage_summary(db: Session = Depends(get_db)):
    return S3LifecycleManager.evaluate_and_apply_lifecycle(db)

