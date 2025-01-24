from pydantic import BaseModel, ConfigDict

class ProductCreate(BaseModel):
    artikul: str

class ProductResponse(BaseModel):
    name: str
    artikul: str
    price: float
    rating: float
    total_quantity: int

    model_config = ConfigDict(from_attributes=True)

class SubscriptionResponse(BaseModel):
    artikul: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)