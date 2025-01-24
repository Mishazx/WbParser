from fastapi import FastAPI
from sqladmin import Admin

from admin import ProductAdmin, TaskLogAdmin, ApiKeyAdmin
from db import Base, SyncEngine, AsyncEngine, AsyncSessionLocal
from router import router_product
from crud import get_active_subscriptions
from tasks import schedule_product_updates

app = FastAPI()

@app.on_event("startup")
async def startup():
    async with AsyncEngine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        subscriptions = await get_active_subscriptions(session)
        for sub in subscriptions:
            schedule_product_updates(sub.artikul)

@app.on_event("shutdown")
async def shutdown():
    await AsyncEngine.dispose()

app.include_router(router_product)

admin = Admin(app, engine=SyncEngine)
admin.add_view(ProductAdmin)
admin.add_view(TaskLogAdmin)
admin.add_view(ApiKeyAdmin)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8888, reload=True)

