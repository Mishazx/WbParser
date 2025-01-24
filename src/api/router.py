from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, List, Optional
from sqlalchemy import select, and_, delete
from datetime import datetime
from pydantic import BaseModel

from crud import create_product, create_or_update_subscription, update_subscription_frequency, get_all_products, get_all_subscriptions
from db import get_db
from schemas import (
    ProductCreate, 
    ProductResponse, 
    SubscriptionResponse, 
    UpdateFrequencyRequest,
    ErrorResponse,
    RateLimitResponse,
    ProductPriceHistory
)
from auth import get_api_key
from models import ApiKey, Product, PriceHistory, Subscription, TaskLog, UserSubscription

router_product = APIRouter(tags=["Products"])

class SubscriptionCreate(BaseModel):
    artikul: str
    chat_id: str
    frequency_minutes: int

class UserSubscriptionResponse(BaseModel):
    chat_id: str
    artikul: str
    created_at: datetime

@router_product.post(
    "/api/v1/products", 
    response_model=Union[ProductResponse, dict],
    summary="Создать или обновить информацию о товаре",
    description="""
    Получает информацию о товаре с Wildberries по артикулу и сохраняет в базу данных.
    
    - Если товар уже существует, обновляет информацию
    - Если товар не найден на Wildberries, возвращает статус ошибки
    """,
    responses={
        200: {
            "description": "Успешное создание/обновление товара",
            "model": ProductResponse
        },
        400: {
            "description": "Неверный формат артикула",
            "model": ErrorResponse
        },
        401: {
            "description": "Неверный API ключ",
            "model": ErrorResponse
        },
        404: {
            "description": "Товар не найден",
            "model": ErrorResponse
        },
        429: {
            "description": "Превышен лимит запросов",
            "model": RateLimitResponse
        }
    }
)
async def create_product_endpoint(
    product: ProductCreate, 
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = get_api_key()
):
    create_product_data = await create_product(db, product)
    if isinstance(create_product_data, dict) and create_product_data.get("status") == "Product not found":
        raise HTTPException(
            status_code=404,
            detail={"error_code": "PRODUCT_NOT_FOUND", "detail": "Товар не найден на Wildberries"}
        )
    return create_product_data

@router_product.get(
    "/api/v1/subscribe/{artikul}", 
    response_model=SubscriptionResponse,
    summary="Подписаться на обновления товара",
    description="""
    Создает подписку на периодическое обновление информации о товаре.
    
    - Если подписка уже существует, активирует её
    - Частота обновления по умолчанию - 30 минут
    - Обновления происходят автоматически в фоновом режиме
    """,
    responses={
        200: {
            "description": "Успешная подписка",
            "model": SubscriptionResponse
        },
        400: {
            "description": "Неверный формат артикула",
            "model": ErrorResponse
        },
        401: {
            "description": "Неверный API ключ",
            "model": ErrorResponse
        },
        429: {
            "description": "Превышен лимит запросов",
            "model": RateLimitResponse
        }
    }
)
async def subscribe_to_product(
    artikul: str = Path(
        ...,
        min_length=1,
        max_length=15,
        description="Артикул товара Wildberries",
        examples=["303265098"]
    ),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = get_api_key()
):
    if not artikul.isdigit():
        raise HTTPException(
            status_code=400,
            detail={"error_code": "INVALID_ARTIKUL", "detail": "Артикул должен содержать только цифры"}
        )
    try:
        subscription = await create_or_update_subscription(db, artikul)
        return subscription
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error_code": "SUBSCRIPTION_ERROR", "detail": str(e)}
        )

