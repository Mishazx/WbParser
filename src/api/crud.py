from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Product, Subscription, TaskLog, ApiKey
from schemas import ProductCreate
from tasks import fetch_product_data
import secrets


async def create_product(session: AsyncSession, product: ProductCreate):
    product_data = await fetch_product_data(product.artikul)
    if product_data.get("status") == "error":
        return {"status": "Product not found"}
    
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

async def update_subscription_frequency(session: AsyncSession, artikul: str, frequency_minutes: int) -> Subscription:
    subscription = await session.execute(
        select(Subscription).where(Subscription.artikul == artikul)
    )
    subscription = subscription.scalars().first()
    
    if not subscription:
        raise Exception("Subscription not found")
    
    subscription.frequency_minutes = frequency_minutes
    await session.commit()
    await session.refresh(subscription)
    return subscription

async def get_active_subscriptions(session: AsyncSession):
    result = await session.execute(
        select(Subscription).where(Subscription.is_active == True)
    )
    return result.scalars().all()

async def get_all_products(session: AsyncSession):
    result = await session.execute(select(Product))
    return result.scalars().all()

async def get_all_subscriptions(session: AsyncSession):
    result = await session.execute(select(Subscription))
    return result.scalars().all()

async def log_task(session: AsyncSession, artikul: str, status: str, message: str = None):
    log_entry = TaskLog(
        artikul=artikul,
        status=status,
        message=message
    )
    session.add(log_entry)
    await session.commit()

async def create_api_key(session: AsyncSession, name: str) -> ApiKey:
    """Создает новый API ключ"""
    api_key = ApiKey(
        key=secrets.token_urlsafe(32),
        name=name,
        is_active=True
    )
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)
    return api_key