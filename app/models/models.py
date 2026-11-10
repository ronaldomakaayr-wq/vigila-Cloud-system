from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="OPERATOR")  # ADMIN, OPERATOR, AUDITOR
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Camera(Base):
    __tablename__ = "cameras"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    location = Column(String(150), nullable=False)
    zone = Column(String(50), default="Zona Norte")
    rtsp_url = Column(String(255), nullable=False)
    status = Column(String(20), default="ONLINE")  # ONLINE, OFFLINE, RECORDING, WARNING
    resolution = Column(String(20), default="1080p")
    fps = Column(Integer, default=30)
    bitrate_kbps = Column(Integer, default=4096)
    is_recording = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    recordings = relationship("VideoRecording", back_populates="camera", cascade="all, delete-orphan")
    alerts = relationship("SecurityAlert", back_populates="camera", cascade="all, delete-orphan")

class VideoRecording(Base):
    __tablename__ = "video_recordings"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    camera_name = Column(String(100), nullable=False)
    filename = Column(String(150), nullable=False)
    s3_key = Column(String(255), nullable=False)
    s3_bucket = Column(String(100), nullable=False)
    # Storage class: STANDARD, STANDARD_IA, GLACIER_FLEXIBLE, DEEP_ARCHIVE
    storage_class = Column(String(30), default="STANDARD")
    file_size_mb = Column(Float, default=120.5)
    duration_seconds = Column(Integer, default=3600)  # 1 hour
    recorded_at = Column(DateTime, default=datetime.utcnow)
    expiration_date = Column(DateTime, nullable=True)
    is_locked = Column(Boolean, default=True)  # S3 Object Lock compliance
    
    camera = relationship("Camera", back_populates="recordings")

class SecurityAlert(Base):
    __tablename__ = "security_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    camera_name = Column(String(100), nullable=False)
    alert_type = Column(String(50), nullable=False)  # MOTION_DETECTED, INTRUSION, LINE_CROSSING
    severity = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(Text, nullable=False)
    s3_clip_key = Column(String(255), nullable=True)
    status = Column(String(20), default="NEW")  # NEW, ACKNOWLEDGED, RESOLVED
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    camera = relationship("Camera", back_populates="alerts")

class EC2InstanceNode(Base):
    __tablename__ = "ec2_worker_instances"
    
    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(String(30), unique=True, index=True, nullable=False)
    instance_type = Column(String(30), default="c7g.xlarge")  # AWS Graviton 3
    availability_zone = Column(String(30), default="us-east-1a")
    state = Column(String(20), default="running")  # running, stopped, terminating
    cpu_utilization = Column(Float, default=42.5)  # CloudWatch metric %
    memory_utilization = Column(Float, default=58.0)
    current_streams = Column(Integer, default=8)
    lifecycle_type = Column(String(30), default="Savings Plan")  # On-Demand, Spot, Savings Plan
    ssm_agent_status = Column(String(20), default="Online")  # AWS Systems Manager Managed
    launch_time = Column(DateTime, default=datetime.utcnow)

class CostMetric(Base):
    __tablename__ = "cost_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    period_name = Column(String(50), nullable=False)
    architecture_type = Column(String(50), nullable=False)  # "Pre-Migration / Legacy" vs "AWS Optimized"
    ec2_cost_usd = Column(Float, nullable=False)
    s3_cost_usd = Column(Float, nullable=False)
    rds_cost_usd = Column(Float, nullable=False)
    data_transfer_usd = Column(Float, nullable=False)
    total_cost_usd = Column(Float, nullable=False)
    active_cameras_count = Column(Integer, default=100)
    notes = Column(Text, nullable=True)

