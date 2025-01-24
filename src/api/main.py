import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from sqladmin import Admin
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from admin import (
    ProductAdmin,
    PriceHistoryAdmin,
    SubscriptionAdmin,
    TaskLogAdmin,
    ApiKeyAdmin,
    UserSubscriptionAdmin
)
from db import connect_with_retries, SyncEngine, AsyncEngine
from router import router_product
from middleware import rate_limit_middleware
from scheduler import start_scheduler
from exception import WildberriesAPIError, ProductNotFoundError, WildberriesTimeoutError, WildberriesResponseError

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)

# Глобальная переменная для хранения планировщика
scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global scheduler
    
    # Startup
    try:
        logger.info("=== Starting application ===")
        
        # Подключаемся к базе данных
        await connect_with_retries()
        logger.info("Successfully connected to database")
        
        # Запускаем планировщик задач
        logger.info("Starting scheduler...")
        scheduler = start_scheduler()
        logger.info("=== Application startup completed successfully ===")
        
        yield
        
        # Shutdown
        logger.info("=== Shutting down application ===")
        if scheduler:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler stopped")
        
        logger.info("Closing database connections...")
        await AsyncEngine.dispose()
        logger.info("=== Application shutdown completed ===")
        
    except Exception as e:
        logger.error(f"Critical error: {e}")
        raise

app = FastAPI(
    title="Wildberries Parser API",
    description="""
    API для получения и отслеживания информации о товарах Wildberries.
    
    ### Возможности
    
    * Получение информации о товарах по артикулу
    * Подписка на обновления товаров
    * Управление частотой обновлений
    * Просмотр истории обновлений
    
    ### Ограничения
    
    * Не более 30 запросов в минуту с одного IP
    * Таймаут запроса к Wildberries API: 10 секунд
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

@app.middleware("http")
async def rate_limiting(request: Request, call_next):
    return await rate_limit_middleware(request, call_next)

@app.exception_handler(WildberriesAPIError)
async def wildberries_exception_handler(request: Request, exc: WildberriesAPIError):
    status_code = 404 if isinstance(exc, ProductNotFoundError) else 500
    if isinstance(exc, WildberriesTimeoutError):
        status_code = 504
    
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_product)

admin = Admin(app, engine=SyncEngine)
admin.add_view(ProductAdmin)
admin.add_view(PriceHistoryAdmin)
admin.add_view(SubscriptionAdmin)
admin.add_view(TaskLogAdmin)
admin.add_view(ApiKeyAdmin)
admin.add_view(UserSubscriptionAdmin)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8888, reload=True)

