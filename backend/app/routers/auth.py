from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.user import AuthResponse, UserOut
from app.services.auth_service import verify_google_token, upsert_user, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class GoogleLoginRequest(BaseModel):
    id_token: str


@router.post("/google", response_model=AuthResponse)
async def google_login(body: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        idinfo = await verify_google_token(body.id_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    user = await upsert_user(db, idinfo)
    token = create_access_token(str(user.id))
    return AuthResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)
