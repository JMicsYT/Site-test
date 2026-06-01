# Локальный запуск ShoShop на ПК (без Docker)

Так можно запускать проект у себя на компьютере для тестирования и доработок. БД — **PostgreSQL** (установленный на ПК). Письма выводятся в консоль.

**Важно:** все команды `python manage.py ...` выполняются **из корня проекта** (`Site-test`), а не из папки `backend`. В корне лежит свой `manage.py`, который сам переходит в `backend` и подхватывает настройки и `.env`.

---

## 1. Установка Python

Нужен **Python 3.11** или новее.

- Скачать: https://www.python.org/downloads/
- При установке отметьте **"Add Python to PATH"**.

Проверка в терминале:
```bash
python --version
```

---

## 2. Корень проекта и виртуальное окружение

**Рабочая папка для всех команд — корень проекта**, например `F:\Файлы\Site-test` (у вас — ваш путь к `Site-test`). Открывайте терминал именно в этой папке.

Виртуальное окружение может быть:
- в **корне** проекта (например `.venv`) — если при открытии консоли у вас автоматически выполняется активация вроде `& .venv/Scripts/Activate.ps1`, ничего дополнительно делать не нужно;
- либо в папке **`backend`** (`venv`) — тогда перед командами один раз активируйте его.

**Если окружения ещё нет**, создайте его в корне проекта и активируйте:

**PowerShell (из корня Site-test):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

При ошибке *«выполнение сценариев отключено»* один раз выполните:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**cmd (из корня Site-test):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

После активации в начале строки должно появиться `(.venv)` или `(venv)`.

---

## 3. Установка зависимостей

Из **корня проекта** (с активированным venv):

```bash
pip install -r backend/requirements.txt
```

Для работы с **PostgreSQL** нужен пакет `psycopg` (уже есть в `requirements.txt`). Если установка падает, попробуйте: `pip install "psycopg[binary]"`.

---

## 4. База данных и переменные окружения

**Где лежит `.env`:** файл должен находиться в папке **`backend`** (редактируйте его там):
- Путь: **`Site-test\backend\.env`**, т.е. **`F:\Файлы\Site-test\backend\.env`** у вас.
- Его нет в репозитории. Чтобы создать: скопируйте в папке `backend` файл **`env.example`** и переименуйте копию в **`.env`**, затем откройте `.env` в любом редакторе и подставьте свои значения.

После этого можно не вводить переменные в терминале — Django при запуске прочитает их из `backend/.env`.

---

### PostgreSQL

1. **Создайте базу данных** в PostgreSQL (через pgAdmin, DBeaver или консоль `psql`).

Если в `.env` указан **`POSTGRES_USER=postgres`** (вход под суперпользователем), достаточно создать только базу:

```sql
CREATE DATABASE shoshop;
```

Если хотите отдельного пользователя для проекта:

```sql
CREATE USER shoshop WITH PASSWORD 'shoshop';
CREATE DATABASE shoshop OWNER shoshop;
```

Тогда в `backend/.env` укажите `POSTGRES_USER=shoshop`, `POSTGRES_PASSWORD=shoshop`.

2. **Переменные окружения** — в `backend/.env` задайте (для локального запуска без Docker — `POSTGRES_HOST=localhost`):

**PowerShell (если не используете .env):**
```powershell
$env:DJANGO_DEBUG="true"; $env:DJANGO_SECRET_KEY="dev-secret-123"; $env:DEFAULT_DOMAIN="127.0.0.1:8000"
$env:POSTGRES_HOST="localhost"; $env:POSTGRES_PORT="5432"; $env:POSTGRES_DB="shoshop"; $env:POSTGRES_USER="postgres"; $env:POSTGRES_PASSWORD="QpAlZmoi516?56"
```

**cmd (если не используете .env):**
```cmd
set DJANGO_DEBUG=true
set DJANGO_SECRET_KEY=dev-secret-123
set DEFAULT_DOMAIN=127.0.0.1:8000
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
set POSTGRES_DB=shoshop
set POSTGRES_USER=shoshop
set POSTGRES_PASSWORD=shoshop
```

---

## 5. Переменные окружения — когда задавать

Если вы **не** используете файл `.env`, задайте переменные из шага 4 **в той же сессии терминала** перед любыми командами `manage.py`.

Если вы **создали и отредактировали `backend/.env`** (скопировав из `backend/env.example`), дополнительные команды не нужны — Django подхватит переменные из файла при запуске.

