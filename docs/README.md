## ShoShop — платформа цифровых товаров

**Полная техническая документация** (развёртывание, переменные окружения, архитектура, API, безопасность, troubleshooting) находится в корневом файле **[`../README.md`](../README.md)**.

Ниже — краткий обзор и ссылки на узкоспециализированные заметки.

### Стек
- Backend: Django 5, Django REST Framework, Celery + Redis
- БД: PostgreSQL
- Frontend: Django templates + CSS (тёмная тема ShoShop)
- Инфраструктура: Docker, docker-compose, Nginx (HTTPS-заглушка), Gunicorn

### Документация
- **DEPLOY_GUIDE.md** — **полный гайд по развёртыванию на сервере** (Docker и VPS, DNS, SSL, `.env`, Nginx, бэкапы, troubleshooting).
- **PROJECT_STATUS.md** — сводка по проекту: что сделано, что нет, что частично, что в планах.
- **RUN_LOCAL.md** — запуск без Docker (Windows/локально), PostgreSQL, переменные окружения (в т.ч. копирование `backend/env.example` в `backend/.env`).
- **SECURITY_AND_AUDIT.md** — что сделано по безопасности, рекомендации для продакшена.
- **ROADMAP_IMPROVEMENTS.md** — план доработок (тесты, UX, админка, деплой).
- **DEPLOY_CHECKLIST.md** — короткий чек-лист перед релизом (DEBUG, SECRET_KEY, ALLOWED_HOSTS, HTTPS, collectstatic, бэкапы БД и т.д.).

### Быстрый старт (локально через docker-compose)
1. Скопируйте `backend/env.example` в `backend/.env` и заполните при необходимости.
2. Соберите и поднимите контейнеры:
   ```bash
   docker-compose build
   docker-compose up
   ```
3. Выполните миграции и соберите статику (в другом терминале):
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py collectstatic --noinput
   docker-compose exec web python manage.py createsuperuser
   ```
4. Откройте `https://localhost/` (используется заглушечный сертификат в `config/nginx/certs`).

### Запуск без Docker (разработка)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
export DJANGO_DEBUG=true
python manage.py migrate
python manage.py runserver
```

### Основные переменные окружения
- `DJANGO_SECRET_KEY` — секретный ключ Django.
- `DJANGO_DEBUG` — режим отладки (`true`/`false`).
- `DJANGO_ALLOWED_HOSTS` — список хостов через запятую.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` — доступ к БД.
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` — настройки брокера/результатов Celery.
- `PAYMENT_PROVIDER_CLASS`, `PAYMENT_API_KEY`, `PAYMENT_API_SECRET`, `PAYMENT_CALLBACK_URL`, `PAYMENT_CALLBACK_SECRET` — платёжный провайдер (секрет callback обязателен в проде).
- `CACHE_URL` — URL Redis для кеша (например `redis://redis:6379/1`). Если не задан, используется локальный кеш.
- `DEFAULT_DOMAIN` — домен для писем (сброс пароля, подтверждение email).
- `PROJECT_NAME` — название сайта (по умолчанию ShoShop).
- **Письма (SMTP):** для реальной отправки писем (сброс пароля, подтверждение email) задайте `EMAIL_HOST`, `EMAIL_PORT` (обычно 587), `EMAIL_USE_TLS=true`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`. Без `EMAIL_HOST` письма выводятся в консоль.
- `REQUIRE_EMAIL_VERIFIED_FOR_PURCHASE` — требовать подтверждённый email для заказов (`true`/`false`, по умолчанию `true`).

### Резервное копирование БД
Рекомендуется настроить регулярный бэкап PostgreSQL (cron или внешний инструмент), например:
```bash
# Ежедневный дамп (cron)
0 3 * * * docker-compose exec -T db pg_dump -U shoshop shoshop | gzip > /backups/shoshop_$(date +\%Y\%m\%d).sql.gz
```
Либо использовать облачные бэкапы (AWS RDS, managed PostgreSQL и т.п.).

