from sqladmin import ModelView, Admin
from models import Product

class ProductAdmin(ModelView, model=Product):
    column_list = [
        Product.id, 
        Product.artikul, 
        Product.name, 
        Product.price,
        Product.rating,
        Product.total_quantity
    ]
    column_labels = {
        Product.id: "ID",
        Product.artikul: "Артикул",
        Product.name: "Название",
        Product.price: "Цена",
        Product.rating: "Рейтинг",
        Product.total_quantity: "Количество"
    }
