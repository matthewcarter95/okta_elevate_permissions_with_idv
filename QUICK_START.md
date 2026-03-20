# Quick Start with Corporate Certificate

## Immediate Steps to Get Running

### 1. Save Your Certificate
Save your Palo Alto PEM certificate in this directory:
```bash
# Copy your PEM file here and name it corporate-ca.pem
cp /path/to/your/palo-alto.pem ./corporate-ca.pem
```

### 2. Install Dependencies with Certificate
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install using your certificate
pip install --cert ./corporate-ca.pem -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy example config
cp .env.example .env

# Edit .env and set these values:
# OKTA_DOMAIN=your-domain.okta.com
# OKTA_CLIENT_ID=your-client-id
# OKTA_CLIENT_SECRET=your-client-secret
# SSL_CERT_PATH=./corporate-ca.pem
```

### 4. Run the Application
```bash
python app.py
```

Visit http://localhost:5000

---

## If Installation Still Fails

### Option A: Set Environment Variable
```bash
export PIP_CERT=./corporate-ca.pem
export REQUESTS_CA_BUNDLE=./corporate-ca.pem
pip install -r requirements.txt
```

### Option B: Disable SSL Verification (Testing Only)
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

Then in your `.env`, set:
```
SSL_CERT_PATH=False
```

**Warning**: Option B disables security checks. Only use for initial testing.

---

## Need More Help?
See [SETUP_CORPORATE_CERT.md](SETUP_CORPORATE_CERT.md) for detailed troubleshooting.
