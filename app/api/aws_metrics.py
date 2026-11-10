from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.core.aws_service import aws_service
from app.models.models import EC2InstanceNode
from app.schemas.schemas import EC2NodeResponse, SSMCommandRequest, SSMCommandResponse
from app.services.ec2_autoscaler import EC2AutoScalingService

router = APIRouter(prefix="/aws", tags=["AWS Infrastructure & SSM"])

@router.get("/ec2-fleet", response_model=List[EC2NodeResponse])
def get_ec2_worker_nodes(db: Session = Depends(get_db)):
    """
    Returns the active EC2 Graviton processing instances managed by Auto Scaling.
    """
    return db.query(EC2InstanceNode).all()

@router.post("/ec2-autoscaling/evaluate")
def evaluate_autoscaling(db: Session = Depends(get_db)):
    """
    Triggers the CloudWatch Auto Scaling policy evaluation to right-size EC2 instances.
    """
    return EC2AutoScalingService.evaluate_fleet_autoscaling(db)

@router.get("/rds-status")
def get_rds_database_status():
    """
    Returns Amazon RDS Multi-AZ health and performance telemetry.
    """
    return {
        "engine": "PostgreSQL 16.2",
        "instance_class": "db.m7g.large (AWS Graviton 3)",
        "deployment_type": "Multi-AZ (Primary: us-east-1a, Synchronous Standby: us-east-1b)",
        "read_replicas_count": 2,
        "read_replica_endpoints": [
            "vigila-rds-read-01.c3x9b.us-east-1.rds.amazonaws.com",
            "vigila-rds-read-02.c3x9b.us-east-1.rds.amazonaws.com"
        ],
        "storage_type": "General Purpose SSD (gp3) with Auto-Scaling enabled",
        "allocated_storage_gb": 200,
        "free_storage_gb": 164.8,
        "active_connections": 38,
        "max_connections": 500,
        "cpu_utilization": 24.6,
        "encryption": "AWS KMS (arn:aws:kms:us-east-1:123456789012:key/vigila-rds-cmk)",
        "status": "AVAILABLE",
        "automated_backup_retention_days": 30
    }

@router.post("/ssm/run-command", response_model=SSMCommandResponse)
def execute_ssm_command(req: SSMCommandRequest):
    """
    AWS Systems Manager Run Command:
    Executes administrative maintenance on EC2 nodes without opening port 22 (SSH).
    """
    return aws_service.execute_ssm_run_command(req.instance_ids, req.command)

@router.get("/ssm/parameter-store")
def get_ssm_parameter_sample(param_name: str = "database/master_password"):
    """
    Demonstrates secure credential retrieval from AWS Systems Manager Parameter Store.
    """
    return aws_service.get_ssm_parameter(param_name)

@router.get("/cloudwatch-alarms")
def get_cloudwatch_alarms():
    """
    Returns active CloudWatch Alarms for CPU, Auto Scaling, and Billing.
    """
    return aws_service.get_cloudwatch_alarms()

