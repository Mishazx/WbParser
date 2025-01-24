from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List
import re
from datetime import datetime

class ProductCreate(BaseModel):
    artikul: str = Field(
        ...,
        min_length=1,
        max_length=15,
        description="Артикул товара Wildberries (только цифры)",
        examples=["303265098"]
    )

    @field_validator('artikul')
    @classmethod
    def validate_artikul(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("Артикул должен содержать только цифры")
        return v

class ProductResponse(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Название товара")
    artikul: str = Field(..., min_length=1, max_length=15, description="Артикул товара Wildberries (только цифры)")
    price: float = Field(..., ge=0, description="Цена товара в рублях")
    rating: float = Field(..., ge=0, le=5, description="Рейтинг товара от 0 до 5")
    total_quantity: int = Field(..., ge=0, description="Общее количество товара на складах")

    model_config = ConfigDict(from_attributes=True)

    @field_validator('price')
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v > 10000000:  # Максимальная цена 10 млн рублей
            raise ValueError("Цена не может быть больше 10,000,000 рублей")
        return round(v, 2)  # Округляем до копеек

class SubscriptionCreate(BaseModel):
    artikul: str
    chat_id: str
    frequency_minutes: int

class UserSubscriptionResponse(BaseModel):
    chat_id: str
    artikul: str
    created_at: datetime

class SubscriptionResponse(BaseModel):
    artikul: str = Field(..., min_length=1, max_length=15)
    is_active: bool = Field(
        ...,
        description="Статус подписки (активна/неактивна)"
    )
    frequency_minutes: Optional[int] = Field(
        default=30,
        ge=1,
        le=1440,
        description="Частота обновления в минутах (от 1 до 1440)"
    )
    last_checked_at: Optional[str] = Field(
        None,
        description="Время последней проверки в формате ISO 8601"
    )

    model_config = ConfigDict(from_attributes=True)

    @field_validator('artikul')
    @classmethod
    def validate_artikul(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("Артикул должен содержать только цифры")
        return v

class UpdateFrequencyRequest(BaseModel):
    frequency_minutes: int = Field(
        ...,
        ge=1,
        le=1440,
        description="Частота обновления в минутах (от 1 до 24 часов)"
    )

    @field_validator('frequency_minutes')
    @classmethod
    def validate_frequency(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Частота обновления не может быть меньше 1 минуты")
        if v > 1440:
            raise ValueError("Частота обновления не может быть больше 24 часов (1440 минут)")
        return v

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Описание ошибки")
    error_code: Optional[str] = Field(None, description="Код ошибки")
    
class RateLimitResponse(BaseModel):
    detail: dict = Field(..., description="Информация о превышении лимита запросов")
    wait_seconds: float = Field(..., description="Время ожидания до следующего запроса")

class PriceHistoryResponse(BaseModel):
    price: float = Field(..., ge=0, description="Цена товара в рублях")
    total_quantity: int = Field(..., ge=0, description="Количество товара на момент записи")
    created_at: datetime = Field(..., description="Дата и время записи")

    model_config = ConfigDict(from_attributes=True)

    @field_validator('price')
    @classmethod
    def validate_price(cls, v: float) -> float:
        return round(v, 2)  # Округляем до копеек

class ProductPriceHistory(BaseModel):
    artikul: str = Field(..., description="Артикул товара")
    name: str = Field(..., description="Название товара")
    history: List[PriceHistoryResponse] = Field(..., description="История изменения цен")

    model_config = ConfigDict(from_attributes=True)