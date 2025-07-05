#!/bin/bash

# Script to install the Foreman Query systemd service

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root (use sudo)"
    exit 1
fi

# Get the current directory
SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SERVICE_DIR/foreman-query.service"

echo "Installing Foreman Query systemd service..."

# Copy service file to systemd directory
cp "$SERVICE_FILE" /etc/systemd/system/

# Set proper permissions
chmod 644 /etc/systemd/system/foreman-query.service

# Reload systemd daemon
systemctl daemon-reload

# Enable the service
systemctl enable foreman-query.service

echo "Service installed successfully!"
echo ""
echo "To start the service:"
echo "  sudo systemctl start foreman-query"
echo ""
echo "To check status:"
echo "  sudo systemctl status foreman-query"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u foreman-query -f"
echo ""
echo "To stop the service:"
echo "  sudo systemctl stop foreman-query"
