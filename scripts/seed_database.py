import os
import sys
from datetime import datetime, timedelta

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.models import User, Camera, VideoRecording, SecurityAlert, EC2InstanceNode, CostMetric

def seed_initial_data(db: Session):
    # 1. Seed Users if not present
    if not db.query(User).first():
        admin = User(
            username="admin",
            email="admin@vigila.cloud",
            hashed_password=get_password_hash("admin123"),
            role="ADMIN"
        )
        operator = User(
            username="operador",
            email="operador@vigila.cloud",
            hashed_password=get_password_hash("operador123"),
            role="OPERATOR"
        )
        db.add_all([admin, operator])
        db.commit()

    # 2. Seed Cameras if not present
    if not db.query(Camera).first():
        cameras_data = [
            Camera(
                code="CAM-01",
                name="Acceso Principal y Recepción",
                location="Edificio Central - Puerta 1",
                zone="Zona Acceso",
                rtsp_url="rtsp://stream.vigila.cloud/live/cam01",
                resolution="1080p",
                fps=30,
                bitrate_kbps=4096,
                status="RECORDING",
                is_recording=True
            ),
            Camera(
                code="CAM-02",
                name="Perímetro Norte Exterior",
                location="Cerco Perimetral Sector Norte",
                zone="Zona Perimetral",
                rtsp_url="rtsp://stream.vigila.cloud/live/cam02",
                resolution="1080p",
                fps=30,
                bitrate_kbps=4096,
                status="RECORDING",
                is_recording=True
            ),
            Camera(
                code="CAM-03",
                name="Estacionamiento de Clientes",
                location="Subsuelo 1 - Bahía B",
                zone="Zona Vehicular",
                rtsp_url="rtsp://stream.vigila.cloud/live/cam03",
                resolution="1080p",
                fps=25,
                bitrate_kbps=3072,
                status="ONLINE",
                is_recording=True
            ),
            Camera(
                code="CAM-04",
                name="Data Center / Servidores",
                location="Sala Técnica - Nivel 2",
                zone="Zona Crítica",
                rtsp_url="rtsp://stream.vigila.cloud/live/cam04",
                resolution="4K",
                fps=30,
                bitrate_kbps=8192,
                status="RECORDING",
                is_recording=True
            ),
            Camera(
                code="CAM-05",
                name="Almacén de Mercadería",
                location="Hangar 3 - Pasillo A",
                zone="Zona Logística",
                rtsp_url="rtsp://stream.vigila.cloud/live/cam05",
                resolution="1080p",
                fps=30,
                bitrate_kbps=4096,
                status="RECORDING",
                is_recording=True
            ),
            Camera(
                code="CAM-06",
                name="Patio de Carga y Descarga",
                location="Sector Muelles 1-4",
                zone="Zona Logística",
                rtsp_url="rtsp://stream.vigila.cloud/live/cam06",
                resolution="1080p",
                fps=30,
                bitrate_kbps=4096,
                status="RECORDING",
                is_recording=True
            )
        ]
        db.add_all(cameras_data)
        db.commit()

    # 3. Seed Video Recordings with S3 Lifecycle Tiers
    if not db.query(VideoRecording).first():
        now = datetime.utcnow()
        cams = db.query(Camera).all()
        
        recordings = [
            # Tier: STANDARD (Recientes: 0-30 días)
            VideoRecording(
                camera_id=cams[0].id,
                camera_name=cams[0].name,
                filename="rec_cam01_20261109_080000.mp4",
                s3_key="recordings/cam01/2026/11/09/rec_080000.mp4",
                s3_bucket="vigila-surveillance-recordings-archive-prod",
                storage_class="STANDARD",
                file_size_mb=420.5,
                duration_seconds=3600,
                recorded_at=now - timedelta(hours=2),
                is_locked=True
            ),
            VideoRecording(
                camera_id=cams[3].id,
                camera_name=cams[3].name,
                filename="rec_cam04_datacenter_20261108_220000.mp4",
                s3_key="recordings/cam04/2026/11/08/rec_220000.mp4",
                s3_bucket="vigila-surveillance-recordings-archive-prod",
                storage_class="STANDARD",
                file_size_mb=850.0,
                duration_seconds=3600,
                recorded_at=now - timedelta(days=1),
                is_locked=True
            ),
            # Tier: STANDARD_IA (31-90 días)
            VideoRecording(
                camera_id=cams[1].id,
                camera_name=cams[1].name,
                filename="rec_cam02_perimetro_20260920_140000.mp4",
                s3_key="recordings/cam02/2026/09/20/rec_140000.mp4",
                s3_bucket="vigila-surveillance-recordings-archive-prod",
                storage_class="STANDARD_IA",
                file_size_mb=390.2,
                duration_seconds=3600,
                recorded_at=now - timedelta(days=45),
                is_locked=True
            ),
            VideoRecording(
                camera_id=cams[2].id,
                camera_name=cams[2].name,
                filename="rec_cam03_parking_20260910_183000.mp4",
                s3_key="recordings/cam03/2026/09/10/rec_183000.mp4",
                s3_bucket="vigila-surveillance-recordings-archive-prod",
                storage_class="STANDARD_IA",
                file_size_mb=310.0,
                duration_seconds=3600,
                recorded_at=now - timedelta(days=58),
                is_locked=True
            ),
            # Tier: GLACIER_FLEXIBLE (91-365 días)
            VideoRecording(
                camera_id=cams[4].id,
                camera_name=cams[4].name,
                filename="rec_cam05_almacen_20260715_030000.mp4",
                s3_key="recordings/cam05/2026/07/15/rec_030000.mp4",
                s3_bucket="vigila-surveillance-recordings-archive-prod",
                storage_class="GLACIER_FLEXIBLE",
                file_size_mb=415.8,
                duration_seconds=3600,
                recorded_at=now - timedelta(days=115),
                is_locked=True
            ),
            # Tier: DEEP_ARCHIVE (>365 días - Retención legal)
            VideoRecording(
                camera_id=cams[3].id,
                camera_name=cams[3].name,
                filename="rec_cam04_datacenter_auditoria_20251010.mp4",
                s3_key="archive/2025/cam04/rec_legal_audit_20251010.mp4",
                s3_bucket="vigila-surveillance-recordings-archive-prod",
                storage_class="DEEP_ARCHIVE",
                file_size_mb=920.0,
                duration_seconds=3600,
                recorded_at=now - timedelta(days=390),
                is_locked=True
            )
        ]
        db.add_all(recordings)
        db.commit()

    # 4. Seed Security Alerts
    if not db.query(SecurityAlert).first():
        cams = db.query(Camera).all()
        now = datetime.utcnow()
        alerts = [
            SecurityAlert(
                camera_id=cams[1].id,
                camera_name=cams[1].name,
                alert_type="INTRUSION",
                severity="CRITICAL",
                description="Persona no autorizada escalando cerco perimetral detectada por modelo YOLO v8",
                s3_clip_key="alerts/20261109/clip_cam02_intrusion.mp4",
                status="NEW",
                timestamp=now - timedelta(minutes=14)
            ),
            SecurityAlert(
                camera_id=cams[3].id,
                camera_name=cams[3].name,
                alert_type="LINE_CROSSING",
                severity="HIGH",
                description="Ingreso no registrado a pasillo de servidores durante ronda nocturna",
                s3_clip_key="alerts/20261109/clip_cam04_line_crossing.mp4",
                status="ACKNOWLEDGED",
                timestamp=now - timedelta(hours=3)
            ),
            SecurityAlert(
                camera_id=cams[4].id,
                camera_name=cams[4].name,
                alert_type="MOTION_DETECTED",
                severity="MEDIUM",
                description="Movimiento detectado en zona de racks de almacenamiento fuera de turno",
                s3_clip_key="alerts/20261108/clip_cam05_motion.mp4",
                status="RESOLVED",
                timestamp=now - timedelta(hours=18)
            )
        ]
        db.add_all(alerts)
        db.commit()

    # 5. Seed EC2 Worker Nodes (AWS Graviton)
    if not db.query(EC2InstanceNode).first():
        nodes = [
            EC2InstanceNode(
                instance_id="i-08a9f4c3b2e1001",
                instance_type="c7g.xlarge",  # AWS Graviton 3 (Arm-based, 20% lower cost)
                availability_zone="us-east-1a",
                state="running",
                cpu_utilization=44.2,
                memory_utilization=52.8,
                current_streams=14,
                lifecycle_type="Savings Plan",
                ssm_agent_status="Online"
            ),
            EC2InstanceNode(
                instance_id="i-08a9f4c3b2e1002",
                instance_type="c7g.xlarge",
                availability_zone="us-east-1b",
                state="running",
                cpu_utilization=49.0,
                memory_utilization=56.1,
                current_streams=16,
                lifecycle_type="Savings Plan",
                ssm_agent_status="Online"
            ),
            EC2InstanceNode(
                instance_id="i-08a9f4c3b2e1003",
                instance_type="c7g.large",
                availability_zone="us-east-1a",
                state="running",
                cpu_utilization=32.5,
                memory_utilization=39.0,
                current_streams=6,
                lifecycle_type="Spot",  # Spot instance for async encoding
                ssm_agent_status="Online"
            )
        ]
        db.add_all(nodes)
        db.commit()

    # 6. Seed Monthly Cost Metrics (Pre-migration vs Optimized)
    if not db.query(CostMetric).first():
        metrics = [
            CostMetric(
                period_name="Junio 2026",
                architecture_type="Pre-Migración (Sobredimensionado)",
                ec2_cost_usd=2850.00,
                s3_cost_usd=1420.00,
                rds_cost_usd=680.00,
                data_transfer_usd=450.00,
                total_cost_usd=5400.00,
                active_cameras_count=60,
                notes="Instancias EC2 x86 On-Demand sin Auto Scaling; S3 todo en Standard sin ciclo de vida."
            ),
            CostMetric(
                period_name="Julio 2026",
                architecture_type="Pre-Migración (Sobredimensionado)",
                ec2_cost_usd=2920.00,
                s3_cost_usd=1580.00,
                rds_cost_usd=690.00,
                data_transfer_usd=490.00,
                total_cost_usd=5680.00,
                active_cameras_count=75,
                notes="Incremento de costos crítico reportado por el caso práctico VIGILA."
            ),
            CostMetric(
                period_name="Agosto 2026 (Transición)",
                architecture_type="AWS Optimizado - Fase Piloto",
                ec2_cost_usd=1800.00,
                s3_cost_usd=850.00,
                rds_cost_usd=480.00,
                data_transfer_usd=280.00,
                total_cost_usd=3410.00,
                active_cameras_count=90,
                notes="Implementación de Auto Scaling y primeros filtros S3 Lifecycle."
            ),
            CostMetric(
                period_name="Septiembre 2026",
                architecture_type="AWS Optimizado (Well-Architected)",
                ec2_cost_usd=1020.00,
                s3_cost_usd=310.00,
                rds_cost_usd=360.00,
                data_transfer_usd=140.00,
                total_cost_usd=1830.00,
                active_cameras_count=100,
                notes="Migración a AWS Graviton 3, Savings Plans, S3 Glacier y CloudFront."
            ),
            CostMetric(
                period_name="Octubre 2026",
                architecture_type="AWS Optimizado (Well-Architected)",
                ec2_cost_usd=980.00,
                s3_cost_usd=280.00,
                rds_cost_usd=340.00,
                data_transfer_usd=120.00,
                total_cost_usd=1720.00,
                active_cameras_count=100,
                notes="Ahorro sostenido del 68% ($3,960/mes) con rendimiento y seguridad mejorados."
            )
        ]
        db.add_all(metrics)
        db.commit()

if __name__ == "__main__":
    from app.core.database import SessionLocal, Base, engine
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_initial_data(db)
    print("Database seeded successfully with initial VIGILA cloud surveillance data.")
    db.close()