@router_product.get(
    "/api/v1/products", 
    response_model=List[ProductResponse],
    summary="Получить список всех товаров",
    description="Возвращает список всех товаров, сохраненных в базе данных",
    responses={
        200: {
            "description": "Список товаров",
            "model": List[ProductResponse]
        },
        401: {
            "description": "Неверный API ключ",
            "model": ErrorResponse
        },
        429: {
            "description": "Превышен лимит запросов",
            "model": RateLimitResponse
        }
    }
)
async def get_all_products_endpoint(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество возвращаемых записей"),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = get_api_key()
):
    try:
        products = await get_all_products(db)
        return products[skip:skip + limit]
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error_code": "DATABASE_ERROR", "detail": str(e)}
        )

@router_product.put(
    "/api/v1/subscription/{artikul}/frequency",
    response_model=SubscriptionResponse,
    summary="Изменить частоту обновления подписки",
    description="""
    Изменяет частоту обновления информации для существующей подписки.
    
    - Частота указывается в минутах
    - Минимальная частота - 1 минута
    - Максимальная частота - 1440 минут (24 часа)
    """,
    responses={
        200: {
            "description": "Частота обновления изменена",
            "model": SubscriptionResponse
        },
        400: {
            "description": "Неверные параметры запроса",
            "model": ErrorResponse
        },
        401: {
            "description": "Неверный API ключ",
            "model": ErrorResponse
        },
        404: {
            "description": "Подписка не найдена",
            "model": ErrorResponse
        },
        429: {
            "description": "Превышен лимит запросов",
            "model": RateLimitResponse
        }
    }
)
async def update_subscription_frequency_endpoint(
    artikul: str = Path(
        ...,
        min_length=1,
        max_length=15,
        description="Артикул товара Wildberries",
        examples=["303265098"]
    ),
    request: UpdateFrequencyRequest = None,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = get_api_key()
):
    if not artikul.isdigit():
        raise HTTPException(
            status_code=400,
            detail={"error_code": "INVALID_ARTIKUL", "detail": "Артикул должен содержать только цифры"}
        )
    try:
        subscription = await update_subscription_frequency(db, artikul, request.frequency_minutes)
        return subscription
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "SUBSCRIPTION_NOT_FOUND", "detail": str(e)}
        )

@router_product.get(
    "/api/v1/subscriptions",
    response_model=List[SubscriptionResponse],
    summary="Получить список всех подписок",
    description="Возвращает список всех активных и неактивных подписок",
    responses={
        200: {
            "description": "Список подписок",
            "model": List[SubscriptionResponse]
        },
        401: {
            "description": "Неверный API ключ",
            "model": ErrorResponse
        },
        429: {
            "description": "Превышен лимит запросов",
            "model": RateLimitResponse
        }
    }
)
async def get_all_subscriptions_endpoint(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество возвращаемых записей"),
    active_only: bool = Query(False, description="Показывать только активные подписки"),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = get_api_key()
):
    try:
        subscriptions = await get_all_subscriptions(db)
        if active_only:
            subscriptions = [s for s in subscriptions if s.is_active]
        return subscriptions[skip:skip + limit]
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error_code": "DATABASE_ERROR", "detail": str(e)}
        )

@router_product.get(
    "/api/v1/products/{artikul}/price-history",
    response_model=ProductPriceHistory,
    summary="Получить историю цен товара",
    description="""
    Возвращает историю изменения цен товара.
    
    - Возвращает последние 100 записей
    - Сортировка от новых к старым
    - Включает информацию о количестве товара на момент записи
    """,
    responses={
        200: {
            "description": "История цен товара",
            "model": ProductPriceHistory
        },
        400: {
            "description": "Неверный формат артикула",
            "model": ErrorResponse
        },
        401: {
            "description": "Неверный API ключ",
            "model": ErrorResponse
        },
        404: {
            "description": "Товар не найден",
            "model": ErrorResponse
        },
        429: {
            "description": "Превышен лимит запросов",
            "model": RateLimitResponse
        }
    }
)
async def get_price_history(
    artikul: str = Path(
        ...,
        min_length=1,
        max_length=15,
        description="Артикул товара Wildberries",
        examples=["303265098"]
    ),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = get_api_key()
):
    if not artikul.isdigit():
        raise HTTPException(
            status_code=400,
            detail={"error_code": "INVALID_ARTIKUL", "detail": "Артикул должен содержать только цифры"}
        )

    # Получаем продукт и его историю цен
    product = await db.execute(
        select(Product).where(Product.artikul == artikul)
    )
    product = product.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "PRODUCT_NOT_FOUND", "detail": "Товар не найден"}
        )

    # Получаем историю цен, отсортированную по дате
    price_history = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.product_id == product.id)
        .order_by(PriceHistory.created_at.desc())
    )
    price_history = price_history.scalars().all()

    return ProductPriceHistory(
        artikul=product.artikul,
        name=product.name,
        history=price_history
    )

