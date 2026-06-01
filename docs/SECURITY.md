# Безопасность ShoShop — соответствие OWASP Top-10 (2021)

Документ описывает, как в проекте ShoShop реализованы механизмы защиты от
десяти самых распространённых классов уязвимостей по OWASP Top-10 (2021).
Это приложение разрабатывалось как дипломный проект **«Защищённая веб-платформа
продажи цифровых товаров»**, поэтому безопасность рассматривалась на всех этапах:
от архитектуры (слои view/service/model) до конкретных деталей (заголовки, куки,
хэши, шифрование, аудит-журналы).

---

## A01:2021 — Broken Access Control (Нарушение контроля доступа)

**Риск:** Пользователь видит/изменяет чужие ресурсы (IDOR), поднимает привилегии.

**Меры в ShoShop:**
- Все защищённые view используют `@login_required` / `LoginRequiredMixin`.
- `OwnerRequiredMixin` (`apps.core.permissions`) проверяет, что объект принадлежит
  текущему пользователю; возвращает 404 (не 403) — чтобы не раскрывать
  существование объекта.
- Все личные данные (заказы, доступы) фильтруются **по user** в `get_queryset()`.
- Цифровые товары НЕ отдаются в списках: для получения значения пользователь
  должен явно запросить **одноразовую подписанную ссылку** (TimestampSigner,
  TTL=15 мин, лимит использований) — см. `apps.orders.downloads`.
- Админка защищена стандартным Django-permission-фреймворком
  (`is_staff` + группы). Дашборд админа — собственные view с `user.is_staff`.

---

## A02:2021 — Cryptographic Failures (Ошибки криптографии)

**Риск:** Данные в открытом виде, слабые алгоритмы, отсутствие HTTPS.

**Меры:**
- **Пароли:** хэш PBKDF2-SHA256 (Django по умолчанию), 600 000 итераций.
- **Цифровые ключи (DigitalItem.value):** симметричное шифрование
  **Fernet (AES-128-CBC + HMAC-SHA256)**, ключ `FIELD_ENCRYPTION_KEY` из ENV.
  Даже дамп БД не раскрывает купленные ключи/коды.
- **2FA:** TOTP (RFC 6238), 160-битный секрет из `secrets.SystemRandom`,
  окно ±1 шаг (30 с) для компенсации расхождения часов.
- **Backup-коды:** 10 одноразовых кодов, хранятся только в хэшированном виде.
- **CSRF-token:** включён для всех форм; cookies с `HttpOnly`, `Secure`
  (в продакшене), `SameSite=Lax`.
- **HSTS** (`SECURE_HSTS_SECONDS=31536000`), `SECURE_SSL_REDIRECT=True` в проде,
  `SECURE_PROXY_SSL_HEADER` — для работы за reverse-proxy.
- **Подписанные ссылки** (Django `TimestampSigner` / HMAC-SHA256) — для выдачи
  цифрового товара и для подписи платёжных callback.

---

## A03:2021 — Injection (Инъекции)

**Риск:** SQL-injection, XSS, command injection.

**Меры:**
- **SQL:** повсеместно используется Django ORM (параметризованные запросы).
  Сырого SQL нет.
- **XSS:** Django-шаблоны экранируют контент по умолчанию; `|safe` не
  применяется к пользовательскому контенту.
- **Content Security Policy (CSP):** middleware (`apps.core.middleware.
  SecurityHeadersMiddleware`) отдаёт заголовок CSP с `default-src 'self'`,
  `frame-ancestors 'none'`, `object-src 'none'`.
- **Входные данные в формах** валидируются Django Forms (типы, длины, наборы).
- **Капча** на регистрации/сбросе пароля — защита от автоматизированных
  инъекций через массовую регистрацию.

---

## A04:2021 — Insecure Design (Небезопасный дизайн)

**Риск:** Архитектура позволяет обходить защиту, отсутствуют лимиты.

**Меры:**
- **Rate-limiting:** middleware `LoginRateLimitMiddleware` ограничивает частоту
  логина/регистрации/сброса пароля по IP (5 попыток за 5 минут).
- **Account lockout:** после N неудачных попыток (`ACCOUNT_LOCKOUT_MAX_FAILURES=10`)
  аккаунт блокируется на 30 минут, пользователь получает письмо с
  одноразовой ссылкой разблокировки.
- **Принцип минимальных привилегий:** роли (`USER`, `STAFF`, `ADMIN`)
  разделены, каждое админ-действие пишется в аудит-журнал.
- **Idempotent payment callback:** `select_for_update()` + проверка статуса
  гарантируют, что повторный callback не выдаст товар дважды.
- **Двухфакторная аутентификация:** защищает от утечек паролей — даже зная
  пароль, злоумышленник не зайдёт без TOTP-кода.

---

## A05:2021 — Security Misconfiguration (Небезопасная конфигурация)

**Риск:** DEBUG=True в проде, `ALLOWED_HOSTS=*`, стандартные пароли,
незакрытые заголовки.

**Меры:**
- `DEBUG=False` управляется через ENV, по умолчанию False.
- `ALLOWED_HOSTS` читается из `DJANGO_ALLOWED_HOSTS`.
- В проде: `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`
  автоматически `True`, `X-Frame-Options: DENY`.
