"""
Streaming utilities for camera feeds
"""
import time
import threading
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image

class FrameProcessor:
    """Handles frame conversion between OpenCV and web formats"""
    
    @staticmethod
    def compress_frame(frame, quality=70):
        """Compress frame to JPEG bytes with specified quality"""
        success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if not success:
            return None
        return buffer.tobytes()
    
    @staticmethod
    def frame_to_base64(frame, quality=70):
        """Convert OpenCV frame to base64 encoded JPEG for web display"""
        if frame is None:
            return None
            
        compressed = FrameProcessor.compress_frame(frame, quality)
        if compressed is None:
            return None
            
        return base64.b64encode(compressed).decode('utf-8')
    
    @staticmethod
    def frame_to_jpeg_response(frame, quality=70):
        """Convert OpenCV frame to JPEG bytes for HTTP response"""
        compressed = FrameProcessor.compress_frame(frame, quality)
        if compressed is None:
            return None
        return compressed

class StreamManager:
    """Manages multiple camera streams with thread safety"""
    
    def __init__(self):
        self.cameras = {}
        self.lock = threading.Lock()
    
    def add_camera(self, camera):
        """Add a camera to the manager"""
        with self.lock:
            self.cameras[camera.name] = camera
            camera.start()
    
    def remove_camera(self, camera_name):
        """Remove a camera from the manager"""
        with self.lock:
            if camera_name in self.cameras:
                self.cameras[camera_name].stop()
                del self.cameras[camera_name]
    
    def get_camera(self, camera_name):
        """Get a camera by name"""
        with self.lock:
            return self.cameras.get(camera_name)
    
    def get_all_cameras(self):
        """Get all cameras"""
        with self.lock:
            return list(self.cameras.values())
    
    def get_camera_names(self):
        """Get all camera names"""
        with self.lock:
            return list(self.cameras.keys())
    
    def start_all(self):
        """Start all cameras"""
        with self.lock:
            for camera in self.cameras.values():
                camera.start()
    
    def stop_all(self):
        """Stop all cameras"""
        with self.lock:
            for camera in self.cameras.values():
                camera.stop()
    
    def get_camera_status(self):
        """Get status of all cameras"""
        status = {}
        with self.lock:
            for name, camera in self.cameras.items():
                status[name] = {
                    "connected": camera.is_connected(),
                    "detection_enabled": camera.detection_enabled,
                    "confidence_threshold": camera.confidence_threshold
                }
        return status
    
    def set_detection_enabled(self, camera_name, enabled):
        """Enable or disable detection for a camera"""
        with self.lock:
            if camera_name in self.cameras:
                self.cameras[camera_name].set_detection_enabled(enabled)
                return True
        return False
    
    def set_confidence_threshold(self, camera_name, threshold):
        """Set confidence threshold for a camera"""
        with self.lock:
            if camera_name in self.cameras:
                self.cameras[camera_name].set_confidence_threshold(threshold)
                return True
        return False
    
    def take_snapshot(self, camera_name, output_dir):
        """Take a snapshot from a camera"""
        with self.lock:
            if camera_name in self.cameras:
                return self.cameras[camera_name].take_snapshot(output_dir)
        return None 