@router_product.post("/api/v1/subscriptions", response_model=UserSubscriptionResponse)
async def create_user_subscription(
    subscription: SubscriptionCreate,
    session: AsyncSession = Depends(get_db)
):
    # Проверяем существование товара
    product = await session.execute(
        select(Product).where(Product.artikul == subscription.artikul)
    )
    product = product.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Создаем или обновляем подписку
    user_sub = await session.execute(
        select(UserSubscription).where(
            and_(
                UserSubscription.chat_id == subscription.chat_id,
                UserSubscription.artikul == subscription.artikul
            )
        )
    )
    user_sub = user_sub.scalar_one_or_none()

    if not user_sub:
        user_sub = UserSubscription(
            chat_id=subscription.chat_id,
            artikul=subscription.artikul
        )
        session.add(user_sub)

    # Создаем или обновляем основную подписку
    sub = await session.execute(
        select(Subscription).where(Subscription.artikul == subscription.artikul)
    )
    sub = sub.scalar_one_or_none()

    if not sub:
        sub = Subscription(
            artikul=subscription.artikul,
            frequency_minutes=subscription.frequency_minutes
        )
        session.add(sub)
    else:
        sub.frequency_minutes = subscription.frequency_minutes
        sub.is_active = True

    await session.commit()
    return user_sub

@router_product.get("/api/v1/subscriptions/{artikul}/users", response_model=List[UserSubscriptionResponse])
async def get_subscription_users(
    artikul: str = Path(..., description="Артикул товара"),
    session: AsyncSession = Depends(get_db)
):
    result = await session.execute(
        select(UserSubscription).where(UserSubscription.artikul == artikul)
    )
    subscriptions = result.scalars().all()
    return subscriptions

@router_product.delete("/api/v1/subscriptions/{artikul}/users/{chat_id}")
async def delete_user_subscription(
    artikul: str = Path(..., description="Артикул товара"),
    chat_id: str = Path(..., description="ID чата пользователя"),
    session: AsyncSession = Depends(get_db)
):
    result = await session.execute(
        delete(UserSubscription).where(
            and_(
                UserSubscription.artikul == artikul,
                UserSubscription.chat_id == chat_id
            )
        )
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Проверяем, остались ли еще подписчики
    remaining = await session.execute(
        select(UserSubscription).where(UserSubscription.artikul == artikul)
    )
    if not remaining.first():
        # Если подписчиков не осталось, деактивируем основную подписку
        sub = await session.execute(
            select(Subscription).where(Subscription.artikul == artikul)
        )
        sub = sub.scalar_one_or_none()
        if sub:
            sub.is_active = False

    await session.commit()
    return {"status": "success"}

@router_product.get("/api/v1/subscriptions/user/{chat_id}", response_model=List[UserSubscriptionResponse])
async def get_user_subscriptions(
    chat_id: str = Path(..., description="ID чата пользователя"),
    session: AsyncSession = Depends(get_db)
):
    """
    Получить список всех подписок пользователя
    """
    result = await session.execute(
        select(UserSubscription)
        .where(UserSubscription.chat_id == chat_id)
        .order_by(UserSubscription.created_at.desc())
    )
    subscriptions = result.scalars().all()
    return subscriptions
