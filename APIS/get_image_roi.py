import cv2
from fastapi import HTTPException
import base64

def capture_frame(rtsp_link):
    # Open RTSP stream
    cap = cv2.VideoCapture(rtsp_link)

    
    if not cap.isOpened():
        raise HTTPException(status_code=404, detail="Video stream not found")
    
    # Read a single frame
    ret, frame = cap.read()
    if not ret:
        raise HTTPException(status_code=500, detail="Failed to capture frame")

    # Convert frame to JPEG
    print("frame : ",frame.shape)
    _, img_encoded = cv2.imencode('.jpg', frame)
    img_bytes = img_encoded.tobytes()

    base64_str = base64.b64encode(img_bytes).decode('utf-8')

    return base64_str