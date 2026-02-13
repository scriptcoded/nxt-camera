"""
Camera Module
Handles USB camera capture and MJPEG streaming.
"""
import cv2
import threading
import time
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Camera:
    """USB camera capture with threaded frame buffering for MJPEG streaming."""
    
    def __init__(self, camera_index=0, width=640, height=480, fps=15, jpeg_quality=60):
        """
        Initialize camera capture.
        
        Args:
            camera_index: Camera device index (default: 0)
            width: Frame width in pixels (default: 640)
            height: Frame height in pixels (default: 480)
            fps: Target frames per second (default: 15)
            jpeg_quality: JPEG compression quality 0-100 (default: 60)
        """
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self.jpeg_quality = jpeg_quality
        
        self.capture: Optional[cv2.VideoCapture] = None
        self.frame: Optional[bytes] = None
        self.lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._connected = False
        
        # Connect to camera
        self.connect()
    
    def connect(self) -> bool:
        """
        Connect to USB camera.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Opening camera device {self.camera_index}...")
            self.capture = cv2.VideoCapture(self.camera_index)
            
            if not self.capture.isOpened():
                logger.error("Failed to open camera")
                return False
            
            # Set camera properties
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.capture.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Read actual properties
            actual_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.capture.get(cv2.CAP_PROP_FPS))
            
            logger.info(f"Camera opened: {actual_width}x{actual_height} @ {actual_fps}fps")
            
            self._connected = True
            self.start_capture()
            return True
            
        except Exception as e:
            logger.error(f"Camera connection error: {e}")
            self._connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if camera is connected."""
        return self._connected
    
    def start_capture(self):
        """Start background capture thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info("Camera capture thread started")
    
    def _capture_loop(self):
        """Background thread continuously capturing frames."""
        frame_delay = 1.0 / self.fps
        
        while self._running:
            if not self.capture or not self.capture.isOpened():
                logger.warning("Camera disconnected in capture loop")
                self._connected = False
                time.sleep(1)
                continue
            
            try:
                ret, frame = self.capture.read()
                
                if not ret:
                    logger.warning("Failed to read frame from camera")
                    self._connected = False
                    time.sleep(1)
                    continue
                
                # Encode frame as JPEG
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
                ret, buffer = cv2.imencode('.jpg', frame, encode_params)
                
                if ret:
                    with self.lock:
                        self.frame = buffer.tobytes()
                
                # Throttle to target FPS
                time.sleep(frame_delay)
                
            except Exception as e:
                logger.error(f"Capture error: {e}")
                time.sleep(1)
    
    def get_frame(self) -> Optional[bytes]:
        """
        Get the latest frame as JPEG bytes.
        
        Returns:
            JPEG-encoded frame or None if unavailable
        """
        with self.lock:
            return self.frame
    
    def generate_frames(self):
        """
        Generator for MJPEG streaming.
        
        Yields:
            Multipart JPEG frames for HTTP streaming
        """
        while True:
            frame = self.get_frame()
            
            if frame is None:
                # Send placeholder or wait
                time.sleep(0.1)
                continue
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    def stop(self):
        """Stop capture and release camera."""
        logger.info("Stopping camera...")
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=2)
        
        if self.capture:
            self.capture.release()
            logger.info("Camera released")
        
        self._connected = False
