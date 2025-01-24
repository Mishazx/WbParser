from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from datetime import datetime
from db import Base
import secrets
from sqlalchemy import event

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    artikul = Column(String, unique=True, index=True)
    price = Column(Float)
    rating = Column(Float)
    total_quantity = Column(Integer)

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    artikul = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    frequency_minutes = Column(Integer, default=30)
    last_checked_at = Column(DateTime, default=datetime.utcnow)

class TaskLog(Base):
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True)
    artikul = Column(String, index=True)
    status = Column(String)  # success/error
    message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Слушатель события для генерации ключа перед вставкой
@event.listens_for(ApiKey, 'before_insert')
def generate_api_key(mapper, connection, target):
    if not target.key:
        target.key = secrets.token_urlsafe(32)
