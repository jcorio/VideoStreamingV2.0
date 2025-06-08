"""
Camera module for handling RTSP streams with object detection.
"""
import os
import time
import threading
import cv2
import numpy as np
from ultralytics import YOLO
from config import CAPTURE_SETTINGS, DETECTION_SETTINGS

class Camera:
    """
    Camera class to handle RTSP stream connection, frame processing and object detection
    """
    def __init__(self, name, url, detection_enabled=True):
        self.name = name
        self.url = url
        self.cap = None
        self.frame = None
        self.processed_frame = None
        self.last_frame_time = 0
        self.connected = False
        self.running = False
        self.detection_enabled = detection_enabled
        self.detection_model = None
        self.confidence_threshold = DETECTION_SETTINGS["confidence_threshold"]
        self.resolution = CAPTURE_SETTINGS["resolution"]
        self.reconnect_delay = CAPTURE_SETTINGS["reconnect_delay"]
        self.frame_count = 0
        self.refresh_interval = DETECTION_SETTINGS["refresh_interval"]
        self.lock = threading.Lock()
        self.thread = None
        self.detections = []
        
    def connect(self):
        """Attempt to connect to the RTSP stream"""
        if self.cap is not None:
            self.cap.release()
            
        # Use RTSP over TCP for more reliable streaming (reduces frame dropping)
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
        
        # Set OpenCV capture properties for optimal streaming
        self.cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)  # Small buffer size to reduce latency
        
        if self.cap.isOpened():
            self.connected = True
            self.last_frame_time = time.time()
            return True
        else:
            self.connected = False
            return False
            
    def load_detection_model(self):
        """Load YOLOv8 detection model"""
        try:
            self.detection_model = YOLO(DETECTION_SETTINGS["yolo_model"])
            return True
        except Exception as e:
            print(f"Error loading detection model for {self.name}: {e}")
            self.detection_model = None
            return False
            
    def start(self):
        """Start camera streaming thread"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._stream_thread)
        self.thread.daemon = True
        self.thread.start()
        
        # Load detection model in separate thread to avoid blocking
        if self.detection_enabled:
            model_thread = threading.Thread(target=self.load_detection_model)
            model_thread.daemon = True
            model_thread.start()
            
    def stop(self):
        """Stop camera streaming thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()
        self.connected = False
        
    def _stream_thread(self):
        """Main camera streaming thread function"""
        retry_count = 0
        
        while self.running:
            # Attempt connection if not connected
            if not self.connected:
                if retry_count < CAPTURE_SETTINGS["retry_attempts"]:
                    success = self.connect()
                    if success:
                        retry_count = 0
                    else:
                        retry_count += 1
                        time.sleep(self.reconnect_delay)
                        continue
                else:
                    # Create an error frame to show connection issue
                    error_frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
                    cv2.putText(error_frame, f"Connection Error: {self.name}", 
                              (30, self.resolution[1]//2 - 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.putText(error_frame, "Attempting to reconnect...", 
                              (30, self.resolution[1]//2 + 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    with self.lock:
                        self.frame = error_frame.copy()
                        self.processed_frame = error_frame.copy()
                    
                    time.sleep(self.reconnect_delay)
                    retry_count = 0  # Reset count and try again
                    continue
            
            # Read frame from stream
            success, frame = self.cap.read()
            
            if not success:
                self.connected = False
                continue
                
            # Update last frame time
            self.last_frame_time = time.time()
            
            # Resize frame if needed
            if frame.shape[1] != self.resolution[0] or frame.shape[0] != self.resolution[1]:
                frame = cv2.resize(frame, self.resolution)
                
            # Process frame with object detection if enabled
            processed = frame.copy()
            
            if self.detection_enabled and self.detection_model and self.frame_count % self.refresh_interval == 0:
                self._detect_objects(processed)
            else:
                # Draw existing detections on the frame
                self._draw_detections(processed)
                
            # Store frames with thread safety
            with self.lock:
                self.frame = frame.copy()
                self.processed_frame = processed.copy()
                
            self.frame_count += 1
            
            # Control the frame rate to avoid excessive CPU usage
            time.sleep(1.0 / CAPTURE_SETTINGS["fps"])
            
    def _detect_objects(self, frame):
        """Run object detection on the current frame"""
        if not self.detection_model:
            return
            
        try:
            # Run YOLOv8 inference on the frame
            results = self.detection_model(frame, conf=self.confidence_threshold)
            
            # Store the detection results
            self.detections = []
            
            for result in results:
                boxes = result.boxes.cpu().numpy()
                
                for i, box in enumerate(boxes):
                    x1, y1, x2, y2 = box.xyxy[0].astype(int)
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = result.names[class_id]
                    
                    self.detections.append({
                        "bbox": (x1, y1, x2, y2),
                        "confidence": confidence,
                        "class_id": class_id,
                        "class_name": class_name
                    })
                    
            # Draw detections on the frame
            self._draw_detections(frame)
        except Exception as e:
            print(f"Detection error on {self.name}: {e}")
            
    def _draw_detections(self, frame):
        """Draw detection boxes and labels on the frame"""
        for det in self.detections:
            x1, y1, x2, y2 = det["bbox"]
            label = f"{det['class_name']} {det['confidence']:.2f}"
            
            # Draw rectangle around the object
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw filled rectangle for text background
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(frame, (x1, y1 - text_size[1] - 10), (x1 + text_size[0], y1), (0, 255, 0), -1)
            
            # Draw text label
            cv2.putText(frame, label, (x1, y1 - 5), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
    def get_frame(self, with_detection=True):
        """Get the current frame with thread safety"""
        with self.lock:
            if with_detection and self.processed_frame is not None:
                return self.processed_frame.copy()
            elif self.frame is not None:
                return self.frame.copy()
            else:
                # Return a blank frame if no frames are available
                blank = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
                cv2.putText(blank, f"Waiting for stream: {self.name}", 
                          (30, self.resolution[1]//2), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                return blank
                
    def set_detection_enabled(self, enabled):
        """Enable or disable object detection"""
        self.detection_enabled = enabled
        
    def set_confidence_threshold(self, threshold):
        """Set confidence threshold for object detection"""
        self.confidence_threshold = threshold
        
    def is_connected(self):
        """Check if the camera is connected"""
        # Consider a stream as disconnected if no frames received for more than 5 seconds
        if not self.connected:
            return False
        if time.time() - self.last_frame_time > 5:
            self.connected = False
            return False
        return True
        
    def take_snapshot(self, output_dir):
        """Save current frame as image snapshot"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{output_dir}/{self.name.replace(' ', '_')}_{timestamp}.jpg"
        
        frame = self.get_frame(with_detection=True)
        if frame is not None:
            cv2.imwrite(filename, frame)
            return filename
        return None 