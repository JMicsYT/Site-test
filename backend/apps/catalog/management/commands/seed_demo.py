"""
Команда заполняет каталог демонстрационными категориями и товарами.
Генерирует красивые локальные SVG-обложки — не требует интернета.

Запуск:
    python manage.py seed_demo            # наполнить / обновить
    python manage.py seed_demo --reset    # сбросить и заполнить заново
"""
import hashlib
import os
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.catalog.models import Category, Product, ProductMedia


CATEGORIES = [
    {"name": "Игры", "slug": "games", "icon": "🎮", "color": "#10b981",
     "description": "Ключи и цифровые версии игр для всех платформ.",
     "featured": True, "sort_order": 1},
    {"name": "Программы", "slug": "software", "icon": "💻", "color": "#3b82f6",
     "description": "Лицензии на ПО: офисные пакеты, дизайн, разработка.",
     "featured": True, "sort_order": 2},
    {"name": "Онлайн-курсы", "slug": "courses", "icon": "🎓", "color": "#f59e0b",
     "description": "Курсы и видеоматериалы от экспертов отрасли.",
     "featured": True, "sort_order": 3},
    {"name": "Подписки", "slug": "subscriptions", "icon": "📦", "color": "#a855f7",
     "description": "Музыка, видео, облачные сервисы и стриминговые платформы.",
     "featured": True, "sort_order": 4},
    {"name": "Медиа-контент", "slug": "media", "icon": "🎬", "color": "#ec4899",
     "description": "Фильмы, музыка, электронные книги и аудиокниги.",
     "sort_order": 5},
    {"name": "Графика и ассеты", "slug": "assets", "icon": "🎨", "color": "#06b6d4",
     "description": "3D-модели, шрифты, иконки, пресеты, шаблоны.",
     "sort_order": 6},
]


