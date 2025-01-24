from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from db import AsyncSessionLocal
from models import ApiKey

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ApiKey).where(
                ApiKey.key == token,
                ApiKey.is_active == True
            )
        )
        api_key = result.scalar_one_or_none()
        
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired API key"
            )
        return api_key

def get_api_key():
    return Depends(verify_api_key) 