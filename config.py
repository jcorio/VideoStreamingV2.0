"""
Configuration file for RTSP Camera Streaming Application
"""

# Camera RTSP stream URLs
CAMERA_STREAMS = {
    "Camera 1": "rtsp://jason:Jcorio44!@68.58.76.245:554/cam/realmonitor?channel=1&subtype=1",
    "Camera 2": "rtsp://jason:Jcorio44!@68.58.76.245:554/cam/realmonitor?channel=2&subtype=1",
    "Camera 3": "rtsp://jason:Jcorio44!@68.58.76.245:554/cam/realmonitor?channel=3&subtype=1",
    "Camera 4": "rtsp://jason:Jcorio44!@68.58.76.245:554/cam/realmonitor?channel=4&subtype=1",
    "Camera 5": "rtsp://jason:Jcorio44!@68.58.76.245:554/cam/realmonitor?channel=5&subtype=1",
    "Camera 6": "rtsp://jason:Jcorio44!@68.58.76.245:554/cam/realmonitor?channel=6&subtype=1",
    "Camera 7": "rtsp://jason:Jcorio44!@68.58.76.245:554/cam/realmonitor?channel=7&subtype=1",
    "Camera 8": "rtsp://jason:Jcorio44!@68.58.76.245:554/cam/realmonitor?channel=8&subtype=1",
    "Camera 9": "rtsp://jason:Jcorio44!@68.58.76.245:554/cam/realmonitor?channel=9&subtype=1",
    "Camera 10": "rtsp://jason:Jcorio44!@68.58.76.245:554/cam/realmonitor?channel=10&subtype=1",
    "Camera 11": "rtsp://jason:Jcorio44!@68.58.76.245:554/cam/realmonitor?channel=11&subtype=1",
    "Camera 12": "rtsp://jason:Jcorio44!@68.58.76.245:554/cam/realmonitor?channel=12&subtype=1",
    "Camera 13": "rtsp://jason:Jcorio44!@68.58.76.245:554/cam/realmonitor?channel=13&subtype=1",
}

# OpenCV video capture settings
CAPTURE_SETTINGS = {
    "resolution": (640, 480),  # Width, Height
    "fps": 15,                 # Target frames per second
    "reconnect_delay": 5,      # Seconds to wait before reconnection attempt
    "retry_attempts": 5,       # Number of connection retry attempts
}

# Object detection settings
DETECTION_SETTINGS = {
    "default_enabled": True,         # Enable detection by default
    "confidence_threshold": 0.5,     # Default confidence threshold
    "refresh_interval": 3,           # Frames between detections
    "yolo_model": "yolov8n.pt",      # YOLOv8 model to use
    "device": "cpu",                 # Use "cuda" for GPU acceleration if available
}

# Web application settings
APP_SETTINGS = {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": False,
    "snapshot_dir": "snapshots",  # Directory to save snapshots
    "socket_timeout": 60,         # Socket timeout in seconds
} 