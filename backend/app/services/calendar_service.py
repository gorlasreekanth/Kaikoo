from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from app.config import settings
from app.utils.token_crypto import encrypt_token, decrypt_token
from app.models.integration import Integration

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def get_auth_url() -> str:
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uris": [settings.google_redirect_uri_calendar],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = settings.google_redirect_uri_calendar
    url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    return url


def exchange_code(code: str) -> dict:
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uris": [settings.google_redirect_uri_calendar],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = settings.google_redirect_uri_calendar
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


def create_event(integration: Integration, title: str, start_time: str, end_time: str, description: str) -> dict:
    creds = _get_credentials(integration)
    service = build("calendar", "v3", credentials=creds)

    event = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_time, "timeZone": "UTC"},
        "end": {"dateTime": end_time, "timeZone": "UTC"},
    }
    result = service.events().insert(calendarId="primary", body=event).execute()
    return {"event_id": result["id"], "event_url": result.get("htmlLink", "")}
