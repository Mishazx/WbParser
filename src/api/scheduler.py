from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, update
from datetime import datetime, timedelta
import logging
import aiohttp
from models import Subscription, Product, TaskLog
from db import AsyncSessionLocal
import os
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)

BOT_API_URL = os.getenv('BOT_API_URL', 'http://bot:8889')

async def notify_price_change(artikul: str, old_price: float, new_price: float, product_name: str):
    """Отправляет запрос в API бота для уведомления об изменении цены"""
    logger.info(f"Attempting to send price change notification to {BOT_API_URL}")
    logger.info(f"Price change details: artikul={artikul}, old_price={old_price}, new_price={new_price}")
    
    try:
        async with aiohttp.ClientSession() as client:
            url = f"{BOT_API_URL}/api/v1/notify/price-change"
            payload = {
                "artikul": artikul,
                "old_price": old_price,
                "new_price": new_price,
                "product_name": product_name
            }
            logger.info(f"Sending POST request to {url} with payload: {payload}")
            
            async with client.post(url, json=payload) as response:
                response_text = await response.text()
                logger.info(f"Received response: Status={response.status}, Body={response_text}")
                
                if response.status != 200:
                    logger.error(f"Failed to send notification request: HTTP {response.status}")
                    return False
                
                result = await response.json()
                logger.info(f"Notification request sent successfully. Notifications sent: {result.get('notifications_sent', 0)}")
                return True
    except Exception as e:
        logger.error(f"Error sending notification request: {str(e)}")
        return False

async def notify_quantity_change(artikul: str, old_quantity: int, new_quantity: int, product_name: str):
    """Отправляет запрос в API бота для уведомления об изменении количества"""
    logger.info(f"Attempting to send quantity change notification to {BOT_API_URL}")
    logger.info(f"Quantity change details: artikul={artikul}, old_quantity={old_quantity}, new_quantity={new_quantity}")
    
    try:
        async with aiohttp.ClientSession() as client:
            url = f"{BOT_API_URL}/api/v1/notify/quantity-change"
            payload = {
                "artikul": artikul,
                "old_quantity": old_quantity,
                "new_quantity": new_quantity,
                "product_name": product_name
            }
            logger.info(f"Sending POST request to {url} with payload: {payload}")
            
            async with client.post(url, json=payload) as response:
                response_text = await response.text()
                logger.info(f"Received response: Status={response.status}, Body={response_text}")
                
                if response.status != 200:
                    logger.error(f"Failed to send quantity notification request: HTTP {response.status}")
                    return False
                
                result = await response.json()
                logger.info(f"Quantity notification request sent successfully. Notifications sent: {result.get('notifications_sent', 0)}")
                return True
    except Exception as e:
        logger.error(f"Error sending quantity notification request: {str(e)}")
        return False

async def update_product_data(artikul: str, session) -> bool:
    """Обновляет данные о товаре и создает запись в логе"""
    logger.info(f"Starting update for product {artikul}")
    try:
        # Получаем текущие данные о товаре
        current_product = await session.execute(
            select(Product).where(Product.artikul == artikul)
        )
        current_product = current_product.scalar_one_or_none()
        
        if not current_product:
            error_msg = f"Product {artikul} not found in database"
            logger.error(error_msg)
            await create_task_log(session, artikul, "error", error_msg)
            return False
            
        old_price = current_product.price
        old_quantity = current_product.total_quantity
        
        async with aiohttp.ClientSession() as client:
            url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=27&nm={artikul}"
            logger.info(f"Sending request to: {url}")
            async with client.get(url) as response:
                if response.status != 200:
                    error_msg = f"Failed to fetch data: HTTP {response.status}"
                    logger.error(error_msg)
                    await create_task_log(session, artikul, "error", error_msg)
                    return False

                data = await response.json()
                products = data.get('data', {}).get('products', [])
                
                if not products:
                    error_msg = "Product not found"
                    logger.error(f"{error_msg} for artikul {artikul}")
                    await create_task_log(session, artikul, "error", error_msg)
                    return False

                product_data = products[0]
                new_price = product_data.get('salePriceU', 0) / 100
                new_rating = product_data.get('rating', 0)
                new_quantity = product_data.get('sizes', [{}])[0].get('stocks', [{}])[0].get('qty', 0)
                
                logger.info(f"Received data for {artikul}: price={new_price}, rating={new_rating}, quantity={new_quantity}")
                
                # Проверяем изменение цены
                if old_price != new_price:
                    logger.info(f"Price changed for {artikul}: {old_price} -> {new_price}")
                    # Отправляем запрос в API бота для уведомления подписчиков
                    await notify_price_change(
                        artikul=artikul,
                        old_price=old_price,
                        new_price=new_price,
                        product_name=current_product.name
                    )
                
                # Проверяем изменение количества
                if old_quantity != new_quantity:
                    logger.info(f"Quantity changed for {artikul}: {old_quantity} -> {new_quantity}")
                    # Отправляем запрос в API бота для уведомления подписчиков
                    await notify_quantity_change(
                        artikul=artikul,
                        old_quantity=old_quantity,
                        new_quantity=new_quantity,
                        product_name=current_product.name
                    )
                
                # Обновляем информацию о товаре
                stmt = update(Product).where(Product.artikul == artikul).values(
                    price=new_price,
                    rating=new_rating,
                    total_quantity=new_quantity,
                    updated_at=datetime.utcnow()
                )
                await session.execute(stmt)
                await session.commit()
                
                success_msg = f"Data updated successfully: price={new_price}, rating={new_rating}, quantity={new_quantity}"
                logger.info(success_msg)
                await create_task_log(session, artikul, "success", success_msg)
                return True

    except Exception as e:
        error_msg = f"Error updating product {artikul}: {str(e)}"
        logger.error(error_msg)
        await create_task_log(session, artikul, "error", error_msg)
        return False

