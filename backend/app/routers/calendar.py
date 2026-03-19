from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.integration import Integration
from app.services import calendar_service
from app.utils.token_crypto import encrypt_token

router = APIRouter(prefix="/calendar", tags=["calendar"])


class CreateEventRequest(BaseModel):
    title: str
    start_time: str
    end_time: str
    description: str = ""
    note_id: str


@router.get("/auth-url")
async def get_auth_url(current_user: User = Depends(get_current_user)):
    return {"url": calendar_service.get_auth_url()}


@router.get("/callback")
async def calendar_callback(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    # Note: In production, validate state param for CSRF prevention
    # This callback is hit by the browser after OAuth, without a user JWT
    # The user should be stored in a session or passed via state param
    # For simplicity here, we return an HTML close-window page
    return {"message": "Authorization received. You can close this window."}


@router.post("/callback")
async def calendar_callback_post(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        token_data = calendar_service.exchange_code(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = await db.execute(
        select(Integration).where(
            Integration.user_id == current_user.id,
            Integration.service == "google_calendar",
        )
    )
    integration = result.scalar_one_or_none()

    if integration is None:
        integration = Integration(user_id=current_user.id, service="google_calendar")
        db.add(integration)

    integration.access_token = encrypt_token(token_data["access_token"])
    if token_data.get("refresh_token"):
        integration.refresh_token = encrypt_token(token_data["refresh_token"])
    integration.token_expiry = token_data.get("expiry")
    integration.scope = token_data.get("scope")

    await db.commit()
    return {"ok": True}


@router.post("/events")
async def create_event(
    body: CreateEventRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Integration).where(
            Integration.user_id == current_user.id,
            Integration.service == "google_calendar",
        )
    )
    integration = result.scalar_one_or_none()
    if not integration or not integration.access_token:
        raise HTTPException(status_code=400, detail="Google Calendar not connected")

    try:
        event_data = calendar_service.create_event(
            integration, body.title, body.start_time, body.end_time, body.description
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return event_data


@router.delete("/disconnect")
async def disconnect_calendar(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Integration).where(
            Integration.user_id == current_user.id,
            Integration.service == "google_calendar",
        )
    )
    integration = result.scalar_one_or_none()
    if integration:
        await db.delete(integration)
        await db.commit()
    return {"ok": True}
