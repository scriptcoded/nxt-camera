"""
Flask Web Application for NXT Camera Car
Streams USB camera feed and controls LEGO Mindstorms NXT via web interface.
"""
import logging
import os
import time
from datetime import datetime
from flask import Flask, render_template, Response, request, jsonify
from flask_socketio import SocketIO, emit

from camera import Camera
from nxt_controller import NXTController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'nxt-camera-secret-key-change-in-production'
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins='*')

# Initialize hardware
camera = None
nxt = None

# GPS location from OwnTracks
location = {
    'lat': None,
    'lon': None,
    'acc': None,  # accuracy in meters
    'alt': None,  # altitude
    'vel': None,  # velocity
    'batt': None, # battery percentage
    'timestamp': None
}


def init_hardware():
    """Initialize camera and NXT controller."""
    global camera, nxt
    
    logger.info("Initializing hardware...")
    
    # Initialize camera
    try:
        camera = Camera(
            camera_index=0,
            width=320,
            height=240,
            fps=10,
            jpeg_quality=50
        )
        if camera.is_connected():
            logger.info("Camera initialized successfully")
        else:
            logger.warning("Camera initialization failed")
    except Exception as e:
        logger.error(f"Camera initialization error: {e}")
        camera = None
    
    # Initialize NXT
    try:
        nxt = NXTController(
            motor_ports=('B', 'C'),
            sensor_port=4,
            power=75
        )
        if nxt.is_connected():
            logger.info("NXT initialized successfully")
        else:
            logger.warning("NXT initialization failed")
    except Exception as e:
        logger.error(f"NXT initialization error: {e}")
        nxt = None


@app.route('/')
def index():
    """Serve main web interface."""
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    """
    Video streaming route. Returns MJPEG stream.
    Headers disable Cloudflare buffering for low latency.
    """
    if camera and camera.is_connected():
        return Response(
            camera.generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame',
            headers={
                'X-Accel-Buffering': 'no',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
    else:
        return "Camera not available", 503


@app.route('/api/location', methods=['POST'])
def receive_location():
    """Receive location updates from OwnTracks."""
    global location
    
    data = request.get_json()
    
    # OwnTracks sends _type: "location" for position updates
    if data and data.get('_type') == 'location':
        location = {
            'lat': data.get('lat'),
            'lon': data.get('lon'),
            'acc': data.get('acc'),
            'alt': data.get('alt'),
            'vel': data.get('vel'),
            'batt': data.get('batt'),
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"Location updated: {location['lat']}, {location['lon']} (±{location['acc']}m)")
        
        # Broadcast to all connected clients
        socketio.emit('location', location)
        
        return jsonify({'status': 'ok'})
    
    return jsonify({'status': 'ignored'}), 200


@app.route('/api/location', methods=['GET'])
def get_location():
    """Get current location."""
    return jsonify(location)


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected")
    
    # Send connection status
    emit('status', {
        'camera': camera.is_connected() if camera else False,
        'nxt': nxt.is_connected() if nxt else False
    })
    
    # Send current location if available
    if location['lat'] is not None:
        emit('location', location)


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info("Client disconnected")
    
    # Stop motors when client disconnects
    if nxt and nxt.is_connected():
        nxt.stop()


@socketio.on('move')
def handle_move(data):
    """
    Handle movement command from client.
    
    Args:
        data: Dictionary with 'direction' key (forward/backward/left/right)
    """
    if not nxt or not nxt.is_connected():
        emit('error', {'message': 'NXT not connected'})
        return
    
    direction = data.get('direction', '')
    logger.debug(f"Move command: {direction}")
    
    try:
        if direction == 'forward':
            nxt.forward()
        elif direction == 'backward':
            nxt.backward()
        elif direction == 'left':
            nxt.left()
        elif direction == 'right':
            nxt.right()
        else:
            logger.warning(f"Unknown direction: {direction}")
    except Exception as e:
        logger.error(f"Movement error: {e}")
        emit('error', {'message': str(e)})


@socketio.on('stop')
def handle_stop():
    """Handle stop command from client."""
    if nxt and nxt.is_connected():
        logger.debug("Stop command")
        try:
            nxt.stop()
        except Exception as e:
            logger.error(f"Stop error: {e}")
            emit('error', {'message': str(e)})


def distance_monitor():
    """Background task to monitor ultrasonic sensor and emit distance updates."""
    while True:
        try:
            if nxt and nxt.is_connected():
                distance = nxt.get_distance()
                if distance is not None:
                    socketio.emit('distance', {'value': distance})
            
            time.sleep(0.5)  # Poll every 500ms
            
        except Exception as e:
            logger.error(f"Distance monitor error: {e}")
            time.sleep(1)


def cleanup():
    """Clean up hardware resources."""
    logger.info("Cleaning up...")
    
    if nxt:
        nxt.disconnect()
    
    if camera:
        camera.stop()


if __name__ == '__main__':
    try:
        # Get port from environment variable or default to 5000
        port = int(os.getenv('PORT', 5000))
        
        # Initialize hardware
        init_hardware()
        
        # Start distance monitoring in background
        socketio.start_background_task(distance_monitor)
        
        # Run Flask app
        logger.info(f"Starting Flask server on 0.0.0.0:{port}")
        socketio.run(app, host='0.0.0.0', port=port, debug=False)
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        cleanup()
