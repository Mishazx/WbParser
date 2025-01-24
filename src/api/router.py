from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from crud import create_product, create_or_update_subscription
from tasks import schedule_product_updates
from db import get_db
from schemas import ProductCreate, ProductResponse, SubscriptionResponse
from auth import get_api_key
from models import ApiKey

router_product = APIRouter()

@router_product.post("/api/v1/products", response_model=ProductResponse)
async def create_product_endpoint(
    product: ProductCreate, 
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = get_api_key()
):
    try:
        create_product_data = await create_product(db, product)
        return create_product_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router_product.get("/api/v1/subscribe/{artikul}", response_model=SubscriptionResponse)
async def subscribe_to_product(
    artikul: str,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = get_api_key()
):
    try:
        subscription = await create_or_update_subscription(db, artikul)
        schedule_product_updates(artikul)
        return subscription
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
