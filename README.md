# Okta Permission Elevation with Identity Verification

A Python Flask application that demonstrates permission elevation using Okta's Identity Verification (IDV) feature. Users can request elevated permissions, which triggers an identity verification flow managed by Okta's account management policies.

## Features

- **Okta OAuth2 Authentication**: Secure login using Okta's authorization code flow with confidential client
- **MyAccount API Integration**: Display and manage user profile attributes
- **Permission Elevation**: Request elevated permissions with a button click
- **Identity Verification**: Automatic IDV flow triggered by Okta account management policy
- **Real-time Status Updates**: Automatic polling to detect when elevation is complete

## Architecture

This application acts as a confidential OAuth2 client:

1. User authenticates via Okta OAuth2 authorization code flow
2. App receives access token with `okta.myAccount.profile.read` and `okta.myAccount.profile.manage` scopes
3. User profile is fetched from Okta MyAccount API (`/idp/myaccount/profile`)
4. When user clicks "Elevate Permissions", the app updates the `elevatePermission` attribute to `true`
5. An Okta account management policy detects this change and triggers IDV flow
6. User completes identity verification (if required by policy)
7. Upon successful verification, Okta sets the `elevatePermission` attribute to `true`
8. App polls for status changes and displays success message

## Prerequisites

- Python 3.8+
- An Okta account with admin access
- An Okta application configured as a confidential client

## Okta Configuration

### 1. Create a Confidential Application

1. Log into your Okta admin console
2. Go to **Applications** > **Applications**
3. Click **Create App Integration**
4. Select **OIDC - OpenID Connect**
5. Choose **Web Application**
6. Configure:
   - **App integration name**: Permission Elevation Demo
   - **Grant type**: Authorization Code
   - **Sign-in redirect URIs**: `http://localhost:5000/callback`
   - **Sign-out redirect URIs**: `http://localhost:5000`
   - **Controlled access**: Choose as appropriate
7. Save and note the **Client ID** and **Client Secret**

### 2. Configure Scopes

Ensure your application has access to these scopes:
- `openid`
- `profile`
- `email`
- `okta.myAccount.profile.read`
- `okta.myAccount.profile.manage`

### 3. Create Custom Profile Attribute

1. Go to **Directory** > **Profile Editor**
2. Select the **User (default)** profile
3. Click **Add Attribute**
4. Configure:
   - **Data type**: Boolean
   - **Display name**: Elevate Permission
   - **Variable name**: `elevatePermission`
   - **Description**: Indicates if user has elevated permissions
5. Save

### 4. Create Account Management Policy

1. Go to **Security** > **Identity Verification**
2. Set up an identity verification flow (if not already configured)
3. Go to **Security** > **Account Management**
4. Create or edit a policy rule that:
   - Triggers on profile attribute change
   - Monitors the `elevatePermission` attribute
   - Requires identity verification when set to `true`
   - Allows the change if verification succeeds

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd okta_elevate_permissions_with_idv
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` with your Okta configuration:
```
OKTA_DOMAIN=your-domain.okta.com
OKTA_CLIENT_ID=your-client-id
OKTA_CLIENT_SECRET=your-client-secret
REDIRECT_URI=http://localhost:5000/callback
SECRET_KEY=your-random-secret-key
```

## Running the Application

1. Activate your virtual environment:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Run the Flask application:
```bash
python app.py
```

3. Open your browser to http://localhost:5000

## Usage

1. Click **Login with Okta**
2. Authenticate with your Okta credentials
3. View your profile attributes on the profile page
4. Click **Elevate Permissions** to request elevation
5. Complete identity verification if prompted by Okta
6. The page will automatically update when elevation is successful

## Development

### Project Structure

```
.
├── app.py                  # Main Flask application
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment variables
├── templates/            # HTML templates
│   ├── base.html        # Base template
│   ├── index.html       # Landing page
│   └── profile.html     # Profile/elevation page
└── static/              # Static assets
    └── css/
        └── style.css    # Application styles
```

### API Endpoints

- `GET /` - Landing page
- `GET /login` - Initiate OAuth2 flow
- `GET /callback` - OAuth2 callback handler
- `GET /profile` - Display user profile (requires authentication)
- `POST /elevate` - Request permission elevation (requires authentication)
- `GET /check-elevation` - Check current elevation status (requires authentication)
- `GET /logout` - Logout and clear session

## Security Considerations

- Never commit `.env` file or expose client secrets
- Use HTTPS in production
- Set a strong `SECRET_KEY` for session management
- Configure appropriate CORS policies
- Implement rate limiting for production use
- Review and test Okta account management policies thoroughly

## Troubleshooting

### "Missing required configuration" error
- Ensure all variables in `.env` are set correctly
- Verify `OKTA_DOMAIN` does not include `https://`

### "Elevation request submitted but no IDV flow"
- Check that your account management policy is active
- Verify the policy monitors the `elevatePermission` attribute
- Ensure identity verification is configured in your Okta org

### "Failed to load profile" error
- Verify your access token has the required scopes
- Check that MyAccount API is enabled in your Okta org
- Ensure the user profile has the custom attribute configured

## License

MIT