# (cat_slug, ptype, license, purpose, emoji, name, short_desc, price, discount, featured)
PRODUCTS = [
    ("games", "game", "perpetual", "personal", "🌆",
     "Cyberpunk 2077 — Steam ключ",
     "Эпический научно-фантастический экшен-RPG в открытом мире Найт-Сити.",
     1999.00, 1299.00, True),
    ("games", "game", "perpetual", "personal", "⚔️",
     "The Witcher 3: Wild Hunt",
     "Легендарная RPG в огромном открытом мире с дополнениями.",
     899.00, None, True),
    ("games", "game", "perpetual", "personal", "🤠",
     "Red Dead Redemption 2",
     "Эпическая история о банде вне закона в закате Дикого Запада.",
     2499.00, 1799.00, False),
    ("games", "game", "perpetual", "personal", "🗡️",
     "Elden Ring — PC Digital",
     "Масштабная dark-fantasy RPG от создателей Dark Souls.",
     3299.00, None, True),
    ("games", "game", "perpetual", "personal", "🧙",
     "Hogwarts Legacy",
     "Откройте тайны магического мира во вселенной Гарри Поттера.",
     2999.00, 2299.00, False),
    ("games", "game", "perpetual", "personal", "🚗",
     "GTA V Premium Edition",
     "Нестареющая классика: Лос-Сантос и бесконечные приключения.",
     1499.00, None, False),
    ("games", "game", "perpetual", "personal", "🎯",
     "Counter-Strike 2 — Prime",
     "Легендарный онлайн-шутер с Prime-статусом и скинами.",
     899.00, 599.00, False),
    ("games", "game", "perpetual", "personal", "🧟",
     "The Last of Us Part I",
     "Ремейк культовой постапокалиптической истории.",
     3499.00, None, False),

    ("software", "software", "subscription", "business", "🎨",
     "Adobe Creative Cloud — 1 год",
     "Полный пакет Adobe: Photoshop, Illustrator, Premiere Pro и ещё 20 приложений.",
     54990.00, 42990.00, True),
    ("software", "software", "perpetual", "business", "📊",
     "Microsoft Office 2021 Pro",
     "Бессрочная лицензия на офисный пакет: Word, Excel, PowerPoint, Outlook.",
     8990.00, None, True),
    ("software", "software", "subscription", "personal", "📝",
     "Microsoft 365 Personal",
     "Годовая подписка на Office, 1 ТБ OneDrive и расширенные функции.",
     5990.00, 4490.00, False),
    ("software", "software", "subscription", "business", "⚙️",
     "JetBrains All Products Pack",
     "Подписка на все IDE: IntelliJ IDEA, PyCharm, WebStorm и другие.",
     24990.00, None, True),
    ("software", "software", "perpetual", "personal", "🖌️",
     "Figma Professional — 1 место",
     "Профессиональная лицензия на Figma для дизайна интерфейсов.",
     14990.00, 11990.00, False),
    ("software", "software", "perpetual", "business", "🛡️",
     "Kaspersky Total Security",
     "Защита от вирусов и угроз на 3 устройства, 1 год.",
     2990.00, 1990.00, False),

    ("courses", "course", "perpetual", "personal", "🐍",
     "Python с нуля до Middle-разработчика",
     "Большой курс: синтаксис, ООП, веб, базы данных, 12 проектов в портфолио.",
     19990.00, 12990.00, True),
    ("courses", "course", "perpetual", "personal", "⚛️",
     "Frontend: React + TypeScript",
     "Современная разработка интерфейсов: хуки, Redux Toolkit, Next.js, тестирование.",
     15990.00, None, True),
    ("courses", "course", "perpetual", "personal", "✏️",
     "UX/UI-дизайн — Figma Master",
     "От исследования до прототипа: UX, визуал, дизайн-системы и кейсы.",
     11990.00, 8990.00, False),
    ("courses", "course", "perpetual", "business", "🌐",
     "Английский для IT — Intermediate+",
     "Грамматика, техническая лексика, собеседования, живые диалоги.",
     9990.00, None, False),
    ("courses", "course", "perpetual", "personal", "🤖",
     "Data Science и Machine Learning",
     "Pandas, NumPy, scikit-learn, нейросети и реальные проекты с Kaggle.",
     24990.00, 18990.00, True),
    ("courses", "course", "perpetual", "personal", "📱",
     "Мобильная разработка: Flutter",
     "Создание кроссплатформенных приложений на Dart + Flutter.",
     13990.00, None, False),

    ("subscriptions", "software", "subscription", "personal", "🎵",
     "Spotify Premium — 12 мес.",
     "Музыка без рекламы, офлайн, любые треки — подписка на год.",
     2990.00, 1990.00, True),
    ("subscriptions", "software", "subscription", "personal", "📺",
     "YouTube Premium — 12 мес.",
     "Видео без рекламы, фоновое воспроизведение, YouTube Music.",
     3490.00, None, False),
    ("subscriptions", "software", "subscription", "personal", "🎬",
     "Netflix Premium — 6 мес.",
     "Фильмы и сериалы в 4K на нескольких устройствах.",
     4990.00, 3990.00, True),
    ("subscriptions", "software", "subscription", "business", "🤖",
     "GitHub Copilot — 1 год",
     "ИИ-ассистент для разработчиков. Ускорьте написание кода в 2 раза.",
     9990.00, None, True),
    ("subscriptions", "software", "subscription", "personal", "☁️",
     "Google One — 2 ТБ на 1 год",
     "Облачное хранилище и дополнительные возможности аккаунта.",
     3990.00, None, False),

    ("media", "media", "perpetual", "personal", "🎥",
     "Dune: Часть первая (4K)",
     "Эпическая научная фантастика Дени Вильнёва. Формат 4K с HDR.",
     599.00, 399.00, False),
    ("media", "media", "perpetual", "personal", "🎧",
     "Альбом: Bohemian Rhapsody (FLAC)",
     "Классический альбом Queen в качестве lossless FLAC.",
     499.00, None, False),
    ("media", "media", "perpetual", "personal", "📖",
     "Электронная книга «Чистый код»",
     "Роберт Мартин — классика программирования. EPUB + PDF.",
     799.00, 499.00, False),
    ("media", "media", "perpetual", "personal", "🎙️",
     "Аудиокнига «Атомные привычки»",
     "Бестселлер Джеймса Клира в озвучке профессионального чтеца.",
     699.00, 449.00, False),

    ("assets", "asset", "perpetual", "business", "🔷",
     "Пак 500 векторных иконок",
     "Современные иконки в SVG и PNG. Коммерческое использование разрешено.",
     1990.00, 990.00, False),
    ("assets", "asset", "perpetual", "business", "🎞️",
     "Сборник LUT для цветокоррекции",
     "30 профессиональных LUT-пресетов для видео и фото.",
     2490.00, None, False),
    ("assets", "asset", "perpetual", "business", "🏙️",
     "3D-модели: Low-Poly City Pack",
     "200+ моделей города: здания, транспорт, детали. FBX, OBJ, GLTF.",
     4990.00, 3490.00, True),
    ("assets", "asset", "perpetual", "business", "🔤",
     "Шрифтовой пак Modern Sans",
     "15 современных шрифтов с расширенной кириллицей и лигатурами.",
     1490.00, 890.00, False),
]


