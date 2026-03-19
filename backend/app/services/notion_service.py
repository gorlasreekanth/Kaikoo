import httpx
from app.config import settings
from app.utils.token_crypto import decrypt_token
from app.models.integration import Integration

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def get_auth_url() -> str:
    return (
        f"https://api.notion.com/v1/oauth/authorize"
        f"?client_id={settings.notion_client_id}"
        f"&response_type=code"
        f"&owner=user"
        f"&redirect_uri={settings.notion_redirect_uri}"
    )


def exchange_code(code: str) -> dict:
    import base64
    credentials = base64.b64encode(
        f"{settings.notion_client_id}:{settings.notion_client_secret}".encode()
    ).decode()

    resp = httpx.post(
        "https://api.notion.com/v1/oauth/token",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
        },
        json={"grant_type": "authorization_code", "code": code, "redirect_uri": settings.notion_redirect_uri},
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "access_token": data["access_token"],
        "workspace_id": data.get("workspace_id"),
    }


def sync_note_to_notion(integration: Integration, category_name: str, note_content: str, page_id: str | None = None) -> dict:
    token = decrypt_token(integration.access_token)
    headers = _headers(token)

    # If no page_id, create a new page
    if not page_id:
        body = {
            "parent": {"type": "workspace", "workspace": True},
            "properties": {
                "title": {"title": [{"text": {"content": category_name}}]}
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": note_content}}]},
                }
            ],
        }
        resp = httpx.post(f"{NOTION_API}/pages", headers=headers, json=body)
        resp.raise_for_status()
        return {"page_id": resp.json()["id"]}

    # Append to existing page
    body = {
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": note_content}}]},
            }
        ]
    }
    resp = httpx.patch(f"{NOTION_API}/blocks/{page_id}/children", headers=headers, json=body)
    resp.raise_for_status()
    return {"page_id": page_id}
