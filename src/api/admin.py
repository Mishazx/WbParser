from sqladmin import ModelView
from models import Product, PriceHistory, Subscription, TaskLog, ApiKey, UserSubscription

class ProductAdmin(ModelView, model=Product):
    column_list = [
        Product.id,
        Product.name,
        Product.artikul,
        Product.price,
        Product.rating,
        Product.total_quantity,
        Product.created_at,
        Product.updated_at
    ]
    column_searchable_list = [Product.name, Product.artikul]
    column_sortable_list = [Product.id, Product.price, Product.rating, Product.total_quantity]
    column_default_sort = ("updated_at", True)
    name = "Товар"
    name_plural = "Товары"
    icon = "fa-shopping-cart"
    can_create = False
    can_edit = False
    can_delete = False

class PriceHistoryAdmin(ModelView, model=PriceHistory):
    column_list = [
        PriceHistory.id,
        PriceHistory.product_id,
        PriceHistory.price,
        PriceHistory.total_quantity,
        PriceHistory.created_at
    ]
    column_sortable_list = [PriceHistory.id, PriceHistory.price, PriceHistory.created_at]
    column_default_sort = ("created_at", True)
    name = "История цен"
    name_plural = "История цен"
    icon = "fa-history"
    can_create = False
    can_edit = False
    can_delete = False

class SubscriptionAdmin(ModelView, model=Subscription):
    column_list = [
        Subscription.id,
        Subscription.artikul,
        Subscription.is_active,
        Subscription.frequency_minutes,
        Subscription.last_checked_at,
        Subscription.created_at
    ]
    column_searchable_list = [Subscription.artikul]
    column_sortable_list = [Subscription.id, Subscription.last_checked_at]
    column_default_sort = ("created_at", True)
    name = "Подписка"
    name_plural = "Подписки"
    icon = "fa-bell"
    can_create = False
    can_edit = False
    can_delete = False

class TaskLogAdmin(ModelView, model=TaskLog):
    column_list = [
        TaskLog.id,
        TaskLog.artikul,
        TaskLog.status,
        TaskLog.message,
        TaskLog.created_at
    ]
    column_searchable_list = [TaskLog.artikul, TaskLog.status]
    column_sortable_list = [TaskLog.id, TaskLog.created_at]
    column_default_sort = ("created_at", True)
    name = "Лог задач"
    name_plural = "Логи задач"
    icon = "fa-list"
    can_create = False
    can_edit = False
    can_delete = False

class ApiKeyAdmin(ModelView, model=ApiKey):
    column_list = [
        ApiKey.id,
        ApiKey.key,
        ApiKey.name,
        ApiKey.is_active,
        ApiKey.created_at
    ]
    column_searchable_list = [ApiKey.name]
    column_sortable_list = [ApiKey.id, ApiKey.created_at]
    column_default_sort = ("created_at", True)
    name = "API ключ"
    name_plural = "API ключи"
    icon = "fa-key"
    can_create = False
    can_edit = False
    can_delete = False

class UserSubscriptionAdmin(ModelView, model=UserSubscription):
    column_list = [
        UserSubscription.id,
        UserSubscription.chat_id,
        UserSubscription.artikul,
        UserSubscription.created_at
    ]
    column_searchable_list = [UserSubscription.chat_id, UserSubscription.artikul]
    column_sortable_list = [UserSubscription.id, UserSubscription.created_at]
    column_default_sort = ("created_at", True)
    name = "Подписка пользователя"
    name_plural = "Подписки пользователей"
    icon = "fa-users"
    can_create = False
    can_edit = False
    can_delete = False
    