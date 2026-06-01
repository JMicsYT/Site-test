@echo off
REM =====================================================================
REM Быстрый локальный запуск ShoShop (PostgreSQL, без Docker)
REM
REM ТРЕБОВАНИЯ:
REM   1) Установлен и запущен PostgreSQL (локально либо удалённо).
REM   2) В файле backend\.env заданы POSTGRES_HOST/PORT/DB/USER/PASSWORD.
REM      Пример смотрите в backend\.env (тот, что уже есть в репозитории).
REM   3) База данных из POSTGRES_DB должна существовать. Если её нет —
REM      создайте её вручную: psql -U postgres -c "CREATE DATABASE shoshop;"
REM =====================================================================
chcp 65001 > nul
cd /d "%~dp0"

REM --- 1. venv ----------------------------------------------------------
if not exist ".venv\Scripts\activate.bat" (
    if exist "venv\Scripts\activate.bat" (
        echo Использую существующее окружение .\venv ...
        call venv\Scripts\activate.bat
    ) else (
        echo Создаю виртуальное окружение .venv и ставлю зависимости...
        python -m venv .venv
        call .venv\Scripts\activate.bat
        pip install -r requirements.txt -q
    )
) else (
    call .venv\Scripts\activate.bat
)

REM --- 2. настройки окружения ------------------------------------------
set DJANGO_DEBUG=true
if "%DJANGO_SECRET_KEY%"=="" set DJANGO_SECRET_KEY=dev-secret-key
set DEFAULT_DOMAIN=127.0.0.1:8000

REM --- 3. проверка .env -------------------------------------------------
if not exist "backend\.env" (
    echo [!] Файл backend\.env не найден — используйте пример из README или docs\RUN_LOCAL.md
    echo     Для работы нужен доступ к PostgreSQL.
    exit /b 1
)

REM --- 4. миграции и суперпользователь (первый запуск) -----------------
cd backend
if not exist ".initialized" (
    echo Первый запуск: применяю миграции и создаю суперпользователя...
    python manage.py migrate
    if errorlevel 1 (
        echo [!] Не удалось применить миграции. Проверьте подключение к PostgreSQL.
        exit /b 1
    )
    echo Создайте суперпользователя:
    python manage.py createsuperuser
    echo. > .initialized
) else (
    python manage.py migrate --noinput
)

REM --- 5. статика и запуск ---------------------------------------------
echo.
echo =====================================================================
echo   ShoShop запущен: http://127.0.0.1:8000/
echo   Админка (Django): http://127.0.0.1:8000/admin/
echo   Кастомный дашборд: http://127.0.0.1:8000/dashboard/
echo   Остановка: Ctrl+C
echo =====================================================================
echo.
python manage.py runserver
