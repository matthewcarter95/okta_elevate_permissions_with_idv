from flask import Flask, redirect, url_for, session, render_template, request, flash, jsonify
from authlib.integrations.flask_client import OAuth
import requests
from config import Config
from functools import wraps
import os

app = Flask(__name__)
app.config.from_object(Config)

# Additional Flask session configuration
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Validate configuration
Config.validate()
print(f"DEBUG: SECRET_KEY configured: {bool(app.config.get('SECRET_KEY'))}")

# Certificate handling: Corporate cert is appended to venv's certifi bundle
# No special configuration needed for requests - it will use certifi automatically

# Initialize OAuth
# Certificate is already in the certifi CA bundle (corporate-ca.pem was appended to venv certifi)
oauth = OAuth(app)

okta = oauth.register(
    'okta',
    client_id=Config.OKTA_CLIENT_ID,
    client_secret=Config.OKTA_CLIENT_SECRET,
    server_metadata_url=f"{Config.OKTA_ISSUER}/.well-known/openid-configuration",
    client_kwargs={'scope': Config.SCOPES}
)


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"DEBUG: login_required check, session keys: {list(session.keys())}")
        if 'access_token' not in session:
            print("DEBUG: No access_token, redirecting to login")
            return redirect(url_for('login'))
        print("DEBUG: access_token found, proceeding")
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """Home page - redirects to profile if logged in"""
    print(f"DEBUG: index route, session keys: {list(session.keys())}")
    if 'access_token' in session:
        print("DEBUG: Has access_token, redirecting to profile")
        return redirect(url_for('profile'))
    print("DEBUG: No access_token, showing index page")
    return render_template('index.html')


@app.route('/login')
def login():
    """Initiate OAuth2 login flow"""
    redirect_uri = url_for('callback', _external=True)
    return okta.authorize_redirect(redirect_uri)


