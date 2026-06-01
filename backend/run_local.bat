@echo off
REM Быстрый локальный запуск ShoShop (без Docker)
cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo Создаю виртуальное окружение и устанавливаю зависимости...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt -q
) else (
    call venv\Scripts\activate.bat
)

set DJANGO_DEBUG=true
set DJANGO_SECRET_KEY=dev-secret-key
set DEFAULT_DOMAIN=127.0.0.1:8000
if "%POSTGRES_HOST%"=="" set POSTGRES_HOST=localhost
if "%POSTGRES_PORT%"=="" set POSTGRES_PORT=5432
if "%POSTGRES_DB%"=="" set POSTGRES_DB=shoshop
if "%POSTGRES_USER%"=="" set POSTGRES_USER=shoshop
if "%POSTGRES_PASSWORD%"=="" set POSTGRES_PASSWORD=shoshop

echo Применение миграций...
python manage.py migrate
if errorlevel 1 (
    echo Ошибка: проверьте backend\.env — POSTGRES_HOST=localhost и доступ к PostgreSQL.
    pause
    exit /b 1
)

echo.
echo Запуск сервера: http://127.0.0.1:8000/
echo Суперпользователь: python manage.py createsuperuser
echo Остановка: Ctrl+C
echo.
python manage.py runserver
