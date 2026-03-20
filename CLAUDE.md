# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python Flask web application that implements permission elevation using Okta's Identity Verification (IDV) feature. The application uses Okta's MyAccount API to allow users to request elevated permissions, which triggers an automatic identity verification flow managed by Okta account management policies.

## Development Setup

### Initial Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Okta credentials
```

### Running the Application
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Run Flask development server
python app.py
```

The application will be available at http://localhost:5000

### Testing Changes
After making code changes:
1. Restart the Flask server (it auto-reloads in debug mode)
2. Test the OAuth flow by logging in
3. Verify profile display from MyAccount API
4. Test the elevation button and IDV trigger

## Architecture

### OAuth2 Flow
- **Client Type**: Confidential (server-side web application)
- **Flow**: Authorization Code flow with PKCE
- **Scopes**: `openid profile email okta.myAccount.profile.read okta.myAccount.profile.manage`
- **Library**: Authlib for OAuth2 client implementation

### Key Components

**app.py**: Main Flask application containing:
- OAuth2 authorization flow (`/login`, `/callback`)
- Profile display route (`/profile`) - fetches from MyAccount API
- Elevation trigger (`POST /elevate`) - updates `elevatePermission` attribute
- Status polling endpoint (`/check-elevation`) - checks if elevation completed
- Session management using Flask sessions

**config.py**: Configuration management
- Loads from environment variables
- Constructs Okta endpoint URLs
- Validates required configuration on startup

**templates/profile.html**: Main user interface
- Displays profile attributes from MyAccount API response
- Shows "Elevate Permissions" button if not elevated
- Client-side JavaScript polls `/check-elevation` every 3 seconds after elevation request
- Auto-reloads page when elevation status changes to `true`

### Okta Integration Points

1. **Authentication**: Standard OAuth2 authorization code flow
2. **MyAccount API**:
   - `GET /idp/myaccount/profile` - Fetch user profile
   - `POST /idp/myaccount/profile` - Update profile attributes (triggers IDV)
3. **Account Management Policy**: External to app - Okta detects `elevatePermission` attribute change and triggers IDV flow
4. **Profile Attribute**: `elevatePermission` (boolean) - custom attribute that controls elevated status

### Data Flow

1. User logs in → receives access token
2. App fetches profile from MyAccount API
3. User clicks "Elevate Permissions" → app POSTs to MyAccount API setting `elevatePermission: true`
4. Okta account management policy detects change → triggers IDV flow (user may see Okta IDV screens)
5. User completes verification → Okta sets `elevatePermission: true` in profile
6. App polls status endpoint → detects change → reloads page showing elevated state

### Important Notes

- The app does not directly handle the IDV flow - that's managed entirely by Okta
- The polling mechanism (3-second interval) allows the app to detect when Okta completes the IDV flow
- Session stores access token, which is used to authorize MyAccount API calls
- The `elevatePermission` attribute must be configured as a custom boolean attribute in Okta User Profile

## Configuration Requirements

### Okta Application Setup
- Type: Web Application (confidential client)
- Grant type: Authorization Code
- Redirect URI: `http://localhost:5000/callback`
- Required scopes: Must have MyAccount scopes enabled

### Okta Profile Schema
- Custom attribute `elevatePermission` (boolean) must exist on User profile

### Okta Account Management Policy
- Must monitor `elevatePermission` attribute changes
- Must trigger IDV when attribute is set to `true`
- Must allow the attribute change upon successful verification
