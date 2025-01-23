from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Product
from schemas import ProductCreate
from tasks import fetch_product_data


async def create_product(session: AsyncSession, product: ProductCreate):
    product_data = await fetch_product_data(product.artikul)
    
    existing_product = await session.execute(
        select(Product).where(Product.artikul == product.artikul)
    )
    existing_product = existing_product.scalars().first()
    
    if existing_product:
        existing_product.name = product_data['name']
        existing_product.price = product_data['price']
        existing_product.rating = product_data['rating']
        existing_product.total_quantity = product_data['total_quantity']
        await session.commit()
        await session.refresh(existing_product)
        return existing_product
    else:
        db_product = Product(
            artikul=product.artikul,
            name=product_data['name'],
            price=product_data['price'],
            rating=product_data['rating'],
            total_quantity=product_data['total_quantity']
        )
        session.add(db_product)
        await session.commit()
        await session.refresh(db_product)
        return db_product