# Палитра для градиентных обложек товара (hex цвета A -> B)
GRADIENT_PALETTES = [
    ("#6366f1", "#8b5cf6"),  # индиго -> фиолет
    ("#10b981", "#14b8a6"),  # зелёный -> бирюзовый
    ("#f59e0b", "#ef4444"),  # оранжевый -> красный
    ("#ec4899", "#8b5cf6"),  # розовый -> фиолет
    ("#3b82f6", "#06b6d4"),  # синий -> циан
    ("#8b5cf6", "#ec4899"),  # фиолет -> розовый
    ("#0ea5e9", "#6366f1"),  # голубой -> индиго
    ("#f43f5e", "#f59e0b"),  # красный -> янтарный
]


def pick_palette(name: str) -> tuple[str, str]:
    """Стабильный выбор палитры по хешу имени."""
    h = int(hashlib.md5(name.encode("utf-8")).hexdigest(), 16)
    return GRADIENT_PALETTES[h % len(GRADIENT_PALETTES)]


def make_cover_svg(name: str, emoji: str, subtitle: str = "") -> bytes:
    """Генерирует SVG-обложку 800x600 с градиентом, emoji и названием."""
    color_a, color_b = pick_palette(name)
    # Экранируем XML-спец символы
    def esc(s: str) -> str:
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    title = esc(name)
    if len(title) > 38:
        title = title[:37] + "…"
    sub = esc(subtitle)
    if len(sub) > 52:
        sub = sub[:51] + "…"

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{color_a}"/>
      <stop offset="100%" stop-color="{color_b}"/>
    </linearGradient>
    <radialGradient id="spot" cx="75%" cy="20%" r="60%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <pattern id="dots" width="40" height="40" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="1.2" fill="#ffffff" fill-opacity="0.12"/>
    </pattern>
  </defs>
  <rect width="800" height="600" fill="url(#g)"/>
  <rect width="800" height="600" fill="url(#dots)"/>
  <rect width="800" height="600" fill="url(#spot)"/>
  <g font-family="'Segoe UI Emoji','Apple Color Emoji','Noto Color Emoji',system-ui,sans-serif">
    <text x="400" y="300" text-anchor="middle" font-size="200" dominant-baseline="middle">{esc(emoji)}</text>
  </g>
  <g font-family="Inter,system-ui,-apple-system,Segoe UI,sans-serif" fill="#ffffff">
    <text x="48" y="520" font-size="36" font-weight="700" letter-spacing="-0.5">{title}</text>
    <text x="48" y="560" font-size="20" font-weight="500" opacity="0.85">{sub}</text>
  </g>
  <g font-family="Inter,sans-serif" fill="#ffffff">
    <rect x="48" y="48" width="110" height="36" rx="18" fill="#ffffff" fill-opacity="0.18"/>
    <text x="103" y="71" text-anchor="middle" font-size="15" font-weight="600" letter-spacing="0.5">SHOSHOP</text>
  </g>
</svg>'''
    return svg.encode("utf-8")


def make_category_svg(name: str, icon: str, color: str = "#4f46e5") -> bytes:
    def esc(s: str) -> str:
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="400" height="400">
  <rect width="400" height="400" fill="{esc(color)}"/>
  <g font-family="'Segoe UI Emoji','Apple Color Emoji','Noto Color Emoji',sans-serif">
    <text x="200" y="230" text-anchor="middle" font-size="180">{esc(icon)}</text>
  </g>
</svg>'''
    return svg.encode("utf-8")


