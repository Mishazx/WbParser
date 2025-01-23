from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from crud import create_product
from db import get_db
from schemas import ProductCreate, ProductResponse

router_product = APIRouter()

@router_product.post("/api/v1/products", response_model=ProductResponse)
async def create_product_endpoint(product: ProductCreate, 
                                db: AsyncSession = Depends(get_db)):
    try:
        create_product_data = await create_product(db, product)
        return create_product_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# @router_product.get("/api/v1/products/{artikul}", response_model=ProductResponse)
# async def get_product_endpoint(artikul: str, 
#                                 db: AsyncSession = Depends(get_db)):
#     # Получаем продукт по артикулу
#     product = await get_product(db, artikul)
#     if product is None:
#         raise HTTPException(status_code=404, detail="Product not found")
#     return product

# @router_product.post("/api/v1/products", response_model=ProductResponse)
# async def create_product_endpoint(product: ProductCreate, 
#                                   db: AsyncSession = Depends(get_db)):
#     create_product_data = await create_product(db, product.artikul)
#     print(create_product_data)
#     return create_product_data

# @router_product.post("/api/v1/products", response_model=ProductResponse)
# async def create_product_endpoint(product: ProductCreate, 
#                                    db: AsyncSession = Depends(get_db)):
#     # Получаем данные о продукте с Wildberries
#     try:
#         create_product_data = await create_product(db, product)
#         return create_product_data
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))