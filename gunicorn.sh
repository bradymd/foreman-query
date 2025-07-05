#!/bin/bash

# Production server with gunicorn
echo "Starting Gunicorn server on port 8087..."

# Check if .env file exists and source it
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if required environment variables are set
if [ -z "$FOREMAN_USERNAME" ] || [ -z "$FOREMAN_PASSWORD" ]; then
    echo "Error: FOREMAN_USERNAME and FOREMAN_PASSWORD environment variables must be set"
    echo "Either:"
    echo "  1. Copy .env.example to .env and fill in your credentials"
    echo "  2. Export the variables manually:"
    echo "     export FOREMAN_USERNAME=your_username"
    echo "     export FOREMAN_PASSWORD=your_password"
    exit 1
fi

gunicorn --bind 0.0.0.0:8087 --workers 4 --timeout 120 app:app