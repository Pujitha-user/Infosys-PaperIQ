import os
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import streamlit as st

# Configuration
CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "client_secrets.json")
SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
REDIRECT_URI = "http://localhost:8501"

def get_flow():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        return None
    
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES
    )
    flow.redirect_uri = REDIRECT_URI
    return flow

def get_auth_url():
    flow = get_flow()
    if not flow:
        return None
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    return authorization_url

def get_user_info(code):
    flow = get_flow()
    if not flow:
        return None
        
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    service = build('oauth2', 'v2', credentials=credentials)
    user_info = service.userinfo().get().execute()
    return user_info
