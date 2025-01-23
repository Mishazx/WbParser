from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from crud.Product import create_product
from database.db import get_db
from schemas.Product import ProductCreate, ProductResponse

router_subscribe = APIRouter()

# @router_subscribe.post("/api/v1/products", response_class=ProductResponse)
# async def create_product_endpoint(product: ProductCreate, 
#                                   db: AsyncSession = Depends(get_db)):
#     return await create_product(db, product.artikul)