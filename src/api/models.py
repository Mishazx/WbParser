from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Index, ForeignKey, inspect, event
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base
import secrets

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    artikul = Column(String, unique=True, index=True)
    price = Column(Float)
    rating = Column(Float, index=True)
    total_quantity = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_price_rating', 'price', 'rating'),
    )

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'))
    price = Column(Float, nullable=False)
    total_quantity = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="price_history")

    __table_args__ = (
        Index('idx_price_history_date', 'created_at'),
        Index('idx_price_history_product', 'product_id', 'created_at'),
    )

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    artikul = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    frequency_minutes = Column(Integer, default=30)
    last_checked_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_active_subscriptions', 'is_active', 'last_checked_at'),
    )

class TaskLog(Base):
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True)
    artikul = Column(String, index=True)
    status = Column(String)  # success/error
    message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_task_logs_date_status', 'created_at', 'status'),
    )

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_active_api_keys', 'is_active', 'key'),
    )

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True)
    chat_id = Column(String, nullable=False)
    artikul = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_user_subscriptions', 'chat_id', 'artikul', unique=True),
    )

@event.listens_for(ApiKey, 'before_insert')
def generate_api_key(mapper, connection, target):
    if not target.key:
        target.key = secrets.token_urlsafe(32)

@event.listens_for(Product, 'after_update')
def track_price_changes(mapper, connection, target):
    """Отслеживает изменения цены товара и создает запись в истории"""
    state = inspect(target)
    
    if state.attrs.price.history.has_changes():
        old_price = state.attrs.price.history.deleted[0] if state.attrs.price.history.deleted else None
        new_price = target.price
        
        if old_price is not None and old_price != new_price:
            connection.execute(
                PriceHistory.__table__.insert().values(
                    product_id=target.id,
                    price=new_price,
                    total_quantity=target.total_quantity
                )
            )
