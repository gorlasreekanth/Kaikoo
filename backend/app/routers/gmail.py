from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.integration import Integration
from app.services import gmail_service
from app.utils.token_crypto import encrypt_token

router = APIRouter(prefix="/gmail", tags=["gmail"])


class SendEmailRequest(BaseModel):
    recipient: str
    subject: str
    body: str
    note_id: str
    action: str = "send"  # 'send' | 'draft'


@router.get("/auth-url")
async def get_auth_url(current_user: User = Depends(get_current_user)):
    return {"url": gmail_service.get_auth_url()}


@router.post("/callback")
async def gmail_callback(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        token_data = gmail_service.exchange_code(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = await db.execute(
        select(Integration).where(
            Integration.user_id == current_user.id,
            Integration.service == "gmail",
        )
    )
    integration = result.scalar_one_or_none()

    if integration is None:
        integration = Integration(user_id=current_user.id, service="gmail")
        db.add(integration)

    integration.access_token = encrypt_token(token_data["access_token"])
    if token_data.get("refresh_token"):
        integration.refresh_token = encrypt_token(token_data["refresh_token"])
    integration.token_expiry = token_data.get("expiry")
    integration.scope = token_data.get("scope")

    await db.commit()
    return {"ok": True}


@router.post("/send")
async def send_email(
    body: SendEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Integration).where(
            Integration.user_id == current_user.id,
            Integration.service == "gmail",
        )
    )
    integration = result.scalar_one_or_none()
    if not integration or not integration.access_token:
        raise HTTPException(status_code=400, detail="Gmail not connected")

    try:
        result_data = gmail_service.send_email(
            integration,
            body.recipient,
            body.subject,
            body.body,
            as_draft=(body.action == "draft"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result_data


@router.delete("/disconnect")
async def disconnect_gmail(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Integration).where(
            Integration.user_id == current_user.id,
            Integration.service == "gmail",
        )
    )
    integration = result.scalar_one_or_none()
    if integration:
        await db.delete(integration)
        await db.commit()
    return {"ok": True}
