#!/bin/bash
# Setup udev rules for LEGO Mindstorms NXT USB access
# This allows non-root users to communicate with the NXT brick

set -e

echo "========================================="
echo "  NXT USB Access Setup"
echo "========================================="
echo

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "❌ This script must be run with sudo"
    echo "Usage: sudo bash setup_udev.sh"
    exit 1
fi

# Get the actual user (not root when using sudo)
ACTUAL_USER="${SUDO_USER:-$USER}"

echo "Setting up udev rules for user: $ACTUAL_USER"
echo

# Create udev rules file
RULES_FILE="/etc/udev/rules.d/99-lego-nxt.rules"

echo "Creating udev rules file: $RULES_FILE"
cat > "$RULES_FILE" << 'EOF'
# LEGO Mindstorms NXT
# Allow non-root users to access NXT via USB
SUBSYSTEM=="usb", ATTR{idVendor}=="0694", MODE="0666", GROUP="plugdev"
EOF

echo "✓ udev rules file created"
echo

# Reload udev rules
echo "Reloading udev rules..."
udevadm control --reload-rules
udevadm trigger
echo "✓ udev rules reloaded"
echo

# Add user to plugdev group
echo "Adding user $ACTUAL_USER to 'plugdev' group..."
if ! groups "$ACTUAL_USER" | grep -q "\bplugdev\b"; then
    usermod -a -G plugdev "$ACTUAL_USER"
    echo "✓ User added to plugdev group"
    echo
    echo "⚠️  You need to log out and log back in for group changes to take effect"
else
    echo "✓ User already in plugdev group"
fi

echo
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo
echo "Next steps:"
echo "1. If you were added to the plugdev group, log out and log back in"
echo "2. Disconnect and reconnect your NXT brick"
echo "3. Run 'lsusb' to verify the NXT is detected"
echo "4. Look for: 'Bus XXX Device XXX: ID 0694:xxxx LEGO Group'"
echo
echo "You should now be able to run the application without permission errors!"
echo