- Безопасные заголовки (middleware `SecurityHeadersMiddleware`):
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy`: запрет geolocation/mic/camera/payment/usb
  - `Content-Security-Policy` (см. A03)
  - `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy`
- PostgreSQL-only: SQLite отключён на уровне настроек (`ImproperlyConfigured`
  если кто-то попытался подставить).

---

## A06:2021 — Vulnerable and Outdated Components (Уязвимые компоненты)

**Риск:** Устаревшие библиотеки с известными CVE.

**Меры:**
- `requirements.txt` фиксирует минорные версии основных пакетов
  (Django 5.0.x, DRF 3.15.x, Celery 5.3.x).
- Регулярный запуск `pip list --outdated` и `safety check` (рекомендуется в CI).
- Использование только активно поддерживаемых LTS-веток (Django 5.0, Python 3.12+).

---

## A07:2021 — Identification and Authentication Failures

**Риск:** Слабая аутентификация, обход, brute-force.

**Меры:**
- **Парольная политика:** Django-валидаторы + проверка через **HIBP
  (Have I Been Pwned)** с k-anonymity — пароль из утечек запрещается.
- **2FA через TOTP** — опционально для пользователя, настраивается в профиле.
- **Защита от user enumeration:** все сообщения об ошибках логина/сброса
  пароля — одинаковые, вне зависимости от того, существует ли email.
- **Session management:** стандартные Django-сессии, `SESSION_COOKIE_AGE`
  настраивается, `update_session_auth_hash` при смене пароля.
- **Email-верификация** обязательна для покупки
  (`REQUIRE_EMAIL_VERIFIED_FOR_PURCHASE`).

---

## A08:2021 — Software and Data Integrity Failures

**Риск:** Tamper данных, replay-атаки, неверифицированные обновления.

**Меры:**
- **Подписанные callback платёжных систем** с HMAC-SHA256
  (`apps.payments.api_urls._verify_callback_secret`):
  - заголовок `X-Signature` — hex HMAC по `"{ts}.{body}"`;
  - `X-Timestamp` — окно валидности 5 минут (защита от replay);
  - nonce кешируется на время окна — один callback = одно применение.
- **Подписанные ссылки на скачивание** — невозможно подделать без `SECRET_KEY`.
- **Soft-delete** для критических сущностей (`Product`, `Order`) — данные
  не теряются, можно восстановить.

---

## A09:2021 — Security Logging and Monitoring Failures

**Риск:** Инциденты не фиксируются, расследование невозможно.

**Меры:**
- **Единая точка логирования безопасности** — `apps.core.audit.log_event`:
  пишет в БД (`SecurityEvent`) и в файл `logs/security.log` (JSON).
- **Событий 20+:** `login_success`, `login_failed`, `logout`, `register`,
  `password_change`, `password_reset_request`, `email_verified`,
  `twofa_enabled/disabled/failed`, `account_locked/unlocked`,
  `order_paid`, `order_cancelled`, `payment_callback_ok/fail`,
  `digital_download`, `admin_action`, `suspicious_activity`.
- **DownloadAudit:** отдельная таблица, фиксирует каждое обращение к
  цифровому товару (успешное или отказ).
- **Пользователь видит свою историю** на странице «Безопасность»:
  время, тип события, IP, User-Agent.
- **Ротация логов** (RotatingFileHandler): 10 МБ × 5 копий для security,
  20 МБ × 5 для приложения.
- **Формат JSON:** легко парсится ELK/Loki/Grafana.

---

## A10:2021 — Server-Side Request Forgery (SSRF)

**Риск:** Сервер делает запросы на внутренние ресурсы по данным пользователя.

**Меры:**
- В приложении практически отсутствуют сценарии, где URL для исходящего
  запроса берётся из ввода пользователя.
- Единственный внешний запрос — HIBP API (`api.pwnedpasswords.com`),
  URL жёстко зашит в код, передаётся только SHA1-префикс пароля.
- Платёжные callback — только входящие, собственные URL настраиваются
  из ENV администратором.

---

## Организационные меры (поверх OWASP)

### ФЗ-152 «О персональных данных»
- Политика конфиденциальности (`/privacy/`) описывает состав ПДн,
  цели обработки, права субъекта.
- Хранение ПДн на серверах в РФ (рекомендация для продакшена).
- Журналирование доступа к ПДн (через `SecurityEvent` + `DownloadAudit`).

### Резервное копирование
- Команда `python manage.py dump_db` создаёт зашифрованный дамп:
  `pg_dump -Fc -Z9` (если доступен) или `dumpdata | gzip` (fallback).
- Рекомендуется настроить cron: `0 3 * * * python manage.py dump_db --out /backups`.

### Тесты безопасности
- `apps/tests/test_security.py` покрывает 15+ сценариев: lockout, 2FA,
  enumeration, signed links, HMAC callback, access control.

---

## Как включить/настроить

```bash
# Обязательные секреты
DJANGO_SECRET_KEY=<50+ случайных символов>
FIELD_ENCRYPTION_KEY=<любая длинная фраза; используется как основа ключа Fernet>
DOWNLOAD_LINK_SECRET=<любая длинная фраза; отдельный ключ для подписи ссылок>
PAYMENT_CALLBACK_SECRET=<из личного кабинета платёжного провайдера>

# Безопасность
HIBP_CHECK_ENABLED=true
ACCOUNT_LOCKOUT_MAX_FAILURES=10
ACCOUNT_LOCKOUT_DURATION=1800
CSP_ENABLED=true

# Production
DJANGO_DEBUG=false
DJANGO_SECURE_SSL_REDIRECT=true
SECURE_PROXY_SSL_HEADER=true  # если за nginx
```
