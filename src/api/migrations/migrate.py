import os
import sys
from alembic import command
from alembic.config import Config

# Добавляем родительскую директорию в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_migrations():
    # Получаем текущую директорию
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Путь к alembic.ini
    alembic_ini = os.path.join(os.path.dirname(current_dir), 'alembic.ini')
    
    # Создаем конфигурацию
    alembic_cfg = Config(alembic_ini)
    alembic_cfg.set_main_option('script_location', os.path.join(os.path.dirname(current_dir), 'migrations'))
    
    # Запускаем миграции
    command.upgrade(alembic_cfg, "head")

if __name__ == "__main__":
    run_migrations() 