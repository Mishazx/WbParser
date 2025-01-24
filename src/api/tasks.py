from apscheduler.schedulers.asyncio import AsyncIOScheduler
import httpx
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, delete, and_

from schemas import ProductCreate
from db import AsyncSessionLocal
from models import Subscription, TaskLog, PriceHistory
from exception import WildberriesAPIError, WildberriesResponseError, WildberriesTimeoutError, ProductNotFoundError

# Настройка логгера
logging.basicConfig(
    filename='subscription_updates.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

scheduler = AsyncIOScheduler()

async def cleanup_old_data():
    """Очистка старых данных"""
    async with AsyncSessionLocal() as session:
        try:
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            await session.execute(
                delete(TaskLog).where(TaskLog.created_at < thirty_days_ago)
            )

            price_history = await session.execute(
                select(PriceHistory.product_id, PriceHistory.id)
                .order_by(PriceHistory.product_id, PriceHistory.created_at.desc())
            )
            
            history_groups = {}
            for product_id, history_id in price_history.fetchall():
                if product_id not in history_groups:
                    history_groups[product_id] = []
                history_groups[product_id].append(history_id)

            for product_id, history_ids in history_groups.items():
                if len(history_ids) > 100:
                    ids_to_delete = history_ids[100:]
                    await session.execute(
                        delete(PriceHistory).where(PriceHistory.id.in_(ids_to_delete))
                    )

            await session.commit()
            logging.info("Cleanup task completed successfully")
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")
            await session.rollback()

async def fetch_product_data(artikul: str) -> dict:
    timeout = httpx.Timeout(10.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(
                f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={artikul}")
            
            if response.status_code == 404:
                raise ProductNotFoundError(f"Product with artikul {artikul} not found")
            elif response.status_code != 200:
                raise WildberriesResponseError(f"API returned status code {response.status_code}")
            
            data = response.json()
            
            if not data.get("data", {}).get("products"):
                raise ProductNotFoundError(f"Product with artikul {artikul} not found in response")
            
            product_data = data["data"]["products"][0]
            return {
                "status": "success",
                "name": product_data["name"],
                "artikul": artikul,
                "price": product_data["salePriceU"] / 100,
                "rating": product_data.get("reviewRating", 0),
                "total_quantity": product_data.get("totalQuantity", 0)
            }
            
        except httpx.TimeoutException:
            raise WildberriesTimeoutError(f"Timeout while fetching data for artikul {artikul}")
        except httpx.RequestError as e:
            raise WildberriesResponseError(f"Request failed: {str(e)}")
        except (KeyError, IndexError) as e:
            raise WildberriesResponseError(f"Invalid response format: {str(e)}")
        except Exception as e:
            raise WildberriesResponseError(f"Unexpected error: {str(e)}")

async def update_product_data(artikul: str):
    from crud import create_product, log_task
    async with AsyncSessionLocal() as session:
        try:
            product = await create_product(session, ProductCreate(artikul=artikul))
            if isinstance(product, dict) and product.get("status") == "Product not found":
                await log_task(session, artikul, "error", "Product not found")
                return
                
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
        except WildberriesAPIError as e:
            await log_task(session, artikul, "error", str(e))
            logging.error(f"Wildberries API error for artikul {artikul}: {str(e)}")
        except Exception as e:
            await log_task(session, artikul, "error", str(e))
            logging.error(f"Request failed for artikul: {artikul} with error: {str(e)}")

async def check_subscriptions():
    async with AsyncSessionLocal() as session:
        subscriptions = await session.execute(
            select(Subscription).where(
                and_(
                    Subscription.is_active == True,
                    Subscription.last_checked_at + timedelta(minutes=Subscription.frequency_minutes) <= datetime.utcnow()
                )
            )
        )
        subscriptions = subscriptions.scalars().all()
        successful_artikuls = []
        failed_artikuls = []
        
        for sub in subscriptions:
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
    scheduler.add_job(cleanup_old_data, 'cron', hour=3)  # Запуск очистки каждый день в 3 часа ночи
    scheduler.start()