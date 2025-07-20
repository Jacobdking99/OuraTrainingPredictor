from requests_oauthlib import OAuth2Session
from python_dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()

# Oura API credentials
CLIENT_ID = os.getenv("OURA_CLIENT_ID")
CLIENT_SECRET = os.getenv("OURA_CLIENT_SECRET")
AUTHORIZATION_BASE_URL = "https://cloud.ouraring.com/oauth/authorize"
TOKEN_URL = "https://api.ouraring.com/oauth/token"
REDIRECT_URI = "https://oura-training-predictor.streamlit.app"  # Update this for production

def get_authorization_url():
    """Generate the Oura authorization URL."""
    oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI)
    authorization_url, state = oauth.authorization_url(AUTHORIZATION_BASE_URL)
    return authorization_url

def fetch_access_token(code):
    """Exchange the authorization code for an access token."""
    oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI)
    token = oauth.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET, code=code)
    return token["access_token"]