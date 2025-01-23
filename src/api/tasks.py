from apscheduler.schedulers.asyncio import AsyncIOScheduler
import httpx

scheduler = AsyncIOScheduler()

async def fetch_product_data(artikul: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={artikul}")
        data = response.json()
        return {
            "name": data["data"]["products"][0]["name"],
            "artikul": artikul,
            "price": data["data"]["products"][0]["salePriceU"] / 100,
            "rating": data["data"]["products"][0].get("reviewRating", 0),
            "total_quantity": data["data"]["products"][0].get("totalQuantity", 0)
        }

def start_periodic_fetch(artikul: str):
    scheduler.add_job(fetch_product_data, 'interval', 
                     args=[artikul], minutes=1)
    scheduler.start()