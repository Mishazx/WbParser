from sqlalchemy.ext.asyncio import AsyncSession
from models.Product import Product

async def create_product(db: AsyncSession, artikul: str):
    product = Product(artikul=artikul)
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product
