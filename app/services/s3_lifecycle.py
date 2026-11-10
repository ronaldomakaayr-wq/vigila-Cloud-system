from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.models import VideoRecording

class S3LifecycleManager:
    """
    Manages Amazon S3 Lifecycle Policies for VIGILA recordings.
    Enforces cost optimization through tiered storage.
    """
    
    # Official AWS Pricing per GB-month (us-east-1)
    PRICING_PER_GB = {
        "STANDARD": 0.023,
        "STANDARD_IA": 0.0125,
        "GLACIER_FLEXIBLE": 0.0036,
        "DEEP_ARCHIVE": 0.00099
    }

    @classmethod
    def evaluate_and_apply_lifecycle(cls, db: Session) -> Dict[str, Any]:
        """
        Scans all video recordings and transitions them based on age:
        - 0 to 30 days: STANDARD
        - 31 to 90 days: STANDARD_IA
        - 91 to 365 days: GLACIER_FLEXIBLE
        - > 365 days: DEEP_ARCHIVE
        """
        now = datetime.utcnow()
        recordings = db.query(VideoRecording).all()
        
        transitions_applied = []
        total_size_gb = 0.0
        standard_size_gb = 0.0
        ia_size_gb = 0.0
        glacier_size_gb = 0.0
        deep_archive_size_gb = 0.0
        
        for rec in recordings:
            age_days = (now - rec.recorded_at).days
            size_gb = rec.file_size_mb / 1024.0
            total_size_gb += size_gb
            
            target_class = rec.storage_class
            
            if age_days > 365 and rec.storage_class != "DEEP_ARCHIVE":
                target_class = "DEEP_ARCHIVE"
            elif age_days > 90 and rec.storage_class not in ["GLACIER_FLEXIBLE", "DEEP_ARCHIVE"]:
                target_class = "GLACIER_FLEXIBLE"
            elif age_days > 30 and rec.storage_class == "STANDARD":
                target_class = "STANDARD_IA"
                
            if target_class != rec.storage_class:
                old_class = rec.storage_class
                rec.storage_class = target_class
                transitions_applied.append({
                    "id": rec.id,
                    "filename": rec.filename,
                    "age_days": age_days,
                    "from_tier": old_class,
                    "to_tier": target_class
                })
            
            if rec.storage_class == "STANDARD":
                standard_size_gb += size_gb
            elif rec.storage_class == "STANDARD_IA":
                ia_size_gb += size_gb
            elif rec.storage_class == "GLACIER_FLEXIBLE":
                glacier_size_gb += size_gb
            elif rec.storage_class == "DEEP_ARCHIVE":
                deep_archive_size_gb += size_gb

        if transitions_applied:
            db.commit()

        # Calculate Costs
        unoptimized_cost = total_size_gb * cls.PRICING_PER_GB["STANDARD"]
        optimized_cost = (
            standard_size_gb * cls.PRICING_PER_GB["STANDARD"] +
            ia_size_gb * cls.PRICING_PER_GB["STANDARD_IA"] +
            glacier_size_gb * cls.PRICING_PER_GB["GLACIER_FLEXIBLE"] +
            deep_archive_size_gb * cls.PRICING_PER_GB["DEEP_ARCHIVE"]
        )
        
        monthly_savings = max(0.0, unoptimized_cost - optimized_cost)
        savings_pct = (monthly_savings / unoptimized_cost * 100) if unoptimized_cost > 0 else 0

        return {
            "total_recordings_scanned": len(recordings),
            "transitions_executed": len(transitions_applied),
            "distribution_gb": {
                "STANDARD": round(standard_size_gb, 2),
                "STANDARD_IA": round(ia_size_gb, 2),
                "GLACIER_FLEXIBLE": round(glacier_size_gb, 2),
                "DEEP_ARCHIVE": round(deep_archive_size_gb, 2),
                "TOTAL_GB": round(total_size_gb, 2)
            },
            "financial_impact": {
                "cost_if_all_standard_usd": round(unoptimized_cost, 2),
                "current_tiered_cost_usd": round(optimized_cost, 2),
                "monthly_savings_usd": round(monthly_savings, 2),
                "savings_percentage": round(savings_pct, 1)
            },
            "recent_transitions": transitions_applied[:10]
        }

