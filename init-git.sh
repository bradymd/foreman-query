#!/bin/bash

# Initialize git repository safely

echo "Initializing git repository for Foreman Query application..."

# Check if already a git repo
if [ -d ".git" ]; then
    echo "Already a git repository!"
    exit 1
fi

# Make sure .env file exists and warn about credentials
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Make sure to create it with your credentials."
    echo "Run: cp .env.example .env"
fi

# Initialize git
git init

# Add all files except credentials
git add .

# Initial commit
git commit -m "Initial commit - Foreman Host Query application

- Flask web application for querying Foreman hosts
- Command-line tool with JSON/CSV output  
- Smart OS and kernel version sorting
- Environment variable configuration
- Systemd service support
- Bootstrap web interface with search and filtering

🤖 Generated with Claude Code"

echo ""
echo "Git repository initialized successfully!"
echo ""
echo "IMPORTANT: Your credentials are safely excluded from git."
echo "Make sure your .env file contains:"
echo "  FOREMAN_USERNAME=your_username"
echo "  FOREMAN_PASSWORD=your_password"
echo ""
echo "Next steps:"
echo "  git remote add origin <your-repo-url>"
echo "  git push -u origin main"