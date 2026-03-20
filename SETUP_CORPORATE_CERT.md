# Setting Up with Corporate SSL Certificate

If you're behind a corporate firewall (like Palo Alto) that performs SSL inspection, you'll need to configure Python and pip to trust your corporate certificate.

## Step 1: Locate or Save Your Certificate

You mentioned having a PEM file for your Palo Alto certificate. Save it in this project directory:

```bash
# Copy your certificate to the project (adjust path as needed)
cp /path/to/your/palo-alto-cert.pem ./corporate-ca.pem
```

Or if you need to export it from your browser:
1. Open any HTTPS site in your browser
2. Click the padlock icon
3. View certificate details
4. Export the root CA certificate as PEM format
5. Save as `corporate-ca.pem` in this directory

## Step 2: Install Python Packages with Certificate

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install pip packages using your certificate
pip install --cert ./corporate-ca.pem -r requirements.txt

# Or set it as an environment variable for the session
export PIP_CERT=./corporate-ca.pem  # On Windows: set PIP_CERT=./corporate-ca.pem
pip install -r requirements.txt
```

## Step 3: Configure Application to Use Certificate

Edit your `.env` file and add:

```bash
SSL_CERT_PATH=/absolute/path/to/corporate-ca.pem
```

Or use a relative path:
```bash
SSL_CERT_PATH=./corporate-ca.pem
```

## Step 4: Set System Environment Variables (Optional)

For a more permanent solution, set these environment variables:

### On macOS/Linux:
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
export REQUESTS_CA_BUNDLE=/path/to/corporate-ca.pem
export SSL_CERT_FILE=/path/to/corporate-ca.pem
export PIP_CERT=/path/to/corporate-ca.pem
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

### On Windows:
Set system environment variables:
```cmd
setx REQUESTS_CA_BUNDLE "C:\path\to\corporate-ca.pem"
setx SSL_CERT_FILE "C:\path\to\corporate-ca.pem"
setx PIP_CERT "C:\path\to\corporate-ca.pem"
```

## Step 5: Run the Application

```bash
source venv/bin/activate
python app.py
```

## Troubleshooting

### Still getting SSL errors?

1. **Verify certificate format**: Ensure your PEM file is properly formatted:
```bash
openssl x509 -in corporate-ca.pem -text -noout
```

2. **Check if certificate is being used**:
```bash
# Test with curl
curl --cacert ./corporate-ca.pem https://your-domain.okta.com

# Test with Python
python -c "import requests; print(requests.get('https://your-domain.okta.com', verify='./corporate-ca.pem'))"
```

3. **Combine certificates**: If you have multiple CAs, combine them:
```bash
cat corporate-ca.pem >> combined-ca.pem
cat /etc/ssl/certs/ca-certificates.crt >> combined-ca.pem  # On Linux
# Or on macOS: cat /etc/ssl/cert.pem >> combined-ca.pem
```

Then use `combined-ca.pem` in your configuration.

### Alternative: Disable SSL Verification (NOT RECOMMENDED FOR PRODUCTION)

Only for local testing, you can disable SSL verification:

In `.env`:
```bash
SSL_CERT_PATH=False
```

Then modify `app.py` to handle this:
```python
def get_requests_kwargs():
    if Config.SSL_CERT_PATH == 'False':
        return {'verify': False}
    elif Config.SSL_CERT_PATH and os.path.exists(Config.SSL_CERT_PATH):
        return {'verify': Config.SSL_CERT_PATH}
    return {}
```

**Warning**: This disables certificate validation and should never be used in production.

## Testing the Setup

Once configured, test the connection:

```bash
python -c "
from config import Config
import requests
Config.validate()
print('Testing connection to Okta...')
try:
    verify = Config.SSL_CERT_PATH if Config.SSL_CERT_PATH else True
    r = requests.get(f'https://{Config.OKTA_DOMAIN}', verify=verify)
    print(f'Success! Status code: {r.status_code}')
except Exception as e:
    print(f'Error: {e}')
"
```

If this succeeds, your certificate is configured correctly.
