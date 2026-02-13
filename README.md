# 🤖 NXT Camera Car

A web-based remote control system for a LEGO Mindstorms NXT robot car with live camera feed. Control your robot from anywhere in the world using a Raspberry Pi, USB camera, and Cloudflare Tunnels.

## ✨ Features

- **Live Camera Streaming**: Real-time MJPEG video feed from USB camera
- **Responsive Controls**: Keyboard (WASD/arrows) and on-screen buttons
- **Tank Drive Control**: Differential steering with two motors
- **Distance Sensing**: Real-time ultrasonic sensor readings
- **Low Latency**: WebSocket-based communication for responsive control
- **Secure Remote Access**: Cloudflare Tunnels with Zero Trust authentication
- **Mobile Friendly**: Touch-optimized controls for phones and tablets

## 🛠️ Hardware Requirements

### Required
- **Raspberry Pi** (tested on Pi 3, works on Pi 4/5)
- **LEGO Mindstorms NXT brick**
- **USB Camera** (any UVC-compatible webcam)
- **2x NXT Motors** for tank drive (connected to ports B and C)
- **Ultrasonic Sensor** (connected to port 4)
- **2x USB cables** (one for NXT, one for camera)
- **Power supply** for Raspberry Pi

### Recommended
- SD card with at least 8GB (16GB+ recommended)
- WiFi connection for Raspberry Pi
- Properly constructed LEGO car chassis

## 📋 Software Requirements

- Raspberry Pi OS (Bullseye or newer)
- Python 3.8+
- Internet connection (for Cloudflare Tunnels)

## 🚀 Installation

### 1. Clone or Download Project

```bash
cd ~
git clone <your-repo-url> nxt-camera
cd nxt-camera
```

Or if you downloaded manually:
```bash
cd ~/nxt-camera
```

### 2. Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv libusb-1.0-0-dev libudev-dev
```

### 3. Create Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Setup NXT USB Access

The NXT brick requires udev rules for non-root USB access:

```bash
sudo bash setup_udev.sh
```

**Important**: After running this script, you may need to:
1. Log out and log back in (if you were added to plugdev group)
2. Disconnect and reconnect your NXT brick

Verify NXT detection:
```bash
lsusb | grep LEGO
# Should show: Bus XXX Device XXX: ID 0694:xxxx LEGO Group
```

## 🎮 Running Locally

### Connect Hardware
1. Connect USB camera to Raspberry Pi
2. Connect NXT brick to Raspberry Pi via USB
3. Ensure NXT is powered on

### Start Application

```bash
source venv/bin/activate
python app.py
```

The server will start on `http://0.0.0.0:5000`

### Access Web Interface

From another device on the same network:
```
http://<raspberry-pi-ip>:5000
```

Find your Pi's IP address:
```bash
hostname -I
```

## 🌐 Internet Access with Cloudflare Tunnels

### Prerequisites

