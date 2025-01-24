from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Product, Subscription, TaskLog
from schemas import ProductCreate
from tasks import fetch_product_data


async def create_product(session: AsyncSession, product: ProductCreate):
    try:
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
    except Exception as e:
        raise Exception(f"Failed to create/update product: {str(e)}")

async def create_or_update_subscription(session: AsyncSession, artikul: str) -> Subscription:
    existing_sub = await session.execute(
        select(Subscription).where(Subscription.artikul == artikul)
    )
    existing_sub = existing_sub.scalars().first()
    
    if existing_sub:
        existing_sub.is_active = True
        await session.commit()
        return existing_sub
    
    subscription = Subscription(artikul=artikul, is_active=True)
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription)
    return subscription

async def get_active_subscriptions(session: AsyncSession):
    result = await session.execute(
        select(Subscription).where(Subscription.is_active == True)
    )
    return result.scalars().all()

async def log_task(session: AsyncSession, artikul: str, status: str, message: str = None):
    log_entry = TaskLog(
        artikul=artikul,
        status=status,
        message=message
    )
    session.add(log_entry)
    await session.commit()