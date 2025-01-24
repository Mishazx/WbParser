import logging
import aiohttp
from fastapi import HTTPException
from pydantic import BaseModel
from typing import List

from config import API_URL, HEADERS, logger

class PriceNotification(BaseModel):
    artikul: str
    old_price: float
    new_price: float
    product_name: str

class QuantityNotification(BaseModel):
    artikul: str
    old_quantity: int
    new_quantity: int
    product_name: str

async def notify_price_change(notification: PriceNotification, bot):
    """Отправляет уведомления об изменении цены подписчикам"""
    logger.info(f"Received price change notification for artikul {notification.artikul}")
    
    async with aiohttp.ClientSession() as session:
        url = f"{API_URL}/subscriptions/{notification.artikul}/users"
        logger.info(f"Fetching subscribers from: {url}")
        
        async with session.get(url, headers=HEADERS) as response:
            if response.status != 200:
                logger.error(f"Failed to get subscribers: HTTP {response.status}")
                raise HTTPException(status_code=500, detail="Failed to get subscribers")
            
            subscribers = await response.json()
            logger.info(f"Found {len(subscribers)} subscribers")
            
            notifications_sent = 0
            for subscriber in subscribers:
                try:
                    chat_id = subscriber['chat_id']
                    price_diff = notification.new_price - notification.old_price
                    price_change = "снизилась" if price_diff < 0 else "повысилась"
                    percent_change = abs(price_diff / notification.old_price * 100)
                    
                    message = (
                        f"💰 Изменение цены на {notification.product_name}!\n\n"
                        f"Артикул: {notification.artikul}\n"
                        f"Старая цена: {notification.old_price:,.2f} ₽\n"
                        f"Новая цена: {notification.new_price:,.2f} ₽\n"
                        f"Цена {price_change} на {abs(price_diff):,.2f} ₽ ({percent_change:.1f}%)\n\n"
                        f"🔗 https://www.wildberries.ru/catalog/{notification.artikul}/detail.aspx"
                    )
                    
                    logger.info(f"Sending notification to chat_id: {chat_id}")
                    await bot.send_message(chat_id=chat_id, text=message)
                    notifications_sent += 1
                    logger.info(f"Successfully sent notification to chat_id: {chat_id}")
                except Exception as e:
                    logger.error(f"Failed to send notification to {chat_id}: {str(e)}")
            
            logger.info(f"Successfully sent {notifications_sent} notifications")
            return {"success": True, "notifications_sent": notifications_sent}

async def notify_quantity_change(notification: QuantityNotification, bot):
    """Отправляет уведомления об изменении количества подписчикам"""
    async with aiohttp.ClientSession() as session:
        url = f"{API_URL}/subscriptions/{notification.artikul}/users"
        async with session.get(url, headers=HEADERS) as response:
            if response.status != 200:
                logger.error(f"Failed to get subscribers: HTTP {response.status}")
                raise HTTPException(status_code=500, detail="Failed to get subscribers")
            
            subscribers = await response.json()
            
            notifications_sent = 0
            for subscriber in subscribers:
                try:
                    chat_id = subscriber['chat_id']
                    quantity_diff = notification.new_quantity - notification.old_quantity
                    quantity_change = "увеличилось" if quantity_diff > 0 else "уменьшилось"
                    percent_change = abs(quantity_diff / notification.old_quantity * 100) if notification.old_quantity > 0 else 100
                    
                    message = (
                        f"📦 Изменение количества товара {notification.product_name}!\n\n"
                        f"Артикул: {notification.artikul}\n"
                        f"Старое количество: {notification.old_quantity:,} шт.\n"
                        f"Новое количество: {notification.new_quantity:,} шт.\n"
                        f"Количество {quantity_change} на {abs(quantity_diff):,} шт. ({percent_change:.1f}%)\n\n"
                        f"🔗 https://www.wildberries.ru/catalog/{notification.artikul}/detail.aspx"
                    )
                    
                    await bot.send_message(chat_id=chat_id, text=message)
                    notifications_sent += 1
                    logger.info(f"Quantity change notification sent to {chat_id}")
                except Exception as e:
                    logger.error(f"Failed to send notification to {chat_id}: {e}")
            
            return {"success": True, "notifications_sent": notifications_sent} 