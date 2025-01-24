from apscheduler.schedulers.asyncio import AsyncIOScheduler
import httpx
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select

from schemas import ProductCreate
from db import AsyncSessionLocal
from models import Subscription

# Настройка логгера
logging.basicConfig(
    filename='subscription_updates.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

scheduler = AsyncIOScheduler()

async def fetch_product_data(artikul: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={artikul}")
        data = response.json()
        try:
            if not data["data"]["products"]:
                return {
                    "status": "error",
                    "message": "Product not found"
                }
            product_data = data["data"]["products"][0]
            return {
                "status": "success",
                "name": product_data["name"],
                "artikul": artikul,
                "price": product_data["salePriceU"] / 100,
                "rating": product_data.get("reviewRating", 0),
                "total_quantity": product_data.get("totalQuantity", 0)
            }
        except (KeyError, IndexError) as e:
            return {
                "status": "error",
                "message": str(e)
            }

async def update_product_data(artikul: str):
    from crud import create_product, log_task
    async with AsyncSessionLocal() as session:
        try:
            product = await create_product(session, ProductCreate(artikul=artikul))
            log_message = {
                "name": product.name,
                "price": product.price,
                "rating": product.rating,
                "total_quantity": product.total_quantity
            }
            await log_task(session, artikul, "success", str(log_message))
            
            subscription = await session.execute(
                select(Subscription).where(Subscription.artikul == artikul)
            )
            subscription = subscription.scalars().first()
            if subscription:
                subscription.last_checked_at = datetime.utcnow()
                await session.commit()
            
            logging.info(f"Request successful for artikul: {artikul}")
        except Exception as e:
            await log_task(session, artikul, "error", str(e))
            logging.error(f"Request failed for artikul: {artikul} with error: {str(e)}")
            raise

async def check_subscriptions():
    async with AsyncSessionLocal() as session:
        subscriptions = await session.execute(select(Subscription))
        subscriptions = subscriptions.scalars().all()
        successful_artikuls = []
        failed_artikuls = []
        for sub in subscriptions:
            if sub.is_active and (sub.last_checked_at + timedelta(minutes=sub.frequency_minutes) <= datetime.utcnow()):
                try:
                    await update_product_data(sub.artikul)
                    successful_artikuls.append(sub.artikul)
                except Exception:
                    failed_artikuls.append(sub.artikul)
        
        if successful_artikuls:
            logging.info(f"{len(successful_artikuls)} requests successful for artikuls: {', '.join(successful_artikuls)}")
        if failed_artikuls:
            logging.error(f"{len(failed_artikuls)} requests failed for artikuls: {', '.join(failed_artikuls)}")

def start_scheduler():
    scheduler.add_job(check_subscriptions, 'interval', minutes=1)
    scheduler.start()