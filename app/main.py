import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api import auth, cameras, recordings, alerts, aws_metrics, cost_analysis
from scripts.seed_database import seed_initial_data

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Sistema de Videovigilancia Cloud de Alta Disponibilidad y Optimización de Costos en AWS"
)

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(cameras.router, prefix=settings.API_V1_STR)
app.include_router(recordings.router, prefix=settings.API_V1_STR)
app.include_router(alerts.router, prefix=settings.API_V1_STR)
app.include_router(aws_metrics.router, prefix=settings.API_V1_STR)
app.include_router(cost_analysis.router, prefix=settings.API_V1_STR)

# Seed database on startup if empty
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()

# Static Files & Dashboard UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "VIGILA Cloud Video Surveillance API is running.", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "system": "VIGILA Cloud Video Surveillance",
        "aws_region": settings.AWS_REGION,
        "s3_bucket": settings.S3_BUCKET_NAME,
        "mode": "Optimized AWS Architecture"
    }

