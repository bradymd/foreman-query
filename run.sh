#!/bin/bash

# Development server
echo "Starting Flask development server on port 8087..."

# Check if .env file exists and source it
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if required environment variables are set
if [ -z "$FOREMAN_URL" ] || [ -z "$FOREMAN_USERNAME" ] || [ -z "$FOREMAN_PASSWORD" ]; then
    echo "Error: FOREMAN_URL, FOREMAN_USERNAME and FOREMAN_PASSWORD environment variables must be set"
    echo "Either:"
    echo "  1. Copy .env.example to .env and fill in your credentials"
    echo "  2. Export the variables manually:"
    echo "     export FOREMAN_URL=https://your-foreman-server.example.com"
    echo "     export FOREMAN_USERNAME=your_username"
    echo "     export FOREMAN_PASSWORD=your_password"
    exit 1
fi

export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=8088
