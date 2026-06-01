#!/usr/bin/env python
"""
Запуск Django из корня проекта: перенаправляет в backend и вызывает backend/manage.py.
Все команды (makemigrations, migrate, runserver и т.д.) можно вызывать отсюда или из папки backend.
"""
import os
import sys

# Корень репозитория (где лежит этот manage.py)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

# Чтобы Django нашёл модуль shoshop (он в backend/)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Рабочая директория — backend (там лежат .env и настройки)
os.chdir(BACKEND_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shoshop.settings")

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
