from pydantic import BaseModel, Field
from typing import List

class SubscriptionCreate(BaseModel):
    """Модель для создания подписки"""
    artikul: str = Field(..., description="Артикул товара на Wildberries", example="123456")
    chat_id: str = Field(..., description="ID чата пользователя в Telegram", example="123456789")
    frequency_minutes: int = Field(
        ..., 
        description="Частота проверки цены в минутах", 
        example=60,
        ge=1,
        le=1440
    )

class UserSubscription(BaseModel):
    """Модель подписки пользователя"""
    artikul: str = Field(..., description="Артикул товара", example="123456")
    frequency_minutes: int = Field(..., description="Частота проверки в минутах", example=60)
    last_checked_at: str = Field(..., description="Время последней проверки", example="2024-03-14T12:00:00")
    created_at: str = Field(..., description="Время создания подписки", example="2024-03-14T10:00:00")

class UserSubscriptionResponse(BaseModel):
    """Модель ответа со списком подписок пользователя"""
    subscriptions: List[UserSubscription] = Field(
        ..., 
        description="Список активных подписок пользователя"
    ) 