async def create_task_log(session, artikul: str, status: str, message: str):
    """Создает запись в логе задач"""
    logger.info(f"Creating task log for {artikul}: {status} - {message}")
    task_log = TaskLog(
        artikul=artikul,
        status=status,
        message=message
    )
    session.add(task_log)
    try:
        await session.commit()
        logger.info(f"Task log created successfully for {artikul}")
    except Exception as e:
        logger.error(f"Error creating task log for {artikul}: {e}")
        await session.rollback()

async def check_subscriptions():
    """Проверяет все активные подписки и обновляет данные при необходимости"""
    logger.info("\n=== Starting subscription check ===")
    async with AsyncSessionLocal() as session:
        try:
            # Получаем все активные подписки
            now = datetime.utcnow()
            query = select(Subscription).where(
                Subscription.is_active == True
            )
            result = await session.execute(query)
            all_subscriptions = result.scalars().all()
            
            logger.info(f"Total active subscriptions found: {len(all_subscriptions)}")
            
            # Фильтруем подписки, которые нужно обновить
            subscriptions_to_update = []
            for sub in all_subscriptions:
                time_since_last_check = now - sub.last_checked_at
                minutes_since_last_check = time_since_last_check.total_seconds() / 60
                should_update = minutes_since_last_check >= sub.frequency_minutes
                
                logger.info(
                    f"Subscription {sub.artikul}:"
                    f"\n    - Last checked: {sub.last_checked_at}"
                    f"\n    - Minutes since last check: {minutes_since_last_check:.1f}"
                    f"\n    - Update frequency: {sub.frequency_minutes} minutes"
                    f"\n    - Needs update: {should_update}"
                )
                
                if should_update:
                    subscriptions_to_update.append(sub)
            
            logger.info(f"\nFound {len(subscriptions_to_update)} subscriptions that need updating")

            for subscription in subscriptions_to_update:
                logger.info(f"\nProcessing subscription for artikul {subscription.artikul}")
                logger.info(f"Update frequency: {subscription.frequency_minutes} minutes")
                logger.info(f"Last checked at: {subscription.last_checked_at}")
                
                # Обновляем данные о товаре
                success = await update_product_data(subscription.artikul, session)
                
                if success:
                    # Обновляем время последней проверки
                    old_check_time = subscription.last_checked_at
                    subscription.last_checked_at = now
                    await session.commit()
                    logger.info(
                        f"Successfully updated subscription for artikul {subscription.artikul}"
                        f"\n    - Previous check time: {old_check_time}"
                        f"\n    - New check time: {now}"
                    )
                else:
                    logger.error(f"Failed to update subscription for artikul {subscription.artikul}")

            logger.info("\n=== Subscription check completed ===")

        except Exception as e:
            logger.error(f"Error in check_subscriptions: {e}")
            await session.rollback()

def start_scheduler():
    """Запускает планировщик задач"""
    try:
        logger.info("=== Initializing scheduler ===")
        scheduler = AsyncIOScheduler()
        
        # Добавляем задачу проверки подписок каждую минуту
        scheduler.add_job(
            check_subscriptions,
            trigger=IntervalTrigger(minutes=1),
            id='check_subscriptions',
            name='Check active subscriptions and update product data',
            replace_existing=True,
            misfire_grace_time=None  # Всегда выполнять пропущенные задачи
        )
        
        scheduler.start()
        logger.info("=== Scheduler started successfully! ===")
        logger.info("Scheduled jobs:")
        for job in scheduler.get_jobs():
            logger.info(f"- {job.name}: runs every {job.trigger.interval.seconds} seconds")
        
        return scheduler
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise 