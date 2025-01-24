import logging
from fastapi import FastAPI
from sqlalchemy import select
from sqladmin import Admin

from admin import ProductAdmin, TaskLogAdmin, ApiKeyAdmin, SubscriptionAdmin
from crud import get_active_subscriptions, create_api_key
from models import ApiKey
from db import connect_with_retries, SyncEngine, AsyncEngine, AsyncSessionLocal
from router import router_product
from tasks import start_scheduler

logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

app = FastAPI()

@app.on_event("startup")
async def startup():
    await connect_with_retries()
    
    async with AsyncSessionLocal() as session:
        existing_keys = await session.execute(select(ApiKey))
        if not existing_keys.scalars().first():
            await create_api_key(session, "Initial API Key")
        
        subscriptions = await get_active_subscriptions(session)
    
    start_scheduler()

@app.on_event("shutdown")
async def shutdown():
    await AsyncEngine.dispose()

app.include_router(router_product)

admin = Admin(app, engine=SyncEngine)
admin.add_view(ProductAdmin)
admin.add_view(TaskLogAdmin)
admin.add_view(ApiKeyAdmin)
admin.add_view(SubscriptionAdmin)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8888, reload=True)

