from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, List

from crud import create_product, create_or_update_subscription, update_subscription_frequency, get_all_products, get_all_subscriptions
from db import get_db
from schemas import ProductCreate, ProductResponse, SubscriptionResponse, UpdateFrequencyRequest
from auth import get_api_key
from models import ApiKey

router_product = APIRouter()

@router_product.post("/api/v1/products", response_model=Union[ProductResponse, dict])
async def create_product_endpoint(
    product: ProductCreate, 
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = get_api_key()
):
    create_product_data = await create_product(db, product)
    if isinstance(create_product_data, dict) and create_product_data.get("status") == "Product not found":
        return {"status": "Product not found"}
    return create_product_data

@router_product.get("/api/v1/subscribe/{artikul}", response_model=SubscriptionResponse)
async def subscribe_to_product(
    artikul: str,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = get_api_key()
):
    try:
        subscription = await create_or_update_subscription(db, artikul)
        return subscription
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router_product.put("/api/v1/subscription/{artikul}/frequency", response_model=SubscriptionResponse)
async def update_subscription_frequency_endpoint(
    artikul: str,
    request: UpdateFrequencyRequest,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = get_api_key()
):
    try:
        subscription = await update_subscription_frequency(db, artikul, request.frequency_minutes)
        return subscription
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router_product.get("/api/v1/products", response_model=List[ProductResponse])
async def get_all_products_endpoint(
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = get_api_key()
):
    try:
        products = await get_all_products(db)
        return products
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router_product.get("/api/v1/subscriptions", response_model=List[SubscriptionResponse])
async def get_all_subscriptions_endpoint(
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = get_api_key()
):
    try:
        subscriptions = await get_all_subscriptions(db)
        return subscriptions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
