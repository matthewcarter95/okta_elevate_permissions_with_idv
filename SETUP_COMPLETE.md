# Setup Complete! 🎉

Your application is ready to configure and run.

## What's Been Done

✅ Copied your Prisma certificate from `~/software/prisma_certificates.pem`
✅ Created virtual environment with Python 3.11.6
✅ Installed all dependencies (Flask, requests, authlib, etc.)
✅ Configured certificate for SSL/TLS connections
✅ Created helper script to run the application

## Next Steps

### 1. Configure Your Okta Application

Edit the `.env` file and replace these values:

```bash
OKTA_DOMAIN=your-domain.okta.com          # e.g., dev-12345.okta.com
OKTA_CLIENT_ID=your-client-id              # From your Okta app
OKTA_CLIENT_SECRET=your-client-secret      # From your Okta app
SECRET_KEY=generate-a-random-key-here      # Use: python -c "import secrets; print(secrets.token_hex(32))"
```

**Note:** The certificate path is already configured: `SSL_CERT_PATH=./corporate-ca.pem`

### 2. Set Up Your Okta Organization

Before running the app, configure these in Okta:

#### A. Create the Custom Profile Attribute
1. Go to **Directory** > **Profile Editor**
2. Select **User (default)** profile
3. Click **Add Attribute**
   - Data type: `Boolean`
   - Display name: `Elevate Permission`
   - Variable name: `elevatePermission`
   - Default value: `false`
4. Save

#### B. Configure Application Scopes
Ensure your Okta application has these scopes:
- `openid`
- `profile`
- `email`
- `okta.myAccount.profile.read`
- `okta.myAccount.profile.manage`

#### C. Create Account Management Policy (for IDV)
1. Go to **Security** > **Identity Verification**
2. Set up an IDV flow (if not already configured)
3. Go to **Security** > **Account Management**
4. Create or edit a policy rule:
   - Trigger: Profile attribute change (`elevatePermission`)
   - Action: Require identity verification
   - On success: Allow the change

### 3. Run the Application

Use the helper script:
```bash
./run.sh
```

Or manually:
```bash
source venv/bin/activate
export REQUESTS_CA_BUNDLE=./corporate-ca.pem
python app.py
```

Then visit: http://localhost:5000

### 4. Test the Flow

1. Click "Login with Okta"
2. Authenticate with your Okta credentials
3. View your profile attributes
4. Click "Elevate Permissions"
5. Complete identity verification (if prompted)
6. Page will automatically refresh showing elevated status

## Troubleshooting

### If you get SSL errors when running:
The certificate is already configured in `.env`, but make sure to set the environment variable:
```bash
export REQUESTS_CA_BUNDLE=./corporate-ca.pem
```

### If pip needs packages in the future:
Use this command to bypass the truststore requirement:
```bash
source venv/bin/activate
PIP_CONFIG_FILE=/dev/null pip install package-name
```

### To test your Okta connection:
```bash
source venv/bin/activate
python -c "from config import Config; Config.validate(); print(f'Okta domain: {Config.OKTA_DOMAIN}')"
```

## Files Created

- `corporate-ca.pem` - Your Prisma certificate
- `venv/` - Python virtual environment
- `run.sh` - Helper script to run the app
- `.env` - Configuration file (needs your Okta credentials)
- All application files (app.py, templates/, static/, etc.)

## Need Help?

- See `README.md` for detailed documentation
- See `SETUP_CORPORATE_CERT.md` for certificate troubleshooting
- See `QUICK_START.md` for quick reference
