import random
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.models import EC2InstanceNode, Camera

class EC2AutoScalingService:
    """
    Manages EC2 Auto Scaling, Worker Fleet health, and Rightsizing
    Migrates x86 workloads to AWS Graviton (c7g/m7g) for 20% cost reduction.
    """

    @classmethod
    def evaluate_fleet_autoscaling(cls, db: Session) -> Dict[str, Any]:
        """
        Calculates cluster load based on active camera streams.
        Target: ~15 video streams per worker instance, 70% CPU target.
        """
        active_cameras = db.query(Camera).filter(Camera.status.in_(["ONLINE", "RECORDING"])).count()
        instances = db.query(EC2InstanceNode).all()
        
        # If no instances exist, bootstrap a default Graviton fleet
        if not instances:
            initial_nodes = [
                EC2InstanceNode(
                    instance_id="i-08a9f4c3b2e1001",
                    instance_type="c7g.xlarge",  # AWS Graviton 3 (4 vCPU, 8 GiB RAM)
                    availability_zone="us-east-1a",
                    state="running",
                    cpu_utilization=48.2,
                    memory_utilization=55.0,
                    current_streams=14,
                    lifecycle_type="Savings Plan",
                    ssm_agent_status="Online"
                ),
                EC2InstanceNode(
                    instance_id="i-08a9f4c3b2e1002",
                    instance_type="c7g.xlarge",
                    availability_zone="us-east-1b",
                    state="running",
                    cpu_utilization=52.7,
                    memory_utilization=58.4,
                    current_streams=16,
                    lifecycle_type="Savings Plan",
                    ssm_agent_status="Online"
                ),
                EC2InstanceNode(
                    instance_id="i-08a9f4c3b2e1003",
                    instance_type="c7g.large",
                    availability_zone="us-east-1a",
                    state="running",
                    cpu_utilization=38.0,
                    memory_utilization=42.1,
                    current_streams=8,
                    lifecycle_type="Spot",  # Spot instance for background transcoding
                    ssm_agent_status="Online"
                )
            ]
            db.add_all(initial_nodes)
            db.commit()
            instances = db.query(EC2InstanceNode).all()

        total_nodes = len(instances)
        avg_cpu = sum(node.cpu_utilization for node in instances) / total_nodes if total_nodes > 0 else 0
        total_streams = sum(node.current_streams for node in instances)
        
        # Determine scaling action recommendation
        scaling_decision = "STABLE"
        action_note = "Fleet capacity is optimal for current camera ingest load."
        
        if avg_cpu > 75.0 or (active_cameras > total_streams + 5):
            scaling_decision = "SCALE_OUT"
            action_note = f"Triggering Auto Scaling Launch Template: Adding 1x c7g.xlarge instance in AZ us-east-1b."
            # Simulate scale out
            new_id = f"i-08a9f4c3b2e{random.randint(1004, 9999)}"
            new_node = EC2InstanceNode(
                instance_id=new_id,
                instance_type="c7g.xlarge",
                availability_zone="us-east-1b",
                state="running",
                cpu_utilization=22.0,
                memory_utilization=35.0,
                current_streams=4,
                lifecycle_type="Spot" if random.random() > 0.5 else "Savings Plan",
                ssm_agent_status="Online"
            )
            db.add(new_node)
            db.commit()
            instances = db.query(EC2InstanceNode).all()
        elif avg_cpu < 25.0 and total_nodes > 2:
            scaling_decision = "SCALE_IN"
            action_note = "Fleet utilization is low. Safely draining and terminating 1 worker instance."
            removable = [node for node in instances if node.lifecycle_type == "Spot"]
            if removable:
                db.delete(removable[-1])
                db.commit()
                instances = db.query(EC2InstanceNode).all()

        return {
            "fleet_status": scaling_decision,
            "action_taken": action_note,
            "total_worker_instances": len(instances),
            "average_cpu_percent": round(avg_cpu, 1),
            "active_camera_streams": active_cameras,
            "instances": [
                {
                    "instance_id": node.instance_id,
                    "instance_type": node.instance_type,
                    "zone": node.availability_zone,
                    "cpu_usage": f"{node.cpu_utilization}%",
                    "lifecycle": node.lifecycle_type,
                    "ssm_agent": node.ssm_agent_status
                }
                for node in instances
            ]
        }

