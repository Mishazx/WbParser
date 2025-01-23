from sqlalchemy import Column, Integer, String, Float
from database.db import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    artikul = Column(String, unique=True, index=True)
    price = Column(Float)
    rating = Column(Float)
    total_quantity = Column(Integer)
