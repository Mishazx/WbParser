import os
import sys
from alembic import command
from alembic.config import Config

# Добавляем родительскую директорию в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def rollback_migrations():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    alembic_ini = os.path.join(os.path.dirname(current_dir), 'alembic.ini')
    
    alembic_cfg = Config(alembic_ini)
    alembic_cfg.set_main_option('script_location', os.path.join(os.path.dirname(current_dir), 'migrations'))
    
    # Откат на одну миграцию назад
    command.downgrade(alembic_cfg, "-1")

if __name__ == "__main__":
    rollback_migrations() 