**Письма (сброс пароля, подтверждение email):** по умолчанию письма выводятся в консоль. Для реальной отправки задайте в `.env`: `EMAIL_HOST`, `EMAIL_PORT` (587), `EMAIL_USE_TLS=true`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`.

**Заказы без подтверждения email:** в разработке можно отключить требование подтверждённого email: в `.env` задайте `REQUIRE_EMAIL_VERIFIED_FOR_PURCHASE=false`.

---

## 6. Миграции и суперпользователь

Из **корня проекта** (там же, где вы открываете консоль):

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

При `createsuperuser` укажите **email** (вместо логина) и пароль.

При необходимости создайте тестовые данные (категория и товар) через админку или команду:

```bash
python manage.py shell
```

```python
from apps.catalog.models import Category, Product
c = Category.objects.create(name="Игры", slug="games", sort_order=0)
Product.objects.create(
    category=c, name="Тестовая игра", slug="test-game",
    short_description="Кратко", description="Описание",
    price=299, product_type="game", license_type="perpetual",
    purpose="personal", status="active"
)
exit()
```

---

## 7. Запуск сервера

Из **корня проекта**:

```bash
python manage.py runserver
```

В консоли появится что-то вроде:
`Starting development server at http://127.0.0.1:8000/`

Откройте в браузере: **http://127.0.0.1:8000/**

---

## 8. Доступ к админкам

В проекте две админки; для обеих нужен пользователь с правами персонала (суперпользователь).

### Создать суперпользователя (если ещё не создавали)

Из **корня проекта**:

```bash
python manage.py createsuperuser
```

Введите **email** (не логин) и пароль. Этот пользователь сможет заходить в обе админки.

### 1) Админка Django (стандартная)

- **URL:** http://127.0.0.1:8000/admin/
- **Вход:** тот же **email** и пароль, что при `createsuperuser`.
- В форме входа в поле «Имя пользователя» (или «Username») нужно вводить **email**.

Если админка не открывается или выдаёт ошибку — проверьте, что миграции применены (`migrate`) и суперпользователь создан.

### 2) Кастомная админ-панель ShoShop

- **URL:** http://127.0.0.1:8000/dashboard/
- **Вход:** тот же пользователь (email + пароль). Если вы не залогинены, откроется страница входа Django (`/admin/login/`) — введите email и пароль, после входа можно снова перейти на **/dashboard/**.

В дашборде: товары, категории, заказы, пользователи, отзывы, настройки, журнал безопасности. Ссылка «На сайт» ведёт на главную, «Django Admin» — в стандартную админку.

---

---

## Что работает без доп. настроек

- Сайт и все страницы.
- Регистрация и вход (пароли хранятся в БД).
- Письма (сброс пароля, подтверждение email) **выводятся в консоль** — ссылки из писем можно копировать в браузер.
- Каталог, корзина, оформление заказа (редирект на заглушку платежа).
- Админка и дашборд (товары, категории, заказы, пользователи, настройки, безопасность).

## Что не запущено при таком режиме

- **Celery и Redis** — фоновые задачи (например, отправка писем в фоне) не выполняются; письма при регистрации отправляются синхронно в консоль.
- **PostgreSQL** — должен быть установлен и запущен локально (в `.env`: `POSTGRES_HOST=localhost`).
- **Nginx и HTTPS** — доступ только по `http://127.0.0.1:8000/`.

---

## Остановка и повторный запуск

- Остановка: в терминале **Ctrl+C**.
- Повторный запуск: снова активируйте `venv`, при необходимости задайте переменные и выполните:
  ```bash
  python manage.py runserver
  ```

---

## Частые проблемы

1. **«No module named 'psycopg'» / «Error loading psycopg2 or psycopg»**  
   Установите драйвер PostgreSQL: `pip install "psycopg[binary]"`.

2. **Страницы без стилей**  
   Статика при `runserver` раздаётся Django. Если что-то не грузится, выполните:
   ```bash
   python manage.py collectstatic --noinput
   ```
   и проверьте `STATIC_URL` / `STATICFILES_DIRS` в настройках.

3. **Ошибки миграций**  
   Убедитесь, что находитесь в каталоге `backend` и виртуальное окружение активировано, затем:
   ```bash
   python manage.py migrate
   ```

4. **Не открывается админ-панель / дашборд**  
   Войдите под суперпользователем (флаг «Персонал»), созданным через `createsuperuser**.

**Перед выкладкой на прод** см. **DEPLOY_CHECKLIST.md**: там указаны collectstatic, раздача статики через Nginx (например из `/var/www/static/`), HTTPS и прочие пункты.

После этого можно спокойно тестировать и дорабатывать проект локально.
