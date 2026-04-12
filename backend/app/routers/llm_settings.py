from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.deps import get_db, get_current_user
from app.models.user import User
from app.models.llm_settings import LLMSettings
from app.schemas.llm_settings import LLMSettingsOut, LLMSettingsUpdate
from app.services.llm_service import chat
from app.utils.token_crypto import encrypt_token

router = APIRouter(prefix="/llm-settings", tags=["llm-settings"])

VALID_PROVIDERS = {"anthropic", "openai"}


@router.get("", response_model=LLMSettingsOut)
async def get_llm_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(LLMSettings).where(LLMSettings.user_id == current_user.id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return LLMSettingsOut()
    return LLMSettingsOut(
        provider=row.provider,
        has_api_key=row.api_key is not None,
        model=row.model,
    )


@router.put("", response_model=LLMSettingsOut)
async def update_llm_settings(
    body: LLMSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(LLMSettings).where(LLMSettings.user_id == current_user.id)
    )
    row = result.scalar_one_or_none()

    if row is None:
        row = LLMSettings(user_id=current_user.id)
        db.add(row)

    if body.provider is not None:
        row.provider = body.provider if body.provider in VALID_PROVIDERS else None
    elif body.provider is None and "provider" in body.model_fields_set:
        # Explicitly set to null — clear provider (use default)
        row.provider = None

    if body.api_key is not None:
        row.api_key = encrypt_token(body.api_key)
    elif body.api_key is None and "api_key" in body.model_fields_set:
        row.api_key = None

    if body.model is not None:
        row.model = body.model
    elif body.model is None and "model" in body.model_fields_set:
        row.model = None

    await db.commit()
    await db.refresh(row)

    return LLMSettingsOut(
        provider=row.provider,
        has_api_key=row.api_key is not None,
        model=row.model,
    )


class TestResult(BaseModel):
    ok: bool
    message: str


@router.post("/test", response_model=TestResult)
async def test_llm_connection(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a minimal prompt to verify the LLM connection works."""
    result = await db.execute(
        select(LLMSettings).where(LLMSettings.user_id == current_user.id)
    )
    user_llm = result.scalar_one_or_none()

    try:
        response = await chat(
            system="You are a helpful assistant.",
            user_message="Reply with exactly: OK",
            role="fast",
            max_tokens=10,
            user_llm_settings=user_llm,
        )
        return TestResult(ok=True, message=f"Connected — model replied: {response[:50]}")
    except Exception as e:
        return TestResult(ok=False, message=str(e)[:200])
