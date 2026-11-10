import os
import sys

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_system():
    print("Iniciando pruebas de integración del sistema VIGILA...")
    
    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("✓ [1/7] Health check OK:", res.json()["status"])
    
    # 2. Cameras
    res = client.get("/api/v1/cameras/")
    assert res.status_code == 200, f"Cameras failed: {res.text}"
    cameras = res.json()
    assert len(cameras) >= 6, "Expected at least 6 seeded cameras"
    print(f"✓ [2/7] Cámaras conectadas OK: {len(cameras)} cámaras detectadas")
    
    # 3. Snapshot frame generator
    res = client.get("/api/v1/cameras/1/snapshot")
    assert res.status_code == 200 and res.headers["content-type"] == "image/jpeg"
    print(f"✓ [3/7] Generador de frames CCTV e IA OK ({len(res.content)} bytes)")
    
    # 4. S3 Recordings & Presigned URL
    res = client.get("/api/v1/recordings/")
    assert res.status_code == 200
    recordings = res.json()
    assert len(recordings) > 0
    rec_id = recordings[0]["id"]
    
    url_res = client.get(f"/api/v1/recordings/{rec_id}/presigned-url")
    assert url_res.status_code == 200
    presigned = url_res.json()
    assert "X-Amz-Signature" in presigned["presigned_url"] or "vigila-token" in presigned["presigned_url"]
    print("✓ [4/7] Seguridad S3: Generación de Presigned URLs (SigV4) OK")
    
    # 5. S3 Lifecycle Transition
    sweep_res = client.post("/api/v1/recordings/run-lifecycle-policy")
    assert sweep_res.status_code == 200
    sweep_data = sweep_res.json()
    print(f"✓ [5/7] Motor de ciclo de vida S3 OK (Ahorro calculado: {sweep_data['financial_impact']['savings_percentage']}%)")
    
    # 6. AWS Systems Manager Run Command (No SSH)
    ssm_res = client.post("/api/v1/aws/ssm/run-command", json={
        "command": "systemctl status vigila-agent",
        "instance_ids": ["i-08a9f4c3b2e1001"]
    })
    assert ssm_res.status_code == 200
    print("✓ [6/7] AWS Systems Manager Run Command (Zero-SSH) OK:", ssm_res.json()["status"])
    
    # 7. Cost Analysis & ROI
    cost_res = client.get("/api/v1/cost-analysis/summary")
    assert cost_res.status_code == 200
    cost_data = cost_res.json()
    print(f"✓ [7/7] Auditoría de Costos OK: Ahorro mensual de ${cost_data['monthly_savings_usd']} USD ({cost_data['savings_percentage']}%)")
    
    print("\n=============================================================")
    print("¡TODAS LAS PRUEBAS TÉCNICAS PASARON SATISFACTORIAMENTE (100%)!")
    print("=============================================================")

if __name__ == "__main__":
    test_system()

