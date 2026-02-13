#!/bin/bash
# Setup Cloudflare Tunnel for secure internet access
# Provides HTTPS access without port forwarding or static IP

set -e

echo "========================================="
echo "  Cloudflare Tunnel Setup"
echo "========================================="
echo

# Check if cloudflared is installed
if command -v cloudflared &> /dev/null; then
    echo "✓ cloudflared is already installed"
    CLOUDFLARED_VERSION=$(cloudflared --version | head -n 1)
    echo "  Version: $CLOUDFLARED_VERSION"
else
    echo "Installing cloudflared..."
    
    # Detect architecture
    ARCH=$(uname -m)
    if [ "$ARCH" = "armv7l" ] || [ "$ARCH" = "armv6l" ]; then
        # Raspberry Pi 3 and older
        DOWNLOAD_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm"
    elif [ "$ARCH" = "aarch64" ]; then
        # Raspberry Pi 4/5 with 64-bit OS
        DOWNLOAD_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
    elif [ "$ARCH" = "x86_64" ]; then
        # x86_64 (for testing on PC)
        DOWNLOAD_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    else
        echo "❌ Unsupported architecture: $ARCH"
        exit 1
    fi
    
    echo "  Architecture: $ARCH"
    echo "  Downloading from: $DOWNLOAD_URL"
    
    wget -O cloudflared "$DOWNLOAD_URL"
    chmod +x cloudflared
    sudo mv cloudflared /usr/local/bin/
    
    echo "✓ cloudflared installed to /usr/local/bin/cloudflared"
fi

echo
echo "========================================="
echo "  Authentication Required"
echo "========================================="
echo
echo "You need to authenticate with your Cloudflare account."
echo "This will open a browser window for you to log in."
echo
echo "Prerequisites:"
echo "  - A Cloudflare account (free tier works fine)"
echo "  - A domain added to Cloudflare"
echo
read -p "Press Enter to continue with authentication..."

cloudflared tunnel login

echo
echo "✓ Authentication successful!"
echo

# Get tunnel name
echo "========================================="
echo "  Creating Tunnel"
echo "========================================="
echo
read -p "Enter a name for your tunnel (e.g., nxt-camera): " TUNNEL_NAME

if [ -z "$TUNNEL_NAME" ]; then
    TUNNEL_NAME="nxt-camera"
    echo "Using default name: $TUNNEL_NAME"
fi

# Create tunnel
cloudflared tunnel create "$TUNNEL_NAME"

echo
echo "✓ Tunnel created: $TUNNEL_NAME"
echo

# Get tunnel ID
TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
echo "Tunnel ID: $TUNNEL_ID"

# Prompt for domain
echo
echo "========================================="
echo "  DNS Configuration"
echo "========================================="
echo
echo "Enter the hostname you want to use for your tunnel."
echo "Example: nxt-camera.yourdomain.com"
echo "         (where yourdomain.com is in your Cloudflare account)"
echo
read -p "Hostname: " HOSTNAME

if [ -z "$HOSTNAME" ]; then
    echo "❌ Hostname is required"
    exit 1
fi

# Create DNS record
cloudflared tunnel route dns "$TUNNEL_NAME" "$HOSTNAME"

echo
echo "✓ DNS record created: $HOSTNAME"
echo

# Create config directory
CONFIG_DIR="$HOME/.cloudflared"
mkdir -p "$CONFIG_DIR"

# Create config file
CONFIG_FILE="$CONFIG_DIR/config.yml"
cat > "$CONFIG_FILE" << EOF
tunnel: $TUNNEL_ID
credentials-file: $CONFIG_DIR/$TUNNEL_ID.json

ingress:
  - hostname: $HOSTNAME
    service: http://localhost:5000
  - service: http_status:404
EOF

echo "✓ Configuration file created: $CONFIG_FILE"
echo

# Install as systemd service
echo "========================================="
echo "  Installing Service"
echo "========================================="
echo
read -p "Install cloudflared as a systemd service (auto-start on boot)? (y/n): " INSTALL_SERVICE

if [ "$INSTALL_SERVICE" = "y" ] || [ "$INSTALL_SERVICE" = "Y" ]; then
    sudo cloudflared service install
    echo "✓ Service installed"
    echo
    echo "Starting service..."
    sudo systemctl start cloudflared
    sudo systemctl enable cloudflared
    echo "✓ Service started and enabled"
fi

echo
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo
echo "Your tunnel is configured:"
echo "  Name:     $TUNNEL_NAME"
echo "  ID:       $TUNNEL_ID"
echo "  Hostname: https://$HOSTNAME"
echo "  Local:    http://localhost:5000"
echo
if [ "$INSTALL_SERVICE" = "y" ] || [ "$INSTALL_SERVICE" = "Y" ]; then
    echo "The tunnel service is running and will start automatically on boot."
    echo
    echo "Service commands:"
    echo "  sudo systemctl status cloudflared   # Check status"
    echo "  sudo systemctl stop cloudflared     # Stop service"
    echo "  sudo systemctl start cloudflared    # Start service"
    echo "  sudo systemctl restart cloudflared  # Restart service"
else
    echo "To start the tunnel manually:"
    echo "  cloudflared tunnel run $TUNNEL_NAME"
fi
echo
echo "Access your NXT Camera Car at: https://$HOSTNAME"
echo
echo "Next: Configure Cloudflare Access for authentication"
echo "  1. Go to https://one.dash.cloudflare.com/"
echo "  2. Navigate to: Zero Trust → Access → Applications"
echo "  3. Add Application → Self-hosted"
echo "  4. Application domain: $HOSTNAME"
echo "  5. Create a policy (e.g., allow specific emails)"
echo
