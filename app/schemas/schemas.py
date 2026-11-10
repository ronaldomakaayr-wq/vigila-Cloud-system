from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Camera Schemas
class CameraBase(BaseModel):
    code: str
    name: str
    location: str
    zone: str = "Zona Central"
    rtsp_url: str
    resolution: str = "1080p"
    fps: int = 30
    bitrate_kbps: int = 4096
    status: str = "ONLINE"
    is_recording: bool = True

class CameraCreate(CameraBase):
    pass

class CameraResponse(CameraBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Video Recording Schemas
class RecordingResponse(BaseModel):
    id: int
    camera_id: int
    camera_name: str
    filename: str
    s3_key: str
    s3_bucket: str
    storage_class: str
    file_size_mb: float
    duration_seconds: int
    recorded_at: datetime
    expiration_date: Optional[datetime] = None
    is_locked: bool
    class Config:
        from_attributes = True

class PresignedUrlResponse(BaseModel):
    recording_id: int
    s3_key: str
    presigned_url: str
    expires_in_seconds: int
    security_protocol: str = "AWS Signature Version 4 (SigV4)"

class StorageTransitionRequest(BaseModel):
    target_tier: str  # STANDARD_IA, GLACIER_FLEXIBLE, DEEP_ARCHIVE

# Alert Schemas
class AlertResponse(BaseModel):
    id: int
    camera_id: int
    camera_name: str
    alert_type: str
    severity: str
    description: str
    s3_clip_key: Optional[str] = None
    status: str
    timestamp: datetime
    class Config:
        from_attributes = True

class AlertStatusUpdate(BaseModel):
    status: str  # ACKNOWLEDGED, RESOLVED

# EC2 Node & AWS Schemas
class EC2NodeResponse(BaseModel):
    id: int
    instance_id: str
    instance_type: str
    availability_zone: str
    state: str
    cpu_utilization: float
    memory_utilization: float
    current_streams: int
    lifecycle_type: str
    ssm_agent_status: str
    launch_time: datetime
    class Config:
        from_attributes = True

class SSMCommandRequest(BaseModel):
    command: str = Field(..., example="uptime")
    instance_ids: List[str] = Field(default=["i-0a1b2c3d4e5f01", "i-0a1b2c3d4e5f02"])

class SSMCommandResponse(BaseModel):
    command_id: str
    document_name: str
    target_instances: List[str]
    status: str
    delivery_channel: str
    output: str
    execution_time_ms: int
    timestamp: str

# Cost Analysis Schemas
class CostItem(BaseModel):
    id: int
    period_name: str
    architecture_type: str
    ec2_cost_usd: float
    s3_cost_usd: float
    rds_cost_usd: float
    data_transfer_usd: float
    total_cost_usd: float
    active_cameras_count: int
    notes: Optional[str] = None
    class Config:
        from_attributes = True

class CostComparisonSummary(BaseModel):
    legacy_cost_monthly: float
    optimized_cost_monthly: float
    monthly_savings_usd: float
    savings_percentage: float
    annual_savings_usd: float
    breakdown_by_service: Dict[str, Any]

