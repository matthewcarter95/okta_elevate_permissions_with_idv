# ✅ Ready to Run!

## What Was Fixed

The SSL certificate issue has been resolved. Your Prisma certificate has been added to the Python certifi CA bundle, so all HTTPS requests will now work properly.

**Solution Applied:**
- Appended `corporate-ca.pem` to the certifi bundle in your virtual environment
- Simplified the code to use the standard certifi bundle
- No environment variables or special configuration needed

## Your Configuration

✅ **Okta Domain:** demo-white-hyena-sko.okta.com
✅ **Client ID:** Configured
✅ **Client Secret:** Configured
✅ **Certificate:** Added to certifi bundle
✅ **Dependencies:** All installed

## Running the Application

Just run:
```bash
./run.sh
```

Then open your browser to: **http://localhost:5000**

## Before You Test

Make sure you've configured in Okta:

### 1. Custom Profile Attribute
- Go to **Directory** > **Profile Editor** > **User (default)**
- Add attribute:
  - Variable name: `elevatePermission`
  - Data type: Boolean
  - Default: false

### 2. Application Scopes
Your Okta app needs these scopes:
- `okta.myAccount.profile.read`
- `okta.myAccount.profile.manage`

### 3. Account Management Policy
- Go to **Security** > **Account Management**
- Create a policy that:
  - Triggers on `elevatePermission` attribute change
  - Requires Identity Verification
  - Allows change on successful verification

## Testing the Flow

1. **Login:** Click "Login with Okta"
2. **View Profile:** See your user attributes
3. **Elevate:** Click "Elevate Permissions"
4. **Verify:** Complete IDV if prompted by Okta
5. **Success:** Page auto-refreshes showing elevated status

## Need to Stop the App?

Press `Ctrl+C` in the terminal

## Future Certificate Updates

If you ever recreate the virtual environment, you'll need to add the certificate again:
```bash
source venv/bin/activate
cat corporate-ca.pem >> $(python -m certifi)
```

## Troubleshooting

### "Permission denied" when running
```bash
chmod +x run.sh
```

### App doesn't start
```bash
source venv/bin/activate
python app.py
```

### Check if certificate is still in certifi
```bash
source venv/bin/activate
grep "Okta Root CA" $(python -m certifi)
```
If nothing is returned, re-add the certificate.

---

**You're all set! Run `./run.sh` to start the application.** 🚀