1. **Cloudflare Account**: Sign up at [cloudflare.com](https://cloudflare.com) (free tier works)
2. **Domain**: Add your domain to Cloudflare (can transfer or use Cloudflare as DNS)

### Setup Tunnel

Run the automated setup script:

```bash
bash setup_tunnel.sh
```

This script will:
1. Download and install `cloudflared` for your architecture
2. Authenticate with your Cloudflare account (opens browser)
3. Create a new tunnel
4. Configure DNS routing
5. Optionally install as a systemd service (auto-start on boot)

### Manual Tunnel Start

If you didn't install as a service:

```bash
cloudflared tunnel run nxt-camera
```

### Configure Cloudflare Access (Authentication)

To protect your robot from unauthorized access:

1. Go to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. Navigate to: **Zero Trust** → **Access** → **Applications**
3. Click **Add an application** → **Self-hosted**
4. Configure:
   - **Application name**: NXT Camera Car
   - **Application domain**: `nxt-camera.yourdomain.com` (or your chosen hostname)
5. Create a policy:
   - **Policy name**: Allow My Email
   - **Action**: Allow
   - **Include**: `Emails` → `your-email@example.com`
   - Or use: **Login with Google**, **GitHub**, etc.
6. Save

Now when anyone accesses your tunnel URL, they'll need to authenticate first!

## 🎯 Usage

### Keyboard Controls

| Key | Action |
|-----|--------|
| `W` or `↑` | Forward |
| `S` or `↓` | Backward |
| `A` or `←` | Turn Left |
| `D` or `→` | Turn Right |
| Release key | Stop |

### On-Screen Controls

- **Tap/Click and Hold** direction buttons to move
- **Release** to stop
- **Stop button** for emergency stop

### Distance Display

The ultrasonic sensor reading appears in the top-right corner of the video feed, showing distance to obstacles in centimeters.

## 🔧 Configuration

### Motor Configuration

Edit `app.py` to change motor ports or power:

```python
nxt = NXTController(
    motor_ports=('B', 'C'),  # Left, Right motor ports
    sensor_port=4,            # Ultrasonic sensor port
    power=75                  # Motor power (0-100)
)
```

### Camera Settings

Edit `app.py` to adjust camera parameters:

```python
camera = Camera(
    camera_index=0,    # Camera device (0 = first camera)
    width=640,         # Resolution width
    height=480,        # Resolution height
    fps=15,            # Frames per second
    jpeg_quality=60    # JPEG compression (0-100)
)
```

**Performance Tips for Raspberry Pi 3**:
- Lower resolution (e.g., 320x240) for faster performance
- Reduce FPS to 10-12 if CPU usage is high
- Lower JPEG quality to 50 for reduced bandwidth

## 🐛 Troubleshooting

### NXT Connection Issues

**Problem**: `Failed to connect to NXT`

**Solutions**:
- Check USB cable connection
- Ensure NXT brick is powered on
- Verify udev rules: `ls -l /dev/bus/usb/*/` should show NXT device with group `plugdev`
- Check user is in plugdev group: `groups`
- Try reconnecting NXT or rebooting Pi

### Camera Not Working

**Problem**: Black screen or "Camera not available"

**Solutions**:
- Check USB camera is connected: `ls /dev/video*`
- Test with: `v4l2-ctl --list-devices`
- Try different camera_index (0, 1, 2, etc.)
- Some cameras may need additional drivers

### High CPU Usage

**Solutions**:
- Reduce camera resolution in `app.py`
- Lower FPS to 10-12
- Decrease JPEG quality
- Close other applications on Pi
- Consider upgrading to Pi 4 or 5

### Cloudflare Tunnel Issues

**Problem**: Tunnel not connecting

**Solutions**:
- Check tunnel status: `sudo systemctl status cloudflared`
- View logs: `sudo journalctl -u cloudflared -f`
- Restart service: `sudo systemctl restart cloudflared`
- Verify credentials file exists: `ls ~/.cloudflared/`

**Problem**: High latency over internet

**Expected behavior**: 200-500ms additional latency is normal over internet
- Video quality can be reduced for lower latency
- Controls should remain responsive via WebSockets

### Permission Errors

**Problem**: `Permission denied` errors

**Solutions**:
- Don't run with `sudo` — use udev rules instead
- Verify group membership: `groups`
- Log out and back in after running `setup_udev.sh`

## 📁 Project Structure

```
nxt-camera/
├── app.py                    # Main Flask application
├── nxt_controller.py         # NXT motor and sensor control
├── camera.py                 # USB camera capture
├── requirements.txt          # Python dependencies
├── setup_udev.sh            # NXT USB access setup
├── setup_tunnel.sh          # Cloudflare Tunnel setup
├── cloudflared-config.yml   # Cloudflare config template
├── templates/
│   └── index.html           # Web interface
├── static/
│   ├── style.css            # CSS styling
│   └── controls.js          # Client-side JavaScript
└── README.md                # This file
```

## 🔒 Security Considerations

### Local Network
- Default configuration has no authentication
- Only run on trusted networks
- Consider adding password protection for local use

### Internet (Cloudflare Tunnels)
- **Always configure Cloudflare Access** for public tunnels
- Use email allowlists or identity providers (Google, GitHub)
- Consider IP restrictions for additional security
- Monitor access logs in Cloudflare dashboard

### Production Hardening
- Change Flask SECRET_KEY in `app.py`
- Use environment variables for sensitive config
- Implement rate limiting for controls
- Add session timeouts

## 🚦 System Requirements

### Raspberry Pi 3
- 1GB RAM sufficient
- 15fps @ 640×480 recommended
- May need to close other apps

### Raspberry Pi 4/5
- Can handle 30fps @ 720p
- More headroom for additional features

## 📝 License

This project is open source. Feel free to modify and distribute.

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Support for additional sensors (touch, light, sound)
- Recording/playback functionality
- Autonomous driving modes
- Multiple camera support
- Mobile app development

## 📚 Resources

- [LEGO Mindstorms NXT](https://www.lego.com/en-us/themes/mindstorms/about)
- [nxt-python Documentation](https://github.com/schodet/nxt-python)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Cloudflare Tunnels](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Cloudflare Access](https://developers.cloudflare.com/cloudflare-one/policies/access/)

## 💡 Tips

1. **Test locally first** before setting up Cloudflare Tunnels
2. **Adjust motor power** based on your robot's weight and terrain
3. **Camera angle matters** - mount camera at driver's eye level
4. **Battery life** - NXT uses AA batteries, keep spares handy
5. **Add LEDs** or sound to indicate connection status on robot
6. **Consider a killswitch** for emergency stops

## 🎓 Educational Use

This project is great for learning:
- Web development (Flask, HTML, CSS, JavaScript)
- WebSocket communication
- Video streaming techniques
- Robotics and motor control
- Linux system administration
- Networking and tunneling

Perfect for classrooms, coding clubs, or personal learning!

---

Built with ❤️ for LEGO Mindstorms enthusiasts

Happy building! 🤖📹🎮
