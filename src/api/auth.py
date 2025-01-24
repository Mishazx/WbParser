from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from db import get_db
from models import ApiKey

security = HTTPBearer()

class ApiKeyResponse(BaseModel):
    """Модель ответа для API ключа"""
    key: str
    is_active: bool

async def get_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db)
) -> str:
    """
    Проверяет API ключ в заголовке Authorization.
    Ожидает заголовок в формате: Bearer <api_key>
    Возвращает строку с API ключом если он валиден
    """
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.key == credentials.credentials)
        .where(ApiKey.is_active == True)
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "INVALID_API_KEY",
                "detail": "Неверный API ключ"
            }
        )
    return api_key.key 