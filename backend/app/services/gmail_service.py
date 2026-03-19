import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from app.config import settings
from app.utils.token_crypto import decrypt_token
from app.models.integration import Integration

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def get_auth_url() -> str:
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uris": [settings.google_redirect_uri_gmail],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = settings.google_redirect_uri_gmail
    url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    return url


def exchange_code(code: str) -> dict:
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uris": [settings.google_redirect_uri_gmail],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = settings.google_redirect_uri_gmail
    flow.fetch_token(code=code)
    creds = flow.credentials
    return {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "expiry": creds.expiry,
        "scope": " ".join(SCOPES),
    }


def _get_credentials(integration: Integration) -> Credentials:
    creds = Credentials(
        token=decrypt_token(integration.access_token),
        refresh_token=decrypt_token(integration.refresh_token) if integration.refresh_token else None,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=SCOPES,
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def send_email(integration: Integration, recipient: str, subject: str, body: str, as_draft: bool = False) -> dict:
    creds = _get_credentials(integration)
    service = build("gmail", "v1", credentials=creds)

    message = MIMEText(body)
    message["to"] = recipient
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    if as_draft:
        result = service.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
        return {"message_id": result["id"], "type": "draft"}
    else:
        result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return {"message_id": result["id"], "type": "sent"}
