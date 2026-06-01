import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ProductCard, type Product } from "@/components/product-card"
import { ArrowRight } from "lucide-react"

// Placeholder данные - будут заменены на данные из Django API
const featuredProducts: Product[] = [
  {
    id: "1",
    title: "SaaS Dashboard UI Kit",
    description: "Полный набор компонентов для создания современных дашбордов",
    price: 4990,
    originalPrice: 7990,
    image: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=600&fit=crop",
    category: "Шаблоны",
    rating: 4.9,
    reviewCount: 128,
    author: "DesignPro",
    featured: true,
  },
  {
    id: "2",
    title: "Курс по Python для начинающих",
    description: "Изучите Python с нуля до профессионального уровня",
    price: 2990,
    image: "https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=800&h=600&fit=crop",
    category: "Курсы",
    rating: 4.8,
    reviewCount: 256,
    author: "CodeMaster",
  },
  {
    id: "3",
    title: "E-commerce Starter Kit",
    description: "Готовый шаблон интернет-магазина на Next.js",
    price: 6990,
    originalPrice: 9990,
    image: "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=800&h=600&fit=crop",
    category: "Шаблоны",
    rating: 4.7,
    reviewCount: 89,
    author: "WebStudio",
    featured: true,
  },
  {
    id: "4",
    title: "Полное руководство по UX/UI",
    description: "Всё о дизайне пользовательских интерфейсов в одной книге",
    price: 1490,
    image: "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=800&h=600&fit=crop",
    category: "Книги",
    rating: 4.9,
    reviewCount: 342,
    author: "DesignBook",
  },
]

export function FeaturedProducts() {
  return (
    <section className="py-16">
      <div className="container mx-auto px-4">
        <div className="mb-10 flex items-center justify-between">
          <div>
            <h2 className="mb-2 text-3xl font-bold text-foreground">Популярные товары</h2>
            <p className="text-muted-foreground">
              Топ продаж за последний месяц
            </p>
          </div>
          <Link href="/catalog">
            <Button variant="outline" className="hidden gap-2 md:flex">
              Смотреть все
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {featuredProducts.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>

        <div className="mt-8 text-center md:hidden">
          <Link href="/catalog">
            <Button variant="outline" className="gap-2">
              Смотреть все товары
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </div>
    </section>
  )
}
