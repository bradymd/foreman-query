#!/bin/bash

# Script to set up SSL certificates and logging for Foreman Query

echo "Setting up SSL certificates and logging for Foreman Query..."

# Get the current user
USER=$(whoami)
echo "Setting up for user: $USER"

# Create log directory
echo "Creating log directory..."
sudo mkdir -p /var/log/gunicorn
sudo chown $USER:$USER /var/log/gunicorn
sudo chmod 755 /var/log/gunicorn

# Check SSL certificate paths
echo "Checking SSL certificate paths..."
if [ -f "/etc/pki/tls/certs/certiffy.ca-bundle" ]; then
    echo "✓ SSL certificate found: /etc/pki/tls/certs/certiffy.ca-bundle"
else
    echo "✗ SSL certificate NOT found: /etc/pki/tls/certs/certiffy.ca-bundle"
    echo "  Please ensure the certificate file exists or update gunicorn.conf.py"
fi

if [ -f "/etc/pki/tls/private/certiffy.key" ]; then
    echo "✓ SSL private key found: /etc/pki/tls/private/certiffy.key"
else
    echo "✗ SSL private key NOT found: /etc/pki/tls/private/certiffy.key"
    echo "  Please ensure the key file exists or update gunicorn.conf.py"
fi

# Set up log rotation
echo "Setting up log rotation..."
sudo tee /etc/logrotate.d/foreman-query > /dev/null <<EOF
/var/log/gunicorn/foreman-query-*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        systemctl reload foreman-query.service > /dev/null 2>&1 || true
    endscript
}
EOF

echo "Log rotation configured for foreman-query logs"

# Test gunicorn configuration
echo "Testing gunicorn configuration..."
if ./venv/bin/gunicorn --config gunicorn.conf.py --check-config app:app; then
    echo "✓ Gunicorn configuration is valid"
else
    echo "✗ Gunicorn configuration has errors"
    exit 1
fi

echo ""
echo "Setup complete!"
echo ""
echo "To start with SSL:"
echo "  ./gunicorn.sh"
echo ""
echo "To check logs:"
echo "  tail -f /var/log/gunicorn/foreman-query-access.log"
echo "  tail -f /var/log/gunicorn/foreman-query-error.log"
echo ""
echo "Service will be available at: https://your-server:8087"