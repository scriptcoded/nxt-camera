# OwnTracks Setup Guide

This guide will help you set up OwnTracks on your iPhone to send location data to your NXT Camera Car.

## What is OwnTracks?

OwnTracks is a free, open-source app that allows you to track your location and send it to your own server (your Raspberry Pi in this case). This way, you can see where your robot is on a map in real-time.

## Prerequisites

- iPhone with OwnTracks app installed
- iPhone serving as Wi-Fi hotspot for the Raspberry Pi
- Raspberry Pi connected to the iPhone's hotspot
- NXT Camera Car application running on the Pi

## Installation

### 1. Install OwnTracks on iPhone

1. Open the **App Store** on your iPhone
2. Search for **"OwnTracks"**
3. Install the app (it's free)

### 2. Configure OwnTracks

1. Open the **OwnTracks** app
2. Tap the **☰** menu (top left)
3. Go to **Settings**

#### Connection Settings

1. In Settings, tap **Connection**
2. Set **Mode** to: **HTTP**
3. Set **URL** to: `http://<raspberry-pi-ip>:5000/api/location`
   - To find your Raspberry Pi's IP on the hotspot network:
     - On the Pi, run: `hostname -I`
     - Or on iPhone: Settings → Personal Hotspot → view connected devices
   - Example: `http://192.168.2.2:5000/api/location`
4. Leave **Authentication** off (optional: you can add basic auth later)
5. Tap **Save**

#### Location Permissions

1. Go to iPhone **Settings** → **Privacy & Security** → **Location Services**
2. Find **OwnTracks** in the list
3. Set to **Always** (required for background tracking)
4. Enable **Precise Location**

#### Reporting Settings (Optional)

Back in OwnTracks Settings:

1. Tap **Reporting**
2. Adjust settings as desired:
   - **Move**: Distance in meters before sending update (default: 100m)
   - **Interval**: Time in seconds between updates (default: 0 = disabled)
   - Recommendation: Set **Move** to `50` for more frequent updates

### 3. Test the Connection

1. Make sure your Raspberry Pi is running the NXT Camera Car app:
   ```bash
   python app.py
   ```

2. In OwnTracks, tap the **☰** menu → **Status**
   - Should show "HTTP" in green
   - If red, check your URL and network connection

3. Open the web interface on another device: `http://<pi-ip>:5000`

4. Walk around with your iPhone - you should see:
   - **GPS indicator turns green** in the status bar at the top
   - A map appear on the website
   - A robot emoji (🤖) marking your location
   - Coordinates and accuracy displayed below the map
   - Battery percentage of your iPhone

**Note**: The GPS indicator will turn red if no location updates are received for 2 minutes.

## Troubleshooting

### Location Not Showing

**Check GPS Status Indicator:**
- Look at the status bar at the top of the web interface
- If GPS indicator is **red**: No location data received yet or timeout
- If GPS indicator is **green**: Location updates are being received

**Check OwnTracks Status:**
- Open OwnTracks → ☰ menu → **Status**
- Look for "HTTP" connection status (should be green)
- Check "Last publish" timestamp

**Verify URL:**
- Make sure the URL in OwnTracks matches your Pi's IP
- Include `/api/location` at the end
- Use `http://` not `https://`

**Check Network:**
- Ensure iPhone and Pi are on the same network (hotspot)
- Try pinging the Pi from another device: `ping <pi-ip>`

**Check Pi Logs:**
```bash
# You should see "Location updated" messages
python app.py
# Look for: INFO - Location updated: <lat>, <lon>
```

**Force Location Update:**
- In OwnTracks, tap ☰ menu → **Publish location now**

### "HTTP 503" or Connection Errors

- Restart the Flask app on the Pi
- Check firewall isn't blocking port 5000
- Verify the Pi's IP address hasn't changed

### Battery Drain

OwnTracks uses GPS which can drain battery. To optimize:

1. In OwnTracks Settings → **Reporting**:
   - Increase **Move** distance (e.g., 200 meters)
   - Don't use time-based **Interval** updates
   
2. iOS Settings → OwnTracks → **Low Power Mode** compatibility:
   - Background tracking may pause in Low Power Mode

### Map Not Loading on Website

- Check browser console for JavaScript errors
- Ensure you have internet connection (for map tiles)
- Try refreshing the page

## Advanced Configuration

### Using Over Internet (Cloudflare Tunnel)

If you've set up Cloudflare Tunnel:

1. In OwnTracks, change URL to your public domain:
   ```
   https://nxt-camera.yourdomain.com/api/location
   ```

2. Make sure Cloudflare Access allows the OwnTracks HTTP POST requests
   - Option 1: Disable Access for `/api/location` path
   - Option 2: Use HTTP authentication in OwnTracks settings

### Security: Adding Authentication

Edit `app.py` to add basic authentication:

```python
from functools import wraps
from flask import request, jsonify

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if auth != 'Bearer YOUR_SECRET_TOKEN':
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/location', methods=['POST'])
@require_auth
def receive_location():
    # ... existing code
```

Then in OwnTracks Settings → Connection:
- Set **Authorization**: `Bearer YOUR_SECRET_TOKEN`

## OwnTracks Features

### Regions (Geofencing)

You can set up regions in OwnTracks to trigger events when entering/leaving areas:
1. OwnTracks → ☰ → **Regions**
2. Tap **+** to add a region
3. Set center point and radius
4. The app will send enter/exit events

### History

OwnTracks keeps a local history of your locations:
- Tap ☰ → **Timeline** to view

### Friends (Multiple Devices)

You can track multiple devices with OwnTracks Server:
- Requires setting up an OwnTracks Recorder (more complex)
- Not covered in this guide

## Privacy Note

All location data is sent directly to YOUR Raspberry Pi. No third-party services are involved. Location data is only stored in memory on the Pi and is lost when the app restarts (unless you add database storage).

## Resources

- [OwnTracks Official Documentation](https://owntracks.org/booklet/)
- [OwnTracks iOS App](https://apps.apple.com/app/owntracks/id692424691)
- [OwnTracks JSON Format](https://owntracks.org/booklet/tech/json/)

---

Happy tracking! 🤖📍
