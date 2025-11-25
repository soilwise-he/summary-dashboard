import os
from flask import redirect, request, session
from flask_appbuilder.security.manager import AUTH_OAUTH
from superset.security import SupersetSecurityManager
from flask_login import current_user

# Keycloak Configuration - Updated for external Keycloak server
KEYCLOAK_INTERNAL_URL = os.getenv('KEYCLOAK_INTERNAL_URL', 'http://keycloak-server:8080')
KEYCLOAK_EXTERNAL_URL = os.getenv('KEYCLOAK_EXTERNAL_URL', 'http://keycloak-server:8080')
KEYCLOAK_REALM = os.getenv('KEYCLOAK_REALM', 'superset_realm')
KEYCLOAK_CLIENT_ID = os.getenv('KEYCLOAK_CLIENT_ID', 'superset')
KEYCLOAK_CLIENT_SECRET = os.getenv('KEYCLOAK_CLIENT_SECRET', 'Z2Gen97MXT3Zdpkc4ZIgipWc4blBaTwu')

# Superset specific config
ROW_LIMIT = 5000
SUPERSET_WEBSERVER_PORT = 8088

# Flask App Builder configuration
AUTH_TYPE = AUTH_OAUTH

# OAuth configuration with prompt parameter
OAUTH_PROVIDERS = [
    {
        'name': 'keycloak',
        'icon': 'fa-key',
        'token_key': 'access_token',
        'remote_app': {
            'client_id': KEYCLOAK_CLIENT_ID,
            'client_secret': KEYCLOAK_CLIENT_SECRET,
            'client_kwargs': {
                'scope': 'openid email profile',
                'prompt': 'login'
            },
            'server_metadata_url': f'{KEYCLOAK_INTERNAL_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration',
            'api_base_url': f'{KEYCLOAK_INTERNAL_URL}/realms/{KEYCLOAK_REALM}/protocol/',
            'access_token_url': f'{KEYCLOAK_INTERNAL_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token',
            'authorize_url': f'{KEYCLOAK_EXTERNAL_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/auth',
            'jwks_uri': f'{KEYCLOAK_INTERNAL_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs',
        }
    }
]

# Enable OAuth logout
OAUTH_LOG_OUT = True

# Custom Security Manager to handle Keycloak roles and logout
class CustomSecurityManager(SupersetSecurityManager):
    def oauth_user_info(self, provider, response=None):
        if provider == 'keycloak':
            me = self.appbuilder.sm.oauth_remotes[provider].get('openid-connect/userinfo')
            data = me.json()
            
            # Get roles from Keycloak
            keycloak_roles = data.get('roles', [])
            
            # Map Keycloak roles to Superset roles
            superset_roles = []
            if 'admin' in keycloak_roles or 'realm-admin' in keycloak_roles:
                superset_roles = ['Admin']
            else:
                superset_roles = ['Gamma']
            
            return {
                'username': data.get('preferred_username', ''),
                'email': data.get('email', ''),
                'first_name': data.get('given_name', ''),
                'last_name': data.get('family_name', ''),
                'role_keys': superset_roles
            }
    
    def get_oauth_redirect_logout_url(self, provider):
        """Get the OAuth provider logout URL"""
        if provider == 'keycloak':
            # Build the post-logout redirect URI (where to go after Keycloak logout)
            post_logout_redirect_uri = request.url_root
            
            # Construct Keycloak logout URL
            logout_url = (
                f"{KEYCLOAK_EXTERNAL_URL}/realms/{KEYCLOAK_REALM}"
                f"/protocol/openid-connect/logout"
                f"?post_logout_redirect_uri={post_logout_redirect_uri}"
                f"&client_id={KEYCLOAK_CLIENT_ID}"
            )
            return logout_url
        return None
    
    def get_oauth_user_info(self, provider, resp):
        """Override to ensure proper session handling"""
        user_info = super().get_oauth_user_info(provider, resp)
        # Store provider in session for logout
        session['oauth_provider'] = provider
        return user_info

CUSTOM_SECURITY_MANAGER = CustomSecurityManager

# Will allow user self registration
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Admin"

# Mapping of Keycloak roles to Superset roles
AUTH_ROLE_ADMIN = 'Admin'
AUTH_ROLE_PUBLIC = 'Public'

# Disable CSRF for OAuth
WTF_CSRF_ENABLED = False

# Session configuration
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = 1800
SESSION_REFRESH_EACH_REQUEST = True

# Use Redis for session storage
SESSION_TYPE = 'redis'
SESSION_REDIS = {
    'host': os.getenv('REDIS_HOST', 'redis'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': 0,
    'key_prefix': 'superset_session:'
}

# Force session clearing on logout
REMEMBER_COOKIE_DURATION = 0

# Secret key for session management
SECRET_KEY = os.getenv('SUPERSET_SECRET_KEY', 'dfXeb4yvtbsF7P1JDlDItoAifnfUIujS')

# Cache configuration
CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'superset_',
    'CACHE_REDIS_HOST': os.getenv('REDIS_HOST', 'redis'),
    'CACHE_REDIS_PORT': int(os.getenv('REDIS_PORT', 6379)),
    'CACHE_REDIS_DB': 1,
}

# Database configuration
SQLALCHEMY_DATABASE_URI = 'sqlite:////app/superset_home/superset.db'

# Async query configuration
RESULTS_BACKEND = CACHE_CONFIG

# Enable Flask session cookie
ENABLE_PROXY_FIX = True

# Prevent browser caching of API responses
SEND_FILE_MAX_AGE_DEFAULT = 0