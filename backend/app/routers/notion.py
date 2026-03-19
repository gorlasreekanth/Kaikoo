from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.integration import Integration
from app.services import notion_service
from app.utils.token_crypto import encrypt_token

router = APIRouter(prefix="/notion", tags=["notion"])


class NotionConfigRequest(BaseModel):
    default_page_id: str | None = None


@router.get("/auth-url")
async def get_auth_url(current_user: User = Depends(get_current_user)):
    return {"url": notion_service.get_auth_url()}


@router.get("/callback")
async def notion_callback(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    return {"message": "Notion authorization received. You can close this window."}


@router.post("/callback")
async def notion_callback_post(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        token_data = notion_service.exchange_code(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = await db.execute(
        select(Integration).where(
            Integration.user_id == current_user.id,
            Integration.service == "notion",
        )
    )
    integration = result.scalar_one_or_none()

    if integration is None:
        integration = Integration(user_id=current_user.id, service="notion")
        db.add(integration)

    integration.access_token = encrypt_token(token_data["access_token"])
    integration.notion_workspace_id = token_data.get("workspace_id")

    await db.commit()
    return {"ok": True}


@router.delete("/disconnect")
async def disconnect_notion(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Integration).where(
            Integration.user_id == current_user.id,
            Integration.service == "notion",
        )
    )
    integration = result.scalar_one_or_none()
    if integration:
        await db.delete(integration)
        await db.commit()
    return {"ok": True}
