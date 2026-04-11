from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.deps import get_db, get_current_user
from app.models.user import User
from app.models.integration import Integration
from app.schemas.integration import IntegrationStatus

router = APIRouter(prefix="/integrations", tags=["integrations"])

SERVICES = ["google_calendar", "gmail", "notion"]


@router.get("", response_model=list[IntegrationStatus])
async def list_integrations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Integration).where(Integration.user_id == current_user.id)
    )
    connected = {i.service: i for i in result.scalars().all()}

    return [
        IntegrationStatus(
            service=svc,
            connected=svc in connected and connected[svc].access_token is not None,
        )
        for svc in SERVICES
    ]
