from pydantic import BaseModel

class ProductCreate(BaseModel):
    artikul: str

class ProductResponse(BaseModel):
    name: str
    artikul: str
    price: float
    rating: float
    total_quantity: int

    class Config:
        orm_mode = True