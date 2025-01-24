from fastapi import APIRouter, HTTPException, Depends
from aiogram import Bot
from notifications import notify_price_change, notify_quantity_change, PriceNotification, QuantityNotification
from typing import Annotated

router = APIRouter(
    prefix="/api/v1",
    tags=["notifications"],
    responses={
        500: {"description": "Внутренняя ошибка сервера"},
    }
)

# Глобальная переменная для хранения экземпляра бота
_bot: Bot | None = None

def set_bot(bot: Bot):
    """Установить экземпляр бота для использования в маршрутах"""
    global _bot
    _bot = bot

async def get_bot() -> Bot:
    """Получить экземпляр бота"""
    if _bot is None:
        raise HTTPException(
            status_code=500,
            detail="Bot instance not initialized"
        )
    return _bot

@router.post(
    "/notify/price-change", 
    summary="Отправить уведомление об изменении цены",
    description="Отправляет уведомления всем подписчикам об изменении цены товара",
    response_description="Результат отправки уведомлений",
    responses={
        200: {"description": "Уведомления успешно отправлены"},
        500: {"description": "Ошибка при отправке уведомлений"}
    }
)
async def price_change_notification(
    notification: PriceNotification,
    bot: Annotated[Bot, Depends(get_bot)]
):
    """Отправляет уведомления об изменении цены подписчикам"""
    return await notify_price_change(notification, bot)

@router.post(
    "/notify/quantity-change",
    summary="Отправить уведомление об изменении количества",
    description="Отправляет уведомления всем подписчикам об изменении количества товара",
    response_description="Результат отправки уведомлений",
    responses={
        200: {"description": "Уведомления успешно отправлены"},
        500: {"description": "Ошибка при отправке уведомлений"}
    }
)
async def quantity_change_notification(
    notification: QuantityNotification,
    bot: Annotated[Bot, Depends(get_bot)]
):
    """Отправляет уведомления об изменении количества подписчикам"""
    return await notify_quantity_change(notification, bot)
