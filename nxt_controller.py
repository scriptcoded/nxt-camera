"""
NXT Controller Module
Manages LEGO Mindstorms NXT brick connection, motor control, and sensor reading.
"""
import threading
import time
import logging
from typing import Optional

try:
    import nxt.locator
    from nxt.motor import Motor, PORT_B, PORT_C
    from nxt.sensor import Ultrasonic, Port
except ImportError:
    print("Warning: nxt-python not installed. Install with: pip install nxt-python")
    raise

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NXTController:
    """Controls LEGO Mindstorms NXT brick with tank drive and ultrasonic sensor."""
    
    def __init__(self, motor_ports=('B', 'C'), sensor_port=4, power=75):
        """
        Initialize NXT controller.
        
        Args:
            motor_ports: Tuple of left and right motor ports (default: B, C)
            sensor_port: Port number for ultrasonic sensor (1-4, default: 4)
            power: Motor power percentage 0-100 (default: 75)
        """
        self.motor_ports = motor_ports
        self.sensor_port = sensor_port
        self.power = power
        self.brick: Optional[nxt.locator.BrickSocket] = None
        self.left_motor: Optional[Motor] = None
        self.right_motor: Optional[Motor] = None
        self.ultrasonic: Optional[Ultrasonic] = None
        self.lock = threading.Lock()
        self._connected = False
        
        # Connect to NXT
        self.connect()
    
    def connect(self) -> bool:
        """
        Connect to NXT brick via USB.
        
        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            try:
                logger.info("Searching for NXT brick...")
                self.brick = nxt.locator.find()
                logger.info(f"Connected to NXT: {self.brick.get_device_info()}")
                
                # Initialize motors
                left_port = PORT_B if self.motor_ports[0].upper() == 'B' else PORT_C
                right_port = PORT_C if self.motor_ports[1].upper() == 'C' else PORT_B
                
                self.left_motor = Motor(self.brick, left_port)
                self.right_motor = Motor(self.brick, right_port)
                
                # Initialize ultrasonic sensor
                sensor_port_map = {1: Port.S1, 2: Port.S2, 3: Port.S3, 4: Port.S4}
                self.ultrasonic = Ultrasonic(self.brick, sensor_port_map[self.sensor_port])
                
                self._connected = True
                logger.info("NXT motors and sensors initialized")
                return True
                
            except Exception as e:
                logger.error(f"Failed to connect to NXT: {e}")
                self._connected = False
                return False
    
    def is_connected(self) -> bool:
        """Check if NXT is connected."""
        return self._connected
    
    def reconnect(self) -> bool:
        """Attempt to reconnect to NXT brick."""
        logger.info("Attempting to reconnect to NXT...")
        self.disconnect()
        time.sleep(1)
        return self.connect()
    
    def disconnect(self):
        """Disconnect from NXT brick."""
        with self.lock:
            try:
                if self.brick:
                    self.stop()
                    self.brick.close()
                    logger.info("Disconnected from NXT")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
            finally:
                self._connected = False
                self.brick = None
                self.left_motor = None
                self.right_motor = None
                self.ultrasonic = None
    
    def _set_motors(self, left_power: int, right_power: int):
        """
        Set motor powers with thread safety.
        
        Args:
            left_power: Power for left motor (-100 to 100)
            right_power: Power for right motor (-100 to 100)
        """
        with self.lock:
            if not self._connected or not self.left_motor or not self.right_motor:
                logger.warning("NXT not connected, cannot set motors")
                return
            
            try:
                if left_power == 0:
                    self.left_motor.brake()
                else:
                    self.left_motor.run(power=left_power)
                
                if right_power == 0:
                    self.right_motor.brake()
                else:
                    self.right_motor.run(power=right_power)
                    
            except Exception as e:
                logger.error(f"Motor control error: {e}")
                self._connected = False
    
    def forward(self):
        """Move forward - both motors forward."""
        logger.debug("Moving forward")
        self._set_motors(self.power, self.power)
    
    def backward(self):
        """Move backward - both motors reverse."""
        logger.debug("Moving backward")
        self._set_motors(-self.power, -self.power)
    
    def left(self):
        """Turn left - right motor forward, left motor reverse."""
        logger.debug("Turning left")
        self._set_motors(-self.power, self.power)
    
    def right(self):
        """Turn right - left motor forward, right motor reverse."""
        logger.debug("Turning right")
        self._set_motors(self.power, -self.power)
    
    def stop(self):
        """Stop all motors."""
        logger.debug("Stopping")
        self._set_motors(0, 0)
    
    def get_distance(self) -> Optional[int]:
        """
        Get distance from ultrasonic sensor.
        
        Returns:
            Distance in centimeters (0-255) or None if error
        """
        with self.lock:
            if not self._connected or not self.ultrasonic:
                return None
            
            try:
                distance = self.ultrasonic.get_distance()
                return distance
            except Exception as e:
                logger.error(f"Sensor read error: {e}")
                return None
