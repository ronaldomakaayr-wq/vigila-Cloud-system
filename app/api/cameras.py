from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.models import Camera
from app.schemas.schemas import CameraResponse, CameraCreate
from app.services.video_engine import video_engine

router = APIRouter(prefix="/cameras", tags=["Cameras"])

@router.get("/", response_model=List[CameraResponse])
def get_all_cameras(db: Session = Depends(get_db)):
    return db.query(Camera).order_by(Camera.code).all()

@router.post("/", response_model=CameraResponse)
def create_camera(camera_in: CameraCreate, db: Session = Depends(get_db)):
    existing = db.query(Camera).filter(Camera.code == camera_in.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="El código de cámara ya existe")
    
    new_cam = Camera(**camera_in.model_dump())
    db.add(new_cam)
    db.commit()
    db.refresh(new_cam)
    return new_cam

@router.get("/{camera_id}", response_model=CameraResponse)
def get_camera(camera_id: int, db: Session = Depends(get_db)):
    cam = db.query(Camera).filter(Camera.id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
    return cam

@router.get("/{camera_id}/stream")
def stream_camera_feed(camera_id: int, db: Session = Depends(get_db)):
    """
    Returns an MJPEG live video stream compatible with any standard HTML5 browser.
    Simulates real-time RTSP/HLS stream processing by EC2 worker instances.
    """
    cam = db.query(Camera).filter(Camera.id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
    
    return StreamingResponse(
        video_engine.stream_generator(cam.code, cam.name, cam.status, cam.resolution),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/{camera_id}/snapshot")
def get_camera_snapshot(camera_id: int, db: Session = Depends(get_db)):
    """
    Returns a single JPEG frame snapshot for live dashboard thumbnails.
    """
    cam = db.query(Camera).filter(Camera.id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
    
    frame_bytes = video_engine.generate_camera_frame(cam.code, cam.name, cam.status, cam.resolution)
    return Response(content=frame_bytes, media_type="image/jpeg")

@router.patch("/{camera_id}/toggle-recording")
def toggle_recording(camera_id: int, db: Session = Depends(get_db)):
    cam = db.query(Camera).filter(Camera.id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
    
    cam.is_recording = not cam.is_recording
    cam.status = "RECORDING" if cam.is_recording else "ONLINE"
    db.commit()
    return {"id": cam.id, "is_recording": cam.is_recording, "status": cam.status}

