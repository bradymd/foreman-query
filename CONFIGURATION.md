# Configuration Guide

## Required Environment Variables

The Foreman Query application requires three environment variables to be configured:

### 1. FOREMAN_URL
- **Purpose**: URL of your Foreman server
- **Example**: `https://your-foreman-server.example.com`
- **Required**: Yes

### 2. FOREMAN_USERNAME  
- **Purpose**: Username for Foreman API authentication
- **Example**: `your_username`
- **Required**: Yes

### 3. FOREMAN_PASSWORD
- **Purpose**: Password for Foreman API authentication  
- **Example**: `your_password`
- **Required**: Yes

## Configuration Methods

### Method 1: .env File (Recommended)
1. Copy the example configuration:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your values:
   ```
   FOREMAN_URL=https://your-foreman-server.example.com
   FOREMAN_USERNAME=your_username
   FOREMAN_PASSWORD=your_password
   ```

### Method 2: Environment Variables
Export the variables in your shell:
```bash
export FOREMAN_URL=https://your-foreman-server.example.com
export FOREMAN_USERNAME=your_username
export FOREMAN_PASSWORD=your_password
```

### Method 3: Command Line Arguments (foreman_query.py only)
```bash
python3 foreman_query.py --url https://your-server.com --username user --password pass -a
```

## Security Notes

- The `.env` file is automatically excluded from git to protect credentials
- Never commit credentials to version control
- Use strong passwords and consider using service accounts with minimal required permissions
- The application disables SSL verification for internal Foreman servers

## Validation

The application will validate that all required configuration is present at startup and provide helpful error messages if anything is missing.

## Public Release Changes

The following hardcoded values have been removed to make this application suitable for public release:

- ✅ Removed hardcoded Foreman server URL
- ✅ Removed hardcoded usernames  
- ✅ Updated all documentation with generic examples
- ✅ Made all configuration values required environment variables
- ✅ Added proper validation and error messages
- ✅ Updated scripts to use dynamic user detection

The application is now completely configurable and ready for use in any Foreman environment.