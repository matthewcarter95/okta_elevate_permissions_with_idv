import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Okta
    OKTA_DOMAIN = os.getenv('OKTA_DOMAIN')
    OKTA_CLIENT_ID = os.getenv('OKTA_CLIENT_ID')
    OKTA_CLIENT_SECRET = os.getenv('OKTA_CLIENT_SECRET')
    REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:5000/callback')

    # SSL Certificate Path (for corporate proxy/firewall)
    SSL_CERT_PATH = os.getenv('SSL_CERT_PATH', None)

    # OAuth2 Configuration
    OKTA_ISSUER = f"https://{OKTA_DOMAIN}/oauth2/default"
    AUTHORIZATION_ENDPOINT = f"https://{OKTA_DOMAIN}/oauth2/default/v1/authorize"
    TOKEN_ENDPOINT = f"https://{OKTA_DOMAIN}/oauth2/default/v1/token"
    USERINFO_ENDPOINT = f"https://{OKTA_DOMAIN}/oauth2/default/v1/userinfo"

    # MyAccount API
    MYACCOUNT_BASE_URL = f"https://{OKTA_DOMAIN}/idp/myaccount"

    # Alternative: Standard Okta API (if MyAccount API has issues)
    API_BASE_URL = f"https://{OKTA_DOMAIN}/api/v1"

    # Scopes needed for MyAccount API (including authenticators for enrollment)
    SCOPES = "openid profile email okta.myAccount.profile.read okta.myAccount.profile.manage okta.myAccount.authenticators.read"

    @staticmethod
    def validate():
        """Validate required configuration"""
        required = ['OKTA_DOMAIN', 'OKTA_CLIENT_ID', 'OKTA_CLIENT_SECRET']
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
