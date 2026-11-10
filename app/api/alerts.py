from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import random
from app.core.database import get_db
from app.models.models import SecurityAlert, Camera
from app.schemas.schemas import AlertResponse, AlertStatusUpdate

router = APIRouter(prefix="/alerts", tags=["Security Alerts"])

@router.get("/", response_model=List[AlertResponse])
def get_alerts(db: Session = Depends(get_db)):
    return db.query(SecurityAlert).order_by(SecurityAlert.timestamp.desc()).limit(50).all()

@router.patch("/{alert_id}/status")
def update_alert_status(alert_id: int, status_update: AlertStatusUpdate, db: Session = Depends(get_db)):
    alert = db.query(SecurityAlert).filter(SecurityAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    alert.status = status_update.status
    db.commit()
    db.refresh(alert)
    return alert

@router.post("/simulate")
def simulate_new_alert(camera_id: int = 1, db: Session = Depends(get_db)):
    cam = db.query(Camera).filter(Camera.id == camera_id).first()
    if not cam:
        cam = db.query(Camera).first()
    
    alert_types = [
        ("INTRUSION", "CRITICAL", f"Movimiento no autorizado detectado en zona restringida ({cam.location if cam else 'Almacén Central'})"),
        ("LINE_CROSSING", "HIGH", "Cruce de perímetro virtual detectado por visión computacional"),
        ("MOTION_DETECTED", "MEDIUM", "Detección de presencia humana fuera de horario laboral")
    ]
    
    chosen = random.choice(alert_types)
    new_alert = SecurityAlert(
        camera_id=cam.id if cam else 1,
        camera_name=cam.name if cam else "Cámara 01",
        alert_type=chosen[0],
        severity=chosen[1],
        description=chosen[2],
        s3_clip_key=f"alerts/{datetime.utcnow().strftime('%Y%m%d')}/clip_{int(datetime.utcnow().timestamp())}.mp4",
        status="NEW",
        timestamp=datetime.utcnow()
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    return new_alert

