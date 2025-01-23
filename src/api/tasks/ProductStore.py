from api.crud.Product import create_product
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import httpx
from ..database.db import AsyncSessionLocal

scheduler = AsyncIOScheduler()

async def fetch_and_store_product(artikul: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={artikul}")
        data =response.json()

        async with AsyncSessionLocal as session:
            await create_product(session, {
                "name": data["data"]["name"],
                "artikul": artikul,
                "price": data["data"]["price"],
                "rating": data["data"]["rating"],
                "total_quantity": data["data"]["total_quantity"]
            })
        
def start_periodic_fetch(artikul: str):
    scheduler.add_job(fetch_and_store_product, 'interval', 
                      args=[artikul], minutes=30)
    scheduler.start()