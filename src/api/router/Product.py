from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from crud.Product import create_product
from database.db import get_db
from schemas.Product import ProductCreate, ProductResponse

router_product = APIRouter()

@router_product.post("/api/v1/products", response_model=ProductResponse)
async def create_product_endpoint(product: ProductCreate, 
                                  db: AsyncSession = Depends(get_db)):
    create_product_data = await create_product(db, product.artikul)
    print(create_product_data)
    return create_product_data
