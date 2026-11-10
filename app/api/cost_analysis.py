from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.models.models import CostMetric
from app.schemas.schemas import CostItem, CostComparisonSummary

router = APIRouter(prefix="/cost-analysis", tags=["Cost Optimization & Financial ROI"])

@router.get("/summary", response_model=CostComparisonSummary)
def get_cost_comparison_summary(db: Session = Depends(get_db)):
    """
    Returns financial impact analysis:
    Pre-Migration / Unoptimized Cloud vs AWS Well-Architected Optimized Architecture.
    """
    # Baseline comparison metrics
    legacy = {
        "ec2": 2850.00,
        "s3": 1400.00,
        "rds": 650.00,
        "data_transfer": 450.00,
        "total": 5350.00
    }
    
    optimized = {
        "ec2": 980.00,        # Auto Scaling + Graviton 3 + Compute Savings Plan
        "s3": 280.00,         # S3 Lifecycle Policies (Standard -> IA -> Glacier)
        "rds": 340.00,        # Aurora / RDS Graviton Multi-AZ right-sized
        "data_transfer": 120.00, # CloudFront CDN edge caching
        "total": 1720.00
    }
    
    monthly_savings = legacy["total"] - optimized["total"]
    savings_pct = (monthly_savings / legacy["total"]) * 100
    annual_savings = monthly_savings * 12
    
    breakdown = {
        "EC2_Compute": {
            "legacy_usd": legacy["ec2"],
            "optimized_usd": optimized["ec2"],
            "savings_usd": legacy["ec2"] - optimized["ec2"],
            "savings_pct": 65.6,
            "actions_applied": [
                "Auto Scaling Group con target tracking al 70% CPU",
                "Migración a procesadores AWS Graviton 3 (c7g.xlarge)",
                "Contrato Compute Savings Plan a 1 año para carga base (24/7)",
                "Uso de instancias Spot para transcodificación secundaria de video"
            ]
        },
        "S3_Storage": {
            "legacy_usd": legacy["s3"],
            "optimized_usd": optimized["s3"],
            "savings_usd": legacy["s3"] - optimized["s3"],
            "savings_pct": 80.0,
            "actions_applied": [
                "Políticas de ciclo de vida automáticas (S3 Lifecycle)",
                "Transición a S3 Standard-IA a los 30 días",
                "Transición a S3 Glacier Flexible Retrieval a los 90 días",
                "Transición a S3 Glacier Deep Archive a los 365 días"
            ]
        },
        "RDS_Database": {
            "legacy_usd": legacy["rds"],
            "optimized_usd": optimized["rds"],
            "savings_usd": legacy["rds"] - optimized["rds"],
            "savings_pct": 47.7,
            "actions_applied": [
                "Right-sizing de instancia a db.m7g.large (Graviton)",
                "Despliegue Multi-AZ para alta disponibilidad y tolerancia a fallos",
                "2 Read Replicas para distribuir consultas de monitoreo en tiempo real",
                "Amazon ElastiCache Redis para caching de sesiones de cámaras"
            ]
        },
        "Data_Transfer_Security": {
            "legacy_usd": legacy["data_transfer"],
            "optimized_usd": optimized["data_transfer"],
            "savings_usd": legacy["data_transfer"] - optimized["data_transfer"],
            "savings_pct": 73.3,
            "actions_applied": [
                "Distribución mediante Amazon CloudFront CDN",
                "Eliminación de IPs públicas y Bastion Hosts con AWS Systems Manager Session Manager",
                "Cifrado de extremo a extremo con AWS KMS y ACM (TLS 1.3)"
            ]
        }
    }

    return {
        "legacy_cost_monthly": legacy["total"],
        "optimized_cost_monthly": optimized["total"],
        "monthly_savings_usd": round(monthly_savings, 2),
        "savings_percentage": round(savings_pct, 1),
        "annual_savings_usd": round(annual_savings, 2),
        "breakdown_by_service": breakdown
    }

@router.get("/history", response_model=List[CostItem])
def get_cost_history(db: Session = Depends(get_db)):
    return db.query(CostMetric).order_by(CostMetric.id).all()

