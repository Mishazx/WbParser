import os
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Инициализация глобальных переменных
BOT_API_TOKEN = os.getenv('BOT_TOKEN')
API_TOKEN = os.getenv('API_TOKEN')
API_URL = os.getenv('API_URL', 'http://app/api/v1')

# Настройки запросов
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {API_TOKEN}'
}

# Логирование конфигурации
logger.info(f"Initialized with API_URL: {API_URL}")
logger.info(f"Bot token present: {'Yes' if BOT_API_TOKEN else 'No'}")
logger.info(f"API token present: {'Yes' if API_TOKEN else 'No'}") 