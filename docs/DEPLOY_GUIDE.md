# Полный гайд по развёртыванию ShoShop на сервере

Этот документ — **пошаговая инструкция «с нуля до работающего сайта в интернете»**.  
Подходит, если вы впервые выкладываете Django-проект на VPS или выделенный сервер.

**Связанные материалы:**

| Файл | Зачем |
|------|--------|
| [`DEPLOY_CHECKLIST.md`](DEPLOY_CHECKLIST.md) | Короткий чек-лист перед релизом |
| [`../README.md`](../README.md) | Общая техническая документация проекта |
| [`RUN_LOCAL.md`](RUN_LOCAL.md) | Локальная разработка без Docker |
| [`SECURITY.md`](SECURITY.md) | Безопасность и OWASP |

---

## Содержание

1. [Что вы получите в итоге](#1-что-вы-получите-в-итоге)
2. [Архитектура продакшена](#2-архитектура-продакшена)
3. [Требования к серверу](#3-требования-к-серверу)
4. [Подготовка домена и DNS](#4-подготовка-домена-и-dns)
5. [Выбор способа развёртывания](#5-выбор-способа-развёртывания)
6. [Способ A: Docker Compose (рекомендуется)](#6-способ-a-docker-compose-рекомендуется)
7. [Способ B: VPS без Docker (Gunicorn + Nginx)](#7-способ-b-vps-без-docker-gunicorn--nginx)
8. [Переменные окружения — полный разбор](#8-переменные-окружения--полный-разбор)
9. [SSL-сертификаты (HTTPS)](#9-ssl-сертификаты-https)
10. [Статика и медиафайлы](#10-статика-и-медиафайлы)
11. [WebSocket (уведомления в реальном времени)](#11-websocket-уведомления-в-реальном-времени)
12. [Celery и фоновые задачи](#12-celery-и-фоновые-задачи)
13. [Почта (SMTP)](#13-почта-smtp)
14. [Платежи и callback](#14-платежи-и-callback)
15. [Первый запуск: админ, демо-данные](#15-первый-запуск-админ-демо-данные)
16. [Резервное копирование и восстановление](#16-резервное-копирование-и-восстановление)
17. [Обновление сайта после изменений в коде](#17-обновление-сайта-после-изменений-в-коде)
18. [Мониторинг и health-check](#18-мониторинг-и-health-check)
19. [Типичные ошибки и решения](#19-типичные-ошибки-и-решения)
20. [Финальный чек-лист](#20-финальный-чек-лист)

---

## 1. Что вы получите в итоге

После прохождения гайда на сервере будет работать:

- **Сайт ShoShop** по адресу `https://ваш-домен.ru`
- **PostgreSQL** — база данных (обязательна, SQLite не используется)
- **Redis** — кеш, Celery, WebSocket (рекомендуется в проде)
- **Nginx** — HTTPS, раздача `/static/` и `/media/`, прокси к Django
- **Gunicorn** — WSGI-сервер для HTTP-запросов Django
- Опционально: **Celery** (фоновые задачи), **Daphne** (WebSocket)

Пользователи смогут регистрироваться, покупать цифровые товары, админ — работать в `/dashboard/` и `/admin/`.

---

## 2. Архитектура продакшена

```
Интернет
   │
   ▼
┌──────────────────────────────────────┐
│  Nginx (:443 HTTPS, :80 → редирект)   │
│  • /static/  → каталог staticfiles    │
│  • /media/   → каталог media          │
│  • /         → proxy → Gunicorn :8000   │
│  • /ws/      → proxy → Daphne :8001   │  (опционально)
└──────────────────────────────────────┘
   │
   ├──► Gunicorn (Django WSGI) ──► PostgreSQL
   │         │
   │         └──► Redis (кеш, Celery, Channels)
   │
   ├──► Celery worker
   ├──► Celery beat
   └──► Daphne (ASGI, WebSocket) — опционально
```

**Важно:** в `docker-compose.yml` из репозитория сервис `web` запускает **только Gunicorn (WSGI)**.  
Обычные страницы сайта работают. **WebSocket-уведомления** (`/ws/notifications/`) для полноценной работы в проде требуют отдельного ASGI-процесса (Daphne) — см. [§11](#11-websocket-уведомления-в-реальном-времени).

---

## 3. Требования к серверу

### Минимальные характеристики (учебный/небольшой трафик)

| Ресурс | Минимум | Рекомендуется |
|--------|---------|---------------|
| CPU | 1 vCPU | 2 vCPU |
| RAM | 2 GB | 4 GB |
| Диск | 20 GB SSD | 40+ GB SSD |
| ОС | Ubuntu 22.04 / 24.04 LTS | то же |

### Программное обеспечение

**Для Docker-деплоя:**

- Docker Engine 24+
- Docker Compose v2 (`docker compose`, не обязательно старый `docker-compose`)

**Для деплоя без Docker:**

- Python **3.11+** (в Dockerfile проекта — 3.11)
- PostgreSQL **14+** (в Compose — 16)
- Redis **7+**
- Nginx **1.22+**
- Git

### Сеть и firewall

Откройте на сервере (через панель хостинга или `ufw`):

| Порт | Назначение |
|------|------------|
| **22** | SSH (доступ администратора) |
| **80** | HTTP (редирект на HTTPS / проверка Let's Encrypt) |
| **443** | HTTPS (основной трафик сайта) |

Порты **5432** (PostgreSQL) и **6379** (Redis) **не открывайте в интернет** — только `localhost` или внутренняя сеть Docker.

Пример `ufw` на Ubuntu:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

---

## 4. Подготовка домена и DNS

1. Купите домен у регистратора (Reg.ru, Timeweb, Cloudflare и т.д.).
2. В DNS создайте записи:

| Тип | Имя | Значение | TTL |
|-----|-----|----------|-----|
| **A** | `@` | IP-адрес вашего VPS | 300–3600 |
| **A** | `www` | тот же IP (или CNAME на `@`) | 300–3600 |

3. Дождитесь распространения DNS (от нескольких минут до 24 часов). Проверка:

```bash
dig +short ваш-домен.ru
ping -c 3 ваш-домен.ru
```

4. Запишите домен — он понадобится в `DJANGO_ALLOWED_HOSTS` и `DEFAULT_DOMAIN`.

---

## 5. Выбор способа развёртывания

| Критерий | Docker Compose | VPS без Docker |
|----------|----------------|----------------|
| Сложность первого деплоя | **Ниже** — всё в одном `compose` | Выше — ставите пакеты вручную |
| Обновления | `git pull` + `docker compose up -d --build` | `git pull` + restart systemd |
| Изоляция | Хорошая | Зависит от настройки |
| Подходит для диплома/демо | **Да** | Да |
| Подходит для «классического» VPS | Да | **Привычный вариант** |

**Рекомендация:** начните со **способа A (Docker)**, если на сервере можно установить Docker.  
Если хостинг без Docker — используйте **способ B**.

---

## 6. Способ A: Docker Compose (рекомендуется)

### 6.1. Подключение к серверу и базовая подготовка

```bash
ssh root@IP_ВАШЕГО_СЕРВЕРА
# или: ssh ubuntu@IP (если создан пользователь ubuntu)
```

Обновите систему (Ubuntu):

```bash
apt update && apt upgrade -y
apt install -y git curl ca-certificates
```

### 6.2. Установка Docker

Официальный способ (актуальная документация: https://docs.docker.com/engine/install/ubuntu/):

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker
```

Проверка:

```bash
docker --version
docker compose version
```

Опционально — добавить пользователя в группу `docker` (чтобы не писать `sudo` каждый раз):

```bash
usermod -aG docker $USER
# Выйдите из SSH и зайдите снова
```

### 6.3. Клонирование проекта на сервер

```bash
mkdir -p /srv
cd /srv
git clone https://github.com/JMicsYT/Site-test.git shoshop
cd shoshop
```

Если репозиторий приватный — настройте SSH-ключ на сервере или используйте deploy token.

Структура после клонирования:

```
/srv/shoshop/
├── docker-compose.yml
├── Dockerfile
├── backend/
├── config/nginx/
└── ...
```

### 6.4. Файл переменных окружения для Docker

**Важно:** `docker-compose.yml` читает **`env_file: .env` из корня репозитория** (рядом с `docker-compose.yml`), а не только `backend/.env`.

Создайте корневой `.env`:

```bash
cd /srv/shoshop
cp backend/env.example .env
nano .env   # или vim / vi
```

Минимально обязательные правки для продакшена (подставьте свои значения):

```env
# === Django ===
DJANGO_SECRET_KEY=СГЕНЕРИРУЙТЕ_ДЛИННЫЙ_СЛУЧАЙНЫЙ_КЛЮЧ
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=ваш-домен.ru,www.ваш-домен.ru
PROJECT_NAME=ShoShop

# === PostgreSQL (имена сервисов Docker) ===
POSTGRES_DB=shoshop
POSTGRES_USER=shoshop
POSTGRES_PASSWORD=НАДЁЖНЫЙ_ПАРОЛЬ_БД
POSTGRES_HOST=db
POSTGRES_PORT=5432

# === Redis / Celery ===
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CACHE_URL=redis://redis:6379/1
CHANNELS_REDIS_URL=redis://redis:6379/2

# === Домен и HTTPS ===
DEFAULT_DOMAIN=ваш-домен.ru
DJANGO_SECURE_SSL_REDIRECT=true
SECURE_PROXY_SSL_HEADER=true

# === Платежи (обязательно свой секрет в проде) ===
PAYMENT_CALLBACK_URL=https://ваш-домен.ru/api/payments/callback/
PAYMENT_CALLBACK_SECRET=СЛУЧАЙНЫЙ_СЕКРЕТ_CALLBACK

# === Шифрование цифровых ключей (сгенерировать один раз, НЕ МЕНЯТЬ потом) ===
FIELD_ENCRYPTION_KEY=СГЕНЕРИРУЙТЕ_FERNET_КЛЮЧ
DOWNLOAD_LINK_SECRET=ОТДЕЛЬНЫЙ_СЛУЧАЙНЫЙ_СЕКРЕТ
```

**Генерация секретов на сервере:**

```bash
# SECRET_KEY Django (50+ символов)
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# FIELD_ENCRYPTION_KEY (Fernet — через Django/cryptography после установки зависимостей)
# Временно в контейнере после первого build:
docker compose run --rm web python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Дублируйте тот же `.env` в `backend/.env` **или** убедитесь, что все ключи есть в корневом `.env` (Compose инжектит их в процесс `web`).  
При bind-mount `./backend:/app` файл `backend/.env` на хосте тоже виден внутри контейнера — удобно держать **одинаковые** значения в обоих местах, чтобы не путаться при ручном `manage.py` с хоста.

### 6.5. SSL-сертификаты для Nginx в Docker

Конфиг `config/nginx/shoshop.conf` ожидает файлы:

```
config/nginx/certs/fullchain.pem
config/nginx/certs/privkey.pem
```

**Вариант 1 — Let's Encrypt на хосте, затем копирование в проект**

Временно остановите nginx в compose, получите сертификат:

```bash
apt install -y certbot
cd /srv/shoshop
docker compose stop nginx

certbot certonly --standalone -d ваш-домен.ru -d www.ваш-домен.ru \
  --agree-tos -m admin@ваш-домен.ru --non-interactive

mkdir -p config/nginx/certs
cp /etc/letsencrypt/live/ваш-домен.ru/fullchain.pem config/nginx/certs/
cp /etc/letsencrypt/live/ваш-домен.ru/privkey.pem config/nginx/certs/
chmod 644 config/nginx/certs/fullchain.pem
chmod 600 config/nginx/certs/privkey.pem
```

**Вариант 2 — самоподписанный сертификат (только для теста)**

```bash
mkdir -p config/nginx/certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout config/nginx/certs/privkey.pem \
  -out config/nginx/certs/fullchain.pem \
  -subj "/CN=localhost"
```

Браузер покажет предупреждение — для продакшена используйте Let's Encrypt.

Отредактируйте `config/nginx/shoshop.conf`: замените `server_name _;` на ваш домен:

```nginx
server_name ваш-домен.ru www.ваш-домен.ru;
```

(в обоих блоках `listen 80` и `listen 443`).

### 6.6. Сборка и запуск контейнеров

```bash
cd /srv/shoshop
docker compose build
docker compose up -d
```

Проверка статуса:

```bash
docker compose ps
docker compose logs -f web --tail=100
```

Должны быть в состоянии `Up`: `web`, `db`, `redis`, `celery`, `celery-beat`, `nginx`.

### 6.7. Первичная настройка приложения внутри контейнера

```bash
# Миграции БД
docker compose exec web python manage.py migrate

# Сбор статики в том static_volume (для Nginx)
docker compose exec web python manage.py collectstatic --noinput

# Создание администратора (интерактивно)
docker compose exec web python manage.py createsuperuser
```

Опционально — демо-данные для проверки каталога:

```bash
docker compose exec web python manage.py seed_demo
```

### 6.8. Проверка в браузере

1. Откройте `https://ваш-домен.ru/`
2. Проверьте `https://ваш-домен.ru/health/` — должен вернуть JSON со статусом (200, если БД доступна)
3. Войдите в `https://ваш-домен.ru/dashboard/` под пользователем с `is_staff=True`

### 6.9. Автозапуск после перезагрузки сервера

В `docker-compose.yml` уже указано `restart: unless-stopped`. Убедитесь, что Docker запускается при загрузке:

```bash
systemctl enable docker
```

После reboot:

```bash
cd /srv/shoshop && docker compose up -d
```

### 6.10. Продление Let's Encrypt (cron)

```bash
crontab -e
```

Добавьте (раз в месяц, путь подставьте свой):

```cron
0 4 1 * * certbot renew --quiet && cp /etc/letsencrypt/live/ваш-домен.ru/*.pem /srv/shoshop/config/nginx/certs/ && cd /srv/shoshop && docker compose restart nginx
```

---

## 7. Способ B: VPS без Docker (Gunicorn + Nginx)

Подходит для VPS, где Docker не используется.

### 7.1. Установка системных пакетов (Ubuntu)

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip \
  postgresql postgresql-contrib \
  redis-server \
  nginx \
  git \
  build-essential libpq-dev
```

### 7.2. PostgreSQL

```bash
sudo -u postgres psql
```

В консоли PostgreSQL:

```sql
CREATE USER shoshop WITH PASSWORD 'НАДЁЖНЫЙ_ПАРОЛЬ';
CREATE DATABASE shoshop OWNER shoshop;
\q
```

Проверка:

```bash
psql -h localhost -U shoshop -d shoshop -c "SELECT 1;"
```

### 7.3. Redis

```bash
sudo systemctl enable redis-server
sudo systemctl start redis-server
redis-cli ping
# Ответ: PONG
```

### 7.4. Пользователь и каталог приложения

```bash
sudo useradd -r -m -d /srv/shoshop -s /bin/bash shoshop
sudo mkdir -p /srv/shoshop
sudo chown shoshop:shoshop /srv/shoshop
```

Клонирование от имени `shoshop`:

```bash
sudo -u shoshop git clone https://ВАШ-РЕПО/Site-test.git /srv/shoshop/app
cd /srv/shoshop/app
```

### 7.5. Виртуальное окружение Python

```bash
sudo -u shoshop bash -c '
cd /srv/shoshop/app/backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
'
```

### 7.6. Файл `backend/.env`

```bash
sudo -u shoshop cp /srv/shoshop/app/backend/env.example /srv/shoshop/app/backend/.env
sudo -u shoshop nano /srv/shoshop/app/backend/.env
```

Для VPS **без Docker** измените хосты:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
CACHE_URL=redis://127.0.0.1:6379/1
CHANNELS_REDIS_URL=redis://127.0.0.1:6379/2

DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=ваш-домен.ru,www.ваш-домен.ru
DJANGO_SECURE_SSL_REDIRECT=true
SECURE_PROXY_SSL_HEADER=true
DEFAULT_DOMAIN=ваш-домен.ru
```

Остальные секреты — как в [§6.4](#64-файл-переменных-окружения-для-docker).

### 7.7. Миграции и статика

```bash
sudo -u shoshop bash -c '
cd /srv/shoshop/app
source backend/venv/bin/activate
export DJANGO_SETTINGS_MODULE=shoshop.settings
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
'
```

`collectstatic` положит файлы в `backend/staticfiles/`.

### 7.8. Systemd: Gunicorn

Создайте `/etc/systemd/system/shoshop-gunicorn.service`:

```ini
[Unit]
Description=ShoShop Gunicorn
After=network.target postgresql.service redis-server.service

[Service]
User=shoshop
Group=shoshop
WorkingDirectory=/srv/shoshop/app/backend
Environment="DJANGO_SETTINGS_MODULE=shoshop.settings"
EnvironmentFile=/srv/shoshop/app/backend/.env
ExecStart=/srv/shoshop/app/backend/venv/bin/gunicorn shoshop.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Запуск:

```bash
sudo systemctl daemon-reload
sudo systemctl enable shoshop-gunicorn
sudo systemctl start shoshop-gunicorn
sudo systemctl status shoshop-gunicorn
```

### 7.9. Systemd: Celery (опционально, но рекомендуется)

`/etc/systemd/system/shoshop-celery.service`:

```ini
[Unit]
Description=ShoShop Celery Worker
After=network.target redis-server.service

[Service]
User=shoshop
Group=shoshop
WorkingDirectory=/srv/shoshop/app/backend
Environment="DJANGO_SETTINGS_MODULE=shoshop.settings"
EnvironmentFile=/srv/shoshop/app/backend/.env
ExecStart=/srv/shoshop/app/backend/venv/bin/celery -A shoshop worker -l info
Restart=always

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/shoshop-celery-beat.service` — аналогично, команда:

```
celery -A shoshop beat -l info
```

```bash
sudo systemctl enable --now shoshop-celery shoshop-celery-beat
```

### 7.10. Nginx на хосте

Пример `/etc/nginx/sites-available/shoshop`:

```nginx
upstream shoshop_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name ваш-домен.ru www.ваш-домен.ru;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ваш-домен.ru www.ваш-домен.ru;

    ssl_certificate /etc/letsencrypt/live/ваш-домен.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ваш-домен.ru/privkey.pem;

    client_max_body_size 20M;

    location /static/ {
        alias /srv/shoshop/app/backend/staticfiles/;
    }

    location /media/ {
        alias /srv/shoshop/app/backend/media/;
    }

    location / {
        proxy_pass http://shoshop_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_redirect off;
    }
}
```

Активация:

```bash
sudo ln -s /etc/nginx/sites-available/shoshop /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

SSL через Certbot:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d ваш-домен.ru -d www.ваш-домен.ru
```

---

## 8. Переменные окружения — полный разбор

Шаблон: `backend/env.example`.  
Ниже — что **обязательно** настроить в проде и что будет, если оставить пустым.

### 8.1. Django (критично)

| Переменная | Прод | Что будет, если неверно |
|------------|------|-------------------------|
| `DJANGO_SECRET_KEY` | Уникальный длинный ключ | Сессии и CSRF небезопасны; при перезапуске с новым ключом — разлогин всех |
| `DJANGO_DEBUG` | **`false`** | Утечка трассировок, открытые настройки |
| `DJANGO_ALLOWED_HOSTS` | Ваш домен(ы) через запятую | **400 Bad Request** / ошибка DisallowedHost |
| `PROJECT_NAME` | Название в шаблонах | Только отображение |

### 8.2. PostgreSQL (критично)

| Переменная | Docker | VPS |
|------------|--------|-----|
| `POSTGRES_HOST` | `db` | `localhost` |
| `POSTGRES_DB` | `shoshop` | то же |
| `POSTGRES_USER` | свой | свой |
| `POSTGRES_PASSWORD` | **сильный пароль** | то же |

Без работающего Postgres сайт не запустится (проект **не поддерживает SQLite**).

### 8.3. HTTPS и прокси

| Переменная | Когда `true` |
|------------|--------------|
| `DJANGO_SECURE_SSL_REDIRECT` | Сайт доступен только по HTTPS; HTTP редиректит на HTTPS |
| `SECURE_PROXY_SSL_HEADER` | Nginx терминирует SSL и проксирует на Gunicorn по HTTP |

Оба обычно **`true`** в проде за Nginx.

### 8.4. Redis, кеш, Celery, Channels

| Переменная | Рекомендация в проде |
|------------|----------------------|
| `CELERY_BROKER_URL` | `redis://redis:6379/0` (Docker) или `redis://127.0.0.1:6379/0` |
| `CELERY_RESULT_BACKEND` | тот же Redis |
| `CACHE_URL` | отдельная БД Redis, напр. `/1` |
| `CHANNELS_REDIS_URL` | отдельная БД, напр. `/2` — для WebSocket между воркерами |

Если `CACHE_URL` пуст — используется **LocMem** (только один процесс, для кластера плохо).

Если `CHANNELS_REDIS_URL` пуст — **InMemory** channel layer (WebSocket только в одном процессе).

### 8.5. Шифрование и выдача цифровых товаров

| Переменная | Важность |
|------------|----------|
| `FIELD_ENCRYPTION_KEY` | Шифрует значения ключей в БД. **Потеря ключа = потеря данных** |
| `DOWNLOAD_LINK_SECRET` | Подпись одноразовых ссылок скачивания |
| `DOWNLOAD_LINK_TTL` | Время жизни ссылки (сек), по умолчанию 900 |
| `DOWNLOAD_LINK_MAX_USES` | Сколько раз можно открыть ссылку |

Сгенерируйте **до первого заказа** с цифровыми товарами.

### 8.6. Платежи

| Переменная | Прод |
|------------|------|
| `PAYMENT_PROVIDER_CLASS` | Класс провайдера (демо: `apps.payments.providers.StubPaymentProvider`) |
| `PAYMENT_CALLBACK_URL` | Публичный HTTPS URL callback |
| `PAYMENT_CALLBACK_SECRET` | **Обязателен** — проверка подписи webhook |

### 8.7. Почта, Telegram, рефералы

См. `backend/env.example` и раздел [§13](#13-почта-smtp).  
Для сброса пароля и подтверждения email нужен реальный SMTP, иначе письма только в логах.

---

## 9. SSL-сертификаты (HTTPS)

### Docker

Сертификаты кладутся в `config/nginx/certs/` — см. [§6.5](#65-ssl-сертификаты-для-nginx-в-docker).

### VPS без Docker

Удобнее всего **Certbot + nginx plugin** — см. [§7.10](#710-nginx-на-хосте).

### Проверка

```bash
curl -I https://ваш-домен.ru/
openssl s_client -connect ваш-домен.ru:443 -servername ваш-домен.ru </dev/null 2>/dev/null | openssl x509 -noout -dates
```

---

## 10. Статика и медиафайлы

| Путь в проекте | Назначение |
|----------------|------------|
| `backend/static/` | Исходники CSS/JS при разработке |
| `backend/staticfiles/` | Результат `collectstatic` — **отдаёт Nginx в проде** |
| `backend/media/` | Загрузки (аватары, картинки товаров) |

### Команда перед каждым релизом с изменениями статики

```bash
python manage.py collectstatic --noinput
```

Docker:

```bash
docker compose exec web python manage.py collectstatic --noinput
```

### Права на media

Процесс Gunicorn должен иметь право записи в `backend/media/`:

```bash
sudo chown -R shoshop:shoshop /srv/shoshop/app/backend/media
```

В Docker том `media_volume` хранит данные между пересборками.

### Кеш браузера

В шаблонах к CSS/JS добавлены `?v=…`. При деплое нового дизайна увеличьте версию в `base.html`, чтобы пользователи не видели старый CSS.

---

## 11. WebSocket (уведомления в реальном времени)

Маршрут: `/ws/notifications/`  
Клиент: `backend/static/js/notifications.js`

### Минимальный вариант (без Daphne)

Сайт работает; уведомления можно обновлять по HTTP (панель в шапке), но **без push в реальном времени**.

### Полный вариант (прод)

1. Задайте `CHANNELS_REDIS_URL` (см. [§8.4](#84-redis-кеш-celery-channels)).
2. Запустите **Daphne** на отдельном порту, например `8001`:

```bash
cd /srv/shoshop/app/backend
source venv/bin/activate
daphne -b 127.0.0.1 -p 8001 shoshop.asgi:application
```

3. Добавьте в Nginx **перед** `location /`:

```nginx
location /ws/ {
    proxy_pass http://127.0.0.1:8001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 86400;
}
```

4. Для Docker — добавьте сервис `daphne` в `docker-compose.yml` и upstream в `shoshop.conf` (по аналогии с `web:8000`).

---

## 12. Celery и фоновые задачи

В Compose уже есть `celery` и `celery-beat`. Проверка:

```bash
docker compose logs celery --tail=50
```

Без Celery основной сайт обычно **работает**; отложенные задачи (если добавите в код) выполняться не будут.

На VPS — systemd-юниты из [§7.9](#79-systemd-celery-опционально-но-рекомендуется).

---

## 13. Почта (SMTP)

Без `EMAIL_HOST` письма пишутся в **консоль** (логи контейнера/журнал systemd).

Пример для Яндекс / Mail.ru / Gmail (значения уточняйте у провайдера):

```env
EMAIL_HOST=smtp.yandex.ru
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=no-reply@ваш-домен.ru
EMAIL_HOST_PASSWORD=пароль_или_пароль_приложения
DEFAULT_FROM_EMAIL=no-reply@ваш-домен.ru
DEFAULT_DOMAIN=ваш-домен.ru
```

Для разработки можно временно:

```env
REQUIRE_EMAIL_VERIFIED_FOR_PURCHASE=false
```

В проде лучше оставить `true` и настроить SMTP.

---

## 14. Платежи и callback

1. Укажите реальный `PAYMENT_CALLBACK_URL` (HTTPS, доступен из интернета).
2. Задайте длинный `PAYMENT_CALLBACK_SECRET`.
3. При подключении эквайринга замените `PAYMENT_PROVIDER_CLASS` на свой класс провайдера.

Проверка доступности callback с сервера:

```bash
curl -I https://ваш-домен.ru/api/payments/callback/
```

(ожидается ответ приложения, не 404 от Nginx).

---

## 15. Первый запуск: админ, демо-данные

```bash
python manage.py createsuperuser
```

Пользователь должен иметь **`is_staff=True`** для `/dashboard/`.  
В Django Admin (`/admin/`) можно выдать staff существующему пользователю.

Демо-каталог:

```bash
python manage.py seed_demo
# с пересозданием: python manage.py seed_demo --reset
```

**Админ-панель:** `https://ваш-домен.ru/dashboard/`  
**Django Admin:** `https://ваш-домен.ru/admin/`

---

## 16. Резервное копирование и восстановление

### 16.1. Команда проекта

```bash
python manage.py dump_db
python manage.py dump_db --out /backups/shoshop
```

### 16.2. PostgreSQL в Docker (cron)

```bash
mkdir -p /backups/shoshop
crontab -e
```

```cron
0 3 * * * cd /srv/shoshop && docker compose exec -T db pg_dump -U shoshop shoshop | gzip > /backups/shoshop/shoshop_$(date +\%Y\%m\%d).sql.gz
```

Храните копии **вне сервера** (S3, другой VPS, NAS).

### 16.3. Восстановление из дампа

```bash
gunzip -c /backups/shoshop/shoshop_20260401.sql.gz | docker compose exec -T db psql -U shoshop shoshop
```

Перед восстановлением на проде — остановите приложение и сделайте бэкап текущего состояния.

### 16.4. Что ещё бэкапить

- `backend/media/` — загруженные файлы
- `backend/.env` и корневой `.env` — **в зашифрованном хранилище**, не в публичном git
- `FIELD_ENCRYPTION_KEY` — без него не расшифровать цифровые ключи в БД

---

## 17. Обновление сайта после изменений в коде

### Docker

```bash
cd /srv/shoshop
git pull
docker compose build
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
```

При изменении только шаблонов/CSS иногда достаточно `git pull` + `collectstatic` без полного rebuild.

### VPS

```bash
cd /srv/shoshop/app
sudo -u shoshop git pull
sudo -u shoshop bash -c 'cd backend && source venv/bin/activate && pip install -r requirements.txt'
sudo -u shoshop bash -c 'cd /srv/shoshop/app && source backend/venv/bin/activate && python manage.py migrate && python manage.py collectstatic --noinput'
sudo systemctl restart shoshop-gunicorn shoshop-celery
```

---

## 18. Мониторинг и health-check

### Эндпоинт

```
GET https://ваш-домен.ru/health/
```

- **200** — приложение и БД доступны  
- **503** — проблема с БД (смотрите логи Postgres и `web`)

Используйте для uptime-мониторинга (UptimeRobot, Better Stack и т.д.).

### Логи

| Окружение | Где смотреть |
|-----------|--------------|
| Docker web | `docker compose logs web -f` |
| Docker nginx | `docker compose logs nginx -f` |
| Django файлы | `backend/logs/app.log`, `backend/logs/security.log` |
| Gunicorn systemd | `journalctl -u shoshop-gunicorn -f` |
| Nginx | `/var/log/nginx/error.log` |

---

## 19. Типичные ошибки и решения

| Симптом | Причина | Решение |
|---------|---------|---------|
| `DisallowedHost` | Домен не в `ALLOWED_HOSTS` | Добавить в `DJANGO_ALLOWED_HOSTS` без пробелов лишних |
| Бесконечный редирект HTTP↔HTTPS | `SECURE_SSL_REDIRECT` без корректного прокси | Включить `SECURE_PROXY_SSL_HEADER=true`, проверить заголовок `X-Forwarded-Proto` в Nginx |
| 502 Bad Gateway | Gunicorn не запущен / неверный порт | `systemctl status` / `docker compose ps`, логи gunicorn |
| Статика 404 | Не выполнен `collectstatic` или неверный `alias` в Nginx | `collectstatic`, путь к `staticfiles` |
| Картинки товаров 404 | Нет `location /media/` или нет прав на `media/` | Nginx + права каталога |
| `connection refused` к Postgres | Неверный `POSTGRES_HOST` | `db` в Docker, `localhost` на VPS |
| WebSocket не подключается | Только Gunicorn, нет Daphne / нет Upgrade в Nginx | [§11](#11-websocket-уведомления-в-реальном-времени) |
| Письма не приходят | Нет SMTP | [§13](#13-почта-smtp) |
| `POST /admin/login/` → **403** на HTTP (по IP) | Secure-cookies при `DEBUG=false` без HTTPS; нет `CSRF_TRUSTED_ORIGINS` | В `/srv/shoshop/.env`: `DJANGO_SECURE_SSL_REDIRECT=false`, `CSRF_TRUSTED_ORIGINS=http://ВАШ_IP`, при необходимости `DJANGO_COOKIE_SECURE=false`; `docker compose up -d --force-recreate web` |
| После деплоя старый дизайн | Кеш браузера или CDN | Ctrl+F5, увеличить `?v=` в `base.html` |
| `ModuleNotFoundError: cryptography` | Не установлены зависимости | `pip install -r backend/requirements.txt` |
| Цифровые ключи не открываются | Сменили `FIELD_ENCRYPTION_KEY` | Восстановить старый ключ из бэкапа `.env` |

---

## 20. Финальный чек-лист

Перед тем как считать сайт «в проде», пройдите пункты из [`DEPLOY_CHECKLIST.md`](DEPLOY_CHECKLIST.md) и дополнительно:

- [ ] Домен открывается по **HTTPS** без предупреждений браузера
- [ ] `DJANGO_DEBUG=false`
- [ ] Уникальные `DJANGO_SECRET_KEY`, `PAYMENT_CALLBACK_SECRET`, `FIELD_ENCRYPTION_KEY`
- [ ] `migrate` и `collectstatic` выполнены
- [ ] Создан суперпользователь / staff для `/dashboard/`
- [ ] `/health/` возвращает 200
- [ ] Регистрация, вход, добавление в корзину, тестовый заказ работают
- [ ] Настроен **ежедневный бэкап** PostgreSQL
- [ ] `.env` **не** попал в git
- [ ] Firewall: открыты только 22, 80, 443
- [ ] (Опционально) SMTP, Redis cache, Daphne + WebSocket, Telegram-алерты

---

**Краткая шпаргалка (Docker, уже настроенный сервер):**

```bash
cd /srv/shoshop
cp backend/env.example .env   # один раз, отредактировать
# положить SSL в config/nginx/certs/
docker compose build && docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py createsuperuser
```

После этого сайт должен быть доступен по вашему домену.

Если что-то из шагов не сходится с вашим хостингом (панель ISPmanager, Timeweb, Selectel и т.д.) — опишите окружение в issue или дополните этот файл под свой провайдер.
