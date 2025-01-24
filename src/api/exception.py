class WildberriesAPIError(Exception):
    """Базовый класс для ошибок Wildberries API"""
    pass

class ProductNotFoundError(WildberriesAPIError):
    """Товар не найден"""
    pass

class WildberriesTimeoutError(WildberriesAPIError):
    """Превышено время ожидания ответа"""
    pass

class WildberriesResponseError(WildberriesAPIError):
    """Ошибка в ответе API"""
    pass
