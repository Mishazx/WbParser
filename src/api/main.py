from fastapi import FastAPI
from sqladmin import Admin

from admin import ProductAdmin
from db import Base, SyncEngine, AsyncEngine
from router import router_product

app = FastAPI()

@app.on_event("startup")
async def startup():
    async with AsyncEngine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("shutdown")
async def shutdown():
    await AsyncEngine.dispose()

app.include_router(router_product)

admin = Admin(app, engine=SyncEngine)
admin.add_view(ProductAdmin)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8888, reload=True)

