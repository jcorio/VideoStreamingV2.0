# VideoStreamingV2.0

A production-ready Python web application for real-time streaming and object detection from 13 Dahua RTSP cameras using Flask and OpenCV.

## Features
- Streams 13 Dahua RTSP camera feeds live in the browser
- Real-time object detection using YOLOv5/YOLOv8
- Bounding boxes and labels overlay on video
- Snapshot button for saving current frames
- Automatic reconnection on stream drop
- Multithreaded/asynchronous for smooth streaming
- Modular, clean, and well-commented code

## Setup (Windows)
1. Clone this repository:
   ```sh
   git clone <your-repo-url>
   cd VideoStreamingV2.0
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Run the application:
   ```sh
   python app.py
   ```
4. Open your browser and go to `http://localhost:5000`

## Requirements
- Python 3.8+
- OpenCV
- Flask
- YOLOv5/YOLOv8 model weights

## Notes
- Designed for Windows 10/11
- No logging or CSV event recording included
- For RTSP camera credentials and URLs, see the application configuration 