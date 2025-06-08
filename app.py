"""
Main Flask application for RTSP camera streaming with object detection
"""
import os
import time
import json
import threading
from flask import Flask, render_template, Response, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from camera import Camera
from streaming import FrameProcessor, StreamManager
from config import CAMERA_STREAMS, APP_SETTINGS, DETECTION_SETTINGS

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'rtsp_streaming_secret_key'

# Initialize SocketIO with async mode
socketio = SocketIO(app, async_mode='eventlet', ping_timeout=APP_SETTINGS["socket_timeout"])

# Initialize stream manager
stream_manager = StreamManager()

# Ensure snapshot directory exists
os.makedirs(APP_SETTINGS["snapshot_dir"], exist_ok=True)

# Flag to control the background thread
thread_running = False
thread_lock = threading.Lock()

def background_thread():
    """Background thread to emit camera frames to clients"""
    global thread_running
    fps_limit = 10  # Limit frames per second for browser performance
    frame_interval = 1.0 / fps_limit
    last_frame_time = {}

    while thread_running:
        # Get current time
        current_time = time.time()
        
        # Process each camera
        for camera in stream_manager.get_all_cameras():
            # Check if enough time has passed since the last frame
            if camera.name not in last_frame_time or (current_time - last_frame_time[camera.name]) >= frame_interval:
                # Get frame with object detection
                frame = camera.get_frame(with_detection=True)
                
                # Convert to base64
                frame_base64 = FrameProcessor.frame_to_base64(frame)
                
                # Emit the frame through SocketIO if valid
                if frame_base64:
                    socketio.emit('camera_frame', {
                        'camera_name': camera.name,
                        'frame': frame_base64,
                        'connected': camera.is_connected(),
                        'timestamp': current_time
                    }, namespace='/stream')
                    
                    # Update last frame time
                    last_frame_time[camera.name] = current_time
        
        # Emit camera status every 5 seconds
        if 'status_time' not in last_frame_time or (current_time - last_frame_time['status_time']) >= 5:
            socketio.emit('camera_status', stream_manager.get_camera_status(), namespace='/stream')
            last_frame_time['status_time'] = current_time
            
        # Sleep to avoid high CPU usage
        socketio.sleep(0.01)

@app.route('/')
def index():
    """Route for the main dashboard page"""
    return render_template('index.html', 
                           camera_names=stream_manager.get_camera_names(),
                           detection_settings=DETECTION_SETTINGS)

@app.route('/stream/<camera_name>')
def stream(camera_name):
    """Route for MJPEG streaming of a specific camera (fallback for non-websocket browsers)"""
    def generate():
        while True:
            camera = stream_manager.get_camera(camera_name)
            if camera:
                frame = camera.get_frame(with_detection=True)
                if frame is not None:
                    jpeg_data = FrameProcessor.frame_to_jpeg_response(frame)
                    if jpeg_data:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + jpeg_data + b'\r\n\r\n')
            # Limit framerate
            time.sleep(0.1)
            
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/snapshot/<camera_name>', methods=['POST'])
def take_snapshot(camera_name):
    """Route for taking a snapshot from a specific camera"""
    snapshot_path = stream_manager.take_snapshot(camera_name, APP_SETTINGS["snapshot_dir"])
    if snapshot_path:
        filename = os.path.basename(snapshot_path)
        return jsonify({'success': True, 'filename': filename})
    else:
        return jsonify({'success': False, 'error': 'Failed to take snapshot'})

@app.route('/snapshots/<filename>')
def get_snapshot(filename):
    """Route for accessing saved snapshots"""
    return send_from_directory(APP_SETTINGS["snapshot_dir"], filename)

@app.route('/snapshots')
def list_snapshots():
    """Route for listing all saved snapshots"""
    snapshots = []
    if os.path.exists(APP_SETTINGS["snapshot_dir"]):
        for filename in os.listdir(APP_SETTINGS["snapshot_dir"]):
            if filename.endswith('.jpg'):
                filepath = os.path.join(APP_SETTINGS["snapshot_dir"], filename)
                snapshots.append({
                    'filename': filename,
                    'timestamp': os.path.getmtime(filepath),
                    'url': f'/snapshots/{filename}'
                })
    return jsonify(snapshots)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Route for getting or updating camera settings"""
    if request.method == 'POST':
        data = request.json
        success = True
        message = "Settings updated successfully"
        
        # Update camera detection settings
        if 'camera_name' in data and 'detection_enabled' in data:
            success = stream_manager.set_detection_enabled(
                data['camera_name'], 
                data['detection_enabled']
            )
            
        # Update confidence threshold
        if 'camera_name' in data and 'confidence_threshold' in data:
            success = stream_manager.set_confidence_threshold(
                data['camera_name'], 
                float(data['confidence_threshold'])
            )
            
        if not success:
            message = "Failed to update settings"
            
        return jsonify({'success': success, 'message': message})
    else:
        # Return current settings
        return jsonify(stream_manager.get_camera_status())

@socketio.on('connect', namespace='/stream')
def socket_connect():
    """Handle client connection to SocketIO"""
    global thread_running
    
    # Start background thread if not already running
    with thread_lock:
        if not thread_running:
            thread_running = True
            socketio.start_background_task(target=background_thread)
    
    # Send initial camera status
    emit('camera_status', stream_manager.get_camera_status())

@socketio.on('disconnect', namespace='/stream')
def socket_disconnect():
    """Handle client disconnection from SocketIO"""
    # We don't stop the background thread here as other clients might be connected
    pass

def initialize_cameras():
    """Initialize and start all camera streams"""
    for name, url in CAMERA_STREAMS.items():
        camera = Camera(name, url, detection_enabled=DETECTION_SETTINGS["default_enabled"])
        stream_manager.add_camera(camera)

if __name__ == '__main__':
    # Initialize cameras
    initialize_cameras()
    
    # Run the Flask app with SocketIO
    socketio.run(app, 
                host=APP_SETTINGS["host"], 
                port=APP_SETTINGS["port"], 
                debug=APP_SETTINGS["debug"],
                use_reloader=False)  # Disable reloader to avoid duplicate camera threads 