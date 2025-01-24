from apscheduler.schedulers.asyncio import AsyncIOScheduler
import httpx

from schemas import ProductCreate
from db import AsyncSessionLocal

scheduler = AsyncIOScheduler()

async def fetch_product_data(artikul: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={artikul}")
        data = response.json()
        try:
            product_data = data["data"]["products"][0]
            return {
                "name": product_data["name"],
                "artikul": artikul,
                "price": product_data["salePriceU"] / 100,
                "rating": product_data.get("reviewRating", 0),
                "total_quantity": product_data.get("totalQuantity", 0)
            }
        except (KeyError, IndexError) as e:
            raise Exception(f"Failed to parse product data: {str(e)}")

async def update_product_data(artikul: str):
    from crud import create_product, log_task
    async with AsyncSessionLocal() as session:
        try:
            product = await create_product(session, ProductCreate(artikul=artikul))
            # Создаем сообщение с данными продукта
            log_message = {
                "name": product.name,
                "price": product.price,
                "rating": product.rating,
                "total_quantity": product.total_quantity
            }
            await log_task(session, artikul, "success", str(log_message))
        except Exception as e:
            await log_task(session, artikul, "error", str(e))
            raise

def schedule_product_updates(artikul: str):
    job = scheduler.get_job(artikul)
    if not job:
        scheduler.add_job(
            update_product_data, 
            'interval',
            minutes=1,
            id=artikul,
            args=[artikul],
            max_instances=1,  # Предотвращаем параллельное выполнение одной и той же задачи
            replace_existing=True  # Заменяем существующую задачу, если она есть
        )
        if not scheduler.running:
            scheduler.start()