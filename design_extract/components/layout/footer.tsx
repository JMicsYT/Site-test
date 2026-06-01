import Link from "next/link"
import { Package } from "lucide-react"

export function Footer() {
  return (
    <footer className="border-t border-border bg-card">
      <div className="container mx-auto px-4 py-12">
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div className="space-y-4">
            <Link href="/" className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                <Package className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold text-foreground">DigiStore</span>
            </Link>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Маркетплейс цифровых товаров. Шаблоны, софт, курсы и электронные книги от проверенных авторов.
            </p>
          </div>

          {/* Каталог */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Каталог</h3>
            <nav className="flex flex-col gap-2">
              <Link href="/catalog?category=templates" className="text-sm text-muted-foreground hover:text-foreground">
                Шаблоны
              </Link>
              <Link href="/catalog?category=software" className="text-sm text-muted-foreground hover:text-foreground">
                Софт
              </Link>
              <Link href="/catalog?category=courses" className="text-sm text-muted-foreground hover:text-foreground">
                Курсы
              </Link>
              <Link href="/catalog?category=ebooks" className="text-sm text-muted-foreground hover:text-foreground">
                Книги
              </Link>
            </nav>
          </div>

          {/* Компания */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Компания</h3>
            <nav className="flex flex-col gap-2">
              <Link href="/about" className="text-sm text-muted-foreground hover:text-foreground">
                О нас
              </Link>
              <Link href="/contact" className="text-sm text-muted-foreground hover:text-foreground">
                Контакты
              </Link>
              <Link href="/seller" className="text-sm text-muted-foreground hover:text-foreground">
                Стать продавцом
              </Link>
              <Link href="/blog" className="text-sm text-muted-foreground hover:text-foreground">
                Блог
              </Link>
            </nav>
          </div>

          {/* Поддержка */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Поддержка</h3>
            <nav className="flex flex-col gap-2">
              <Link href="/help" className="text-sm text-muted-foreground hover:text-foreground">
                Центр помощи
              </Link>
              <Link href="/faq" className="text-sm text-muted-foreground hover:text-foreground">
                FAQ
              </Link>
              <Link href="/terms" className="text-sm text-muted-foreground hover:text-foreground">
                Условия использования
              </Link>
              <Link href="/privacy" className="text-sm text-muted-foreground hover:text-foreground">
                Политика конфиденциальности
              </Link>
            </nav>
          </div>
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-border pt-8 md:flex-row">
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} DigiStore. Все права защищены.
          </p>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              Способы оплаты:
            </span>
            <div className="flex items-center gap-2">
              <div className="rounded bg-muted px-2 py-1 text-xs font-medium text-muted-foreground">Visa</div>
              <div className="rounded bg-muted px-2 py-1 text-xs font-medium text-muted-foreground">MasterCard</div>
              <div className="rounded bg-muted px-2 py-1 text-xs font-medium text-muted-foreground">МИР</div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}
