from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import AsyncSessionLocal, Base, Engine

from router.Product import router_product
from router.Subscribe import router_subscribe
app = FastAPI()

@app.on_event("startup")
async def startup():
    async with Engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(router_product)
app.include_router(router_subscribe)