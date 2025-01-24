from sqladmin import ModelView, Admin
from models import Product, TaskLog, ApiKey, Subscription
import secrets
import uuid
from typing import Any
from db import AsyncSessionLocal
from crud import create_api_key

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

class TaskLogAdmin(ModelView, model=TaskLog):
    column_list = [
        TaskLog.id,
        TaskLog.artikul,
        TaskLog.status,
        TaskLog.message,
        TaskLog.created_at
    ]
    column_labels = {
        TaskLog.id: "ID",
        TaskLog.artikul: "Артикул",
        TaskLog.status: "Статус",
        TaskLog.message: "Сообщение",
        TaskLog.created_at: "Время создания"
    }
    can_create = False
    can_edit = False
    can_delete = False
    column_sortable_list = [TaskLog.created_at]
    column_default_sort = ('created_at', True)

class ApiKeyAdmin(ModelView, model=ApiKey):
    column_list = [
        ApiKey.id,
        ApiKey.key,
        ApiKey.name,
        ApiKey.is_active,
        ApiKey.created_at
    ]
    column_labels = {
        ApiKey.id: "ID",
        ApiKey.key: "API Ключ",
        ApiKey.name: "Название",
        ApiKey.is_active: "Активен",
        ApiKey.created_at: "Создан"
    }
    
    form_excluded_columns = [ApiKey.key, ApiKey.created_at]
    
    can_delete = False
    can_edit = False
    can_create = False

class SubscriptionAdmin(ModelView, model=Subscription):
    column_list = [
        Subscription.id,
        Subscription.artikul,
        Subscription.is_active,
        Subscription.frequency_minutes,
        Subscription.last_checked_at
    ]
    column_labels = {
        Subscription.id: "ID",
        Subscription.artikul: "Артикул",
        Subscription.is_active: "Активен",
        Subscription.frequency_minutes: "Частота (минуты)",
        Subscription.last_checked_at: "Последняя проверка"
    }
    can_create = True
    can_edit = True
    can_delete = True
