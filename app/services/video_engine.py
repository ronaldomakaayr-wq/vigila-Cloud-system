import io
import time
import math
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

class VideoEngine:
    """
    Simulates high-performance cloud video streams, frame processing,
    and movement/intrusion analysis. Generates real-time MJPEG streams.
    """
    
    def __init__(self):
        self.frame_counters = {}

    def generate_camera_frame(self, camera_code: str, camera_name: str, status: str, resolution_str: str = "1080p") -> bytes:
        """
        Renders a simulated real-time CCTV security camera frame
        with telemetry overlay, live timestamp, grid, and simulated detection boxes.
        """
        width, height = 640, 360  # Optimized for streaming preview
        image = Image.new("RGB", (width, height), color=(18, 24, 32))
        draw = ImageDraw.Draw(image)
        
        # Grid lines (CCTV monitoring effect)
        for x in range(0, width, 80):
            draw.line([(x, 0), (x, height)], fill=(28, 38, 48), width=1)
        for y in range(0, height, 60):
            draw.line([(y, 0), (y, width)], fill=(28, 38, 48), width=1)
        
        # Simulated background scene (interior room or perimeter fence)
        # Horizon / wall line
        draw.line([(0, 240), (width, 240)], fill=(45, 55, 72), width=2)
        # Perspective floor lines
        draw.line([(0, 360), (220, 240)], fill=(30, 41, 59), width=1)
        draw.line([(640, 360), (420, 240)], fill=(30, 41, 59), width=1)
        
        # Live Time & Telemetry
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        t = time.time()
        
        # Telemetry Header
        header_text = f"AWS VIGILA | {camera_code} - {camera_name} | {resolution_str} @ 30FPS | CLOUD RECORDING"
        draw.rectangle([(10, 10), (width - 10, 35)], fill=(10, 15, 20, 200), outline=(50, 70, 90))
        draw.text((18, 16), header_text, fill=(0, 255, 170))
        
        # Live Timestamp & Rec indicator
        rec_dot_color = (255, 40, 40) if int(t * 2) % 2 == 0 else (100, 20, 20)
        draw.ellipse([(width - 95, 16), (width - 83, 28)], fill=rec_dot_color)
        draw.text((width - 75, 16), "REC", fill=(255, 255, 255))
        
        # Live Motion Simulation (A moving object box to demonstrate AI Computer Vision)
        obj_x = int(240 + 140 * math.sin(t * 0.8))
        obj_y = int(190 + 30 * math.cos(t * 0.8))
        box_w, box_h = 70, 110
        
        # Draw AI Detection Bounding Box
        box_color = (0, 255, 128) if status == "ONLINE" else (255, 170, 0)
        draw.rectangle([(obj_x, obj_y), (obj_x + box_w, obj_y + box_h)], outline=box_color, width=2)
        draw.text((obj_x + 4, obj_y - 14), "PERSON [94.2%]", fill=box_color)
        
        # Bottom Telemetry Bar (AWS Cloud Telemetry)
        footer_text = f"{now_str} | AWS KMS AES-256 | S3 Ingest: 4.2 MB/s | SSM: Active"
        draw.rectangle([(10, height - 32), (width - 10, height - 10)], fill=(10, 15, 20, 200), outline=(50, 70, 90))
        draw.text((18, height - 28), footer_text, fill=(160, 190, 210))
        
        # Crosshair in center
        cx, cy = width // 2, height // 2
        draw.line([(cx - 12, cy), (cx + 12, cy)], fill=(0, 255, 255, 150), width=1)
        draw.line([(cx, cy - 12), (cx, cy + 12)], fill=(0, 255, 255, 150), width=1)
        
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=75)
        return buffer.getvalue()

    def stream_generator(self, camera_code: str, camera_name: str, status: str, resolution: str = "1080p"):
        """
        Yields multipart JPEG frames for continuous browser rendering.
        """
        while True:
            frame_bytes = self.generate_camera_frame(camera_code, camera_name, status, resolution)
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
            time.sleep(0.1)  # 10 FPS preview stream to conserve bandwidth

video_engine = VideoEngine()