def ensure_media_dir(subdir: str) -> Path:
    path = Path(settings.MEDIA_ROOT) / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_svg(subdir: str, filename: str, content: bytes) -> str:
    """Сохраняет SVG в MEDIA_ROOT/subdir/filename и возвращает абсолютный URL."""
    out_dir = ensure_media_dir(subdir)
    out_file = out_dir / filename
    with open(out_file, "wb") as f:
        f.write(content)
    return f"{settings.MEDIA_URL}{subdir}/{filename}"


def long_description(name: str, short: str) -> str:
    return (
        f"{short}\n\n"
        f"«{name}» — это качественный цифровой продукт, доступный сразу после оплаты.\n"
        "Что входит:\n"
        "• Полный доступ к продукту без ограничений\n"
        "• Оригинальный ключ / файл / лицензия\n"
        "• Подробная инструкция по активации\n"
        "• Поддержка при возникновении вопросов\n\n"
        "Как это работает:\n"
        "1. Оплачиваете заказ любым удобным способом\n"
        "2. Ключ и инструкция приходят на почту и в личный кабинет\n"
        "3. Активируете продукт по инструкции и пользуетесь\n\n"
        "Если возникнут вопросы — напишите нам в чат поддержки, ответим быстро."
    )


class Command(BaseCommand):
    help = "Заполняет каталог демонстрационными товарами и категориями с локальными SVG-обложками."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Удалить существующие товары/медиа/категории перед заполнением.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write(self.style.WARNING("Сброс каталога..."))
            ProductMedia.objects.all().delete()
            for p in Product.objects.all():
                try:
                    p.delete()
                except Exception:
                    self.stdout.write(self.style.WARNING(
                        f"  Пропущен товар с заказами: {p.name}"
                    ))
            for c in Category.objects.all():
                if not c.products.exists():
                    c.delete()

        ensure_media_dir("product_covers")
        ensure_media_dir("category_covers")

        # Категории
        cats_map = {}
        for data in CATEGORIES:
            slug = data["slug"]
            img = save_svg(
                "category_covers", f"{slug}.svg",
                make_category_svg(data["name"], data.get("icon", ""), data.get("color", "#4f46e5")),
            )
            cat, created = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": data["name"],
                    "icon": data.get("icon", ""),
                    "color": data.get("color", "#4f46e5"),
                    "description": data.get("description", ""),
                    "featured": data.get("featured", False),
                    "sort_order": data.get("sort_order", 0),
                    "image_url": img,
                },
            )
            cats_map[slug] = cat
            self.stdout.write(f"  {'+' if created else '~'} Категория: {cat.name}")

        # Товары
        created_count = 0
        for (cat_slug, ptype, license_t, purpose, emoji, name, short_desc,
             price, discount, featured) in PRODUCTS:
            slug = slugify(name, allow_unicode=False)
            if not slug:
                slug = f"product-{abs(hash(name))}"
            cat = cats_map[cat_slug]
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    "category": cat,
                    "name": name,
                    "short_description": short_desc,
                    "description": long_description(name, short_desc),
                    "price": Decimal(str(price)),
                    "discount_price": Decimal(str(discount)) if discount else None,
                    "product_type": ptype,
                    "license_type": license_t,
                    "purpose": purpose,
                    "status": Product.Status.ACTIVE,
                    "is_featured": featured,
                },
            )
            if created:
                created_count += 1

            # Обложка
            img_url = save_svg(
                "product_covers",
                f"{slug}.svg",
                make_cover_svg(name, emoji, cat.name),
            )
            # Оставляем только один актуальный медиа на товар
            product.media.all().delete()
            ProductMedia.objects.create(
                product=product,
                media_type=ProductMedia.MediaType.IMAGE,
                url=img_url,
                sort_order=0,
            )

        # Сброс кэша
        from django.core.cache import cache
        cache.clear()

        self.stdout.write(self.style.SUCCESS(
            f"\nГотово! Категорий: {len(CATEGORIES)}, товаров: {len(PRODUCTS)} "
            f"(новых: {created_count}). Все обложки — локальные SVG."
        ))