@app.route('/callback')
def callback():
    """OAuth2 callback handler"""
    try:
        print("DEBUG: Starting callback")
        token = okta.authorize_access_token()
        print(f"DEBUG: Got token, access_token present: {'access_token' in token}")

        # Mark session as permanent to ensure it persists
        session.permanent = True

        session['access_token'] = token['access_token']
        session['id_token'] = token.get('id_token')
        session.modified = True  # Force session to save
        print(f"DEBUG: Stored in session, session keys: {list(session.keys())}")

        # Get user info
        userinfo = okta.get(Config.USERINFO_ENDPOINT).json()
        session['user'] = userinfo
        print(f"DEBUG: Got userinfo: {userinfo.get('email', 'no email')}")

        flash('Successfully logged in!', 'success')
        print("DEBUG: Redirecting to profile")
        return redirect(url_for('profile'))
    except Exception as e:
        print(f"DEBUG: Exception in callback: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Login failed: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    """Display user profile from MyAccount API"""
    try:
        print("DEBUG: In profile route, about to call MyAccount API")
        # Get profile from MyAccount API
        # MyAccount API uses ION+JSON hypermedia format
        headers = {
            'Authorization': f"Bearer {session['access_token']}",
            'Accept': 'application/ion+json; okta-version=1.0.0',
            'Content-Type': 'application/ion+json; okta-version=1.0.0'
        }

        print(f"DEBUG: Calling {Config.MYACCOUNT_BASE_URL}/profile")
        response = requests.get(
            f"{Config.MYACCOUNT_BASE_URL}/profile",
            headers=headers
        )
        print(f"DEBUG: MyAccount API response status: {response.status_code}")

        if response.status_code == 200:
            profile_data = response.json()
            print(f"DEBUG: Got profile data, keys: {list(profile_data.keys())}")

            # Check if user has elevated permissions
            elevated = profile_data.get('profile', {}).get('elevatePermission', False)
            print(f"DEBUG: Elevated status: {elevated}")

            print("DEBUG: Rendering profile.html")
            return render_template(
                'profile.html',
                profile=profile_data,
                elevated=elevated
            )
        else:
            print(f"DEBUG: MyAccount API failed with status {response.status_code}")
            print(f"DEBUG: Response body: {response.text[:200]}")
            flash(f'Failed to load profile: {response.status_code}', 'error')
            return redirect(url_for('index'))

    except Exception as e:
        print(f"DEBUG: Exception in profile route: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Error loading profile: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/elevate', methods=['POST'])
def elevate():
    """Trigger permission elevation by updating profile attribute"""
    print("=" * 80)
    print(f"DEBUG: /elevate route called, method: {request.method}")
    print(f"DEBUG: Session has access_token: {'access_token' in session}")

    # Check authentication
    if 'access_token' not in session:
        print("DEBUG: No access_token in session, returning 401")
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    # Step 1: List available authenticators to get an authenticatorId
    try:
        print("DEBUG: Step 1 - Listing available authenticators")
        headers = {
            'Authorization': f"Bearer {session['access_token']}",
            'Accept': 'application/ion+json; okta-version=1.0.0',
            'Content-Type': 'application/ion+json; okta-version=1.0.0'
        }

        # List authenticators from MyAccount API
        list_url = f"{Config.MYACCOUNT_BASE_URL}/authenticators"
        print(f"DEBUG: GET {list_url}")

        list_response = requests.get(list_url, headers=headers)
        print(f"DEBUG: List authenticators status: {list_response.status_code}")
        print(f"DEBUG: List authenticators response: {list_response.text[:500]}")

        if list_response.status_code != 200:
            return jsonify({
                'success': False,
                'message': f'Failed to list authenticators: {list_response.status_code}'
            }), list_response.status_code

        authenticators = list_response.json()
        print(f"DEBUG: Authenticators response is a list with {len(authenticators)} items")

        # Find an enrollable authenticator (e.g., Google Authenticator)
        authenticator_id = None

        for auth in authenticators:
            print(f"DEBUG: Authenticator: key={auth.get('key')}, enrollable={auth.get('enrollable')}, id={auth.get('id')}")

            # Look for google_otp (Google Authenticator) first
            if auth.get('key') == 'google_otp' and auth.get('enrollable'):
                authenticator_id = auth.get('id')
                print(f"DEBUG: Found Google Authenticator: {authenticator_id}")
                break

        if not authenticator_id:
            # Try phone_number next (this often supports multiple enrollments)
            for auth in authenticators:
                if auth.get('key') == 'phone_number' and auth.get('enrollable'):
                    authenticator_id = auth.get('id')
                    print(f"DEBUG: Using phone_number authenticator: {authenticator_id}")
                    break

        if not authenticator_id:
            # Try webauthn (security key)
            for auth in authenticators:
                if auth.get('key') == 'webauthn' and auth.get('enrollable'):
                    authenticator_id = auth.get('id')
                    print(f"DEBUG: Using webauthn authenticator: {authenticator_id}")
                    break

        if not authenticator_id:
            return jsonify({
                'success': False,
                'message': 'No unenrolled authenticators available'
            }), 400

        # Step 2: Build the enrollment URL with redirect_uri
        import secrets
        state_token = secrets.token_urlsafe(32)
        session['idv_state'] = state_token
        session['idv_initiated'] = True
        session.modified = True

        redirect_uri = "http://localhost:5000/idv-callback"
        enrollment_url = f"https://{Config.OKTA_DOMAIN}/idp/bootstrap/enroll-authenticator/{authenticator_id}?redirect_uri={redirect_uri}"

        print(f"DEBUG: Enrollment URL: {enrollment_url}")
        print(f"DEBUG: State token: {state_token}")

        return jsonify({
            'success': True,
            'redirect_required': True,
            'redirect_url': enrollment_url,
            'message': 'Redirecting to Okta for authenticator enrollment and identity verification...'
        })

    except Exception as e:
        print(f"DEBUG: Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

    try:
        print("DEBUG: Building headers for Okta MyAccount API")
        # MyAccount API uses ION+JSON hypermedia format
        headers = {
            'Authorization': f"Bearer {session['access_token']}",
            'Content-Type': 'application/ion+json; okta-version=1.0.0',
            'Accept': 'application/ion+json; okta-version=1.0.0'
        }
        print(f"DEBUG: Headers prepared: {list(headers.keys())}")

        # Try using standard Okta API instead of MyAccount API
        # This may trigger Account Management policies more reliably
        use_standard_api = False  # Use MyAccount API which is working

        if use_standard_api:
            # Use standard Okta Users API
            url = f"{Config.API_BASE_URL}/users/me"
            print(f"DEBUG: Using standard API endpoint: {url}")
            headers = {
                'Authorization': f"Bearer {session['access_token']}",
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        else:
            # Use MyAccount API
            url = f"{Config.MYACCOUNT_BASE_URL}/profile"

        # Step 1: GET the current profile
        print(f"DEBUG: Step 1 - Getting current profile from: {url}")
        get_response = requests.get(url, headers=headers)
        print(f"DEBUG: GET response status: {get_response.status_code}")

        if get_response.status_code != 200:
            print(f"DEBUG: Failed to get profile: {get_response.text[:200]}")
            return jsonify({
                'success': False,
                'message': f'Failed to get current profile: {get_response.status_code}'
            }), get_response.status_code

        # Step 2: Modify the elevatePermission attribute
        profile_data = get_response.json()
        print(f"DEBUG: Got profile, keys: {list(profile_data.keys())}")

        if use_standard_api:
            # Standard API: profile is at top level
            if 'profile' not in profile_data:
                print(f"DEBUG: No 'profile' key in response")
                return jsonify({
                    'success': False,
                    'message': 'Invalid profile structure returned from API'
                }), 500

            # Update just the profile attributes
            profile_update = {
                'profile': {
                    'elevatePermission': True
                }
            }
            print(f"DEBUG: Sending partial update: {profile_update}")

            # Standard API uses POST for partial updates
            response = requests.post(url, headers=headers, json=profile_update)
        else:
            # MyAccount API: requires full profile
            if 'profile' not in profile_data:
                print(f"DEBUG: No 'profile' key in response: {profile_data}")
                return jsonify({
                    'success': False,
                    'message': 'Invalid profile structure returned from API'
                }), 500

            # Update the elevatePermission field
            profile_data['profile']['elevatePermission'] = True
            print(f"DEBUG: Modified profile, elevatePermission = True")

            # Step 3: PUT the entire profile back
            print(f"DEBUG: Step 2 - Sending PUT with full profile to: {url}")
            response = requests.put(url, headers=headers, json=profile_data)

        print(f"DEBUG: PATCH request completed")
        print(f"DEBUG: Response status: {response.status_code}")
        print(f"DEBUG: Response headers: {dict(response.headers)}")
        print(f"DEBUG: Response body: {response.text[:500]}")
        print("=" * 80)

        if response.status_code in [200, 202]:
            # The update was accepted - IDV flow may be triggered by Okta policy
            return jsonify({
                'success': True,
                'message': 'Elevation request submitted. Identity verification may be required.'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to submit elevation request: {response.status_code}',
                'details': response.text
            }), response.status_code

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/check-elevation')
def check_elevation():
    """Check current elevation status"""
    # Check authentication
    if 'access_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        # MyAccount API uses ION+JSON hypermedia format
        headers = {
            'Authorization': f"Bearer {session['access_token']}",
            'Accept': 'application/ion+json; okta-version=1.0.0',
            'Content-Type': 'application/ion+json; okta-version=1.0.0'
        }

        response = requests.get(
            f"{Config.MYACCOUNT_BASE_URL}/profile",
            headers=headers
        )

        if response.status_code == 200:
            profile_data = response.json()
            elevated = profile_data.get('profile', {}).get('elevatePermission', False)

            return jsonify({
                'elevated': elevated
            })
        else:
            return jsonify({
                'error': 'Failed to check status'
            }), response.status_code

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/idv-callback')
def idv_callback():
    """Handle return from Okta after IDV/enrollment"""
    print("DEBUG: User returned from Okta IDV flow")
    print(f"DEBUG: Session keys: {list(session.keys())}")

    if 'idv_initiated' in session:
        print("DEBUG: IDV was initiated, completing elevation")
        session.pop('idv_initiated', None)
        session.pop('idv_state', None)

        # Now update the profile attribute
        try:
            headers = {
                'Authorization': f"Bearer {session['access_token']}",
                'Content-Type': 'application/ion+json; okta-version=1.0.0',
                'Accept': 'application/ion+json; okta-version=1.0.0'
            }

            profile_url = f"{Config.MYACCOUNT_BASE_URL}/profile"

            # Get current profile
            get_response = requests.get(profile_url, headers=headers)
            if get_response.status_code == 200:
                profile_data = get_response.json()
                profile_data['profile']['elevatePermission'] = True

                # Update profile
                put_response = requests.put(profile_url, headers=headers, json=profile_data)
                print(f"DEBUG: Profile update status: {put_response.status_code}")

                if put_response.status_code == 200:
                    flash('Identity verification complete! Permissions elevated.', 'success')
                else:
                    flash('Verification complete but elevation failed. Please try again.', 'error')
            else:
                flash('Could not complete elevation. Please try again.', 'error')

        except Exception as e:
            print(f"DEBUG: Error updating profile: {e}")
            flash('Error completing elevation. Please try again.', 'error')

    return redirect(url_for('profile'))


@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()

    # Redirect to Okta logout endpoint
    logout_url = (
        f"https://{Config.OKTA_DOMAIN}/oauth2/default/v1/logout?"
        f"id_token_hint={session.get('id_token', '')}&"
        f"post_logout_redirect_uri={request.url_root}"
    )

    return redirect(logout_url)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
