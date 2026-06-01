"use client"

import { useState } from "react"
import Image from "next/image"
import Link from "next/link"
import { Header } from "@/components/layout/header"
import { Footer } from "@/components/layout/footer"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Card, CardContent } from "@/components/ui/card"
import { ProductCard, type Product } from "@/components/product-card"
import {
  Star,
  ShoppingCart,
  Heart,
  Share2,
  Download,
  Shield,
  Clock,
  CheckCircle,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
} from "lucide-react"

// Placeholder данные - будут заменены на данные из Django API
const product = {
  id: "1",
  title: "SaaS Dashboard UI Kit",
  description:
    "Полный набор компонентов для создания современных дашбордов. Включает более 200 готовых компонентов, тёмную и светлую темы, адаптивный дизайн.",
  fullDescription: `
## О продукте

SaaS Dashboard UI Kit — это профессиональный набор компонентов, созданный для разработчиков и дизайнеров, которые хотят быстро создавать современные дашборды.

### Что включено:

- **200+ компонентов** — кнопки, формы, таблицы, графики, карточки и многое другое
- **Тёмная и светлая тема** — полная поддержка обеих цветовых схем
- **Адаптивный дизайн** — отлично выглядит на всех устройствах
- **Figma файлы** — исходные макеты для кастомизации
- **React компоненты** — готовый к использованию код
- **Документация** — подробные инструкции по использованию

### Технологии:

- React 18+
- TypeScript
- Tailwind CSS
- shadcn/ui

### Поддержка:

Мы предоставляем 6 месяцев технической поддержки и бесплатные обновления.
  `,
  price: 4990,
  originalPrice: 7990,
  images: [
    "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&h=800&fit=crop",
    "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200&h=800&fit=crop",
    "https://images.unsplash.com/photo-1504868584819-f8e8b4b6d7e3?w=1200&h=800&fit=crop",
  ],
  category: "Шаблоны",
  rating: 4.9,
  reviewCount: 128,
  salesCount: 1560,
  author: {
    name: "DesignPro",
    avatar: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop",
    rating: 4.9,
    productsCount: 24,
    sales: 12500,
  },
  features: [
    "200+ готовых компонентов",
    "Figma + React код",
    "Тёмная и светлая тема",
    "6 месяцев поддержки",
    "Бесплатные обновления",
    "Коммерческая лицензия",
  ],
  files: [
    { name: "dashboard-ui-kit.zip", size: "45.2 MB" },
    { name: "documentation.pdf", size: "2.1 MB" },
  ],
  reviews: [
    {
      id: "1",
      author: "Алексей К.",
      avatar: "",
      rating: 5,
      date: "2 дня назад",
      text: "Отличный UI Kit! Сэкономил мне недели работы. Компоненты качественные и хорошо документированы.",
    },
    {
      id: "2",
      author: "Мария С.",
      avatar: "",
      rating: 5,
      date: "1 неделю назад",
      text: "Очень довольна покупкой. Поддержка отвечает быстро, всё работает как надо.",
    },
    {
      id: "3",
      author: "Дмитрий В.",
      avatar: "",
      rating: 4,
      date: "2 недели назад",
      text: "Хороший набор, но хотелось бы больше примеров использования.",
    },
  ],
}

const relatedProducts: Product[] = [
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
  },
  {
    id: "6",
    title: "Mobile App UI Kit",
    description: "200+ экранов для iOS и Android приложений",
    price: 3990,
    originalPrice: 5990,
    image: "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=800&h=600&fit=crop",
    category: "Шаблоны",
    rating: 4.8,
    reviewCount: 156,
    author: "MobileFirst",
  },
]

export default function ProductPage() {
  const [currentImage, setCurrentImage] = useState(0)
  const [isWishlisted, setIsWishlisted] = useState(false)

  const discount = product.originalPrice
    ? Math.round((1 - product.price / product.originalPrice) * 100)
    : 0

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 bg-background">
        <div className="container mx-auto px-4 py-8">
          {/* Breadcrumb */}
          <nav className="mb-6 flex items-center gap-2 text-sm text-muted-foreground">
            <Link href="/" className="hover:text-foreground">
              Главная
            </Link>
            <span>/</span>
            <Link href="/catalog" className="hover:text-foreground">
              Каталог
            </Link>
            <span>/</span>
            <Link href="/catalog?category=templates" className="hover:text-foreground">
              {product.category}
            </Link>
            <span>/</span>
            <span className="text-foreground">{product.title}</span>
          </nav>

          <div className="grid gap-8 lg:grid-cols-2">
            {/* Image Gallery */}
            <div className="space-y-4">
              <div className="relative aspect-[4/3] overflow-hidden rounded-xl bg-muted">
                <Image
                  src={product.images[currentImage]}
                  alt={product.title}
                  fill
                  className="object-cover"
                />
                {product.images.length > 1 && (
                  <>
                    <Button
                      variant="secondary"
                      size="icon"
                      className="absolute left-4 top-1/2 -translate-y-1/2"
                      onClick={() =>
                        setCurrentImage((prev) =>
                          prev === 0 ? product.images.length - 1 : prev - 1
                        )
                      }
                    >
                      <ChevronLeft className="h-5 w-5" />
                    </Button>
                    <Button
                      variant="secondary"
                      size="icon"
                      className="absolute right-4 top-1/2 -translate-y-1/2"
                      onClick={() =>
                        setCurrentImage((prev) =>
                          prev === product.images.length - 1 ? 0 : prev + 1
                        )
                      }
                    >
                      <ChevronRight className="h-5 w-5" />
                    </Button>
                  </>
                )}
              </div>
              <div className="flex gap-3">
                {product.images.map((image, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentImage(index)}
                    className={`relative aspect-[4/3] w-24 overflow-hidden rounded-lg border-2 transition-colors ${
                      currentImage === index ? "border-primary" : "border-border"
                    }`}
                  >
                    <Image src={image} alt="" fill className="object-cover" />
                  </button>
                ))}
              </div>
            </div>

            {/* Product Info */}
            <div>
              <div className="mb-4 flex items-center gap-3">
                <Badge variant="secondary">{product.category}</Badge>
                {discount > 0 && (
                  <Badge className="bg-destructive text-destructive-foreground">
                    -{discount}%
                  </Badge>
                )}
              </div>

              <h1 className="mb-4 text-3xl font-bold text-foreground">{product.title}</h1>

              <div className="mb-4 flex items-center gap-4">
                <div className="flex items-center gap-1">
                  <Star className="h-5 w-5 fill-chart-4 text-chart-4" />
                  <span className="font-semibold text-foreground">{product.rating}</span>
                  <span className="text-muted-foreground">({product.reviewCount} отзывов)</span>
                </div>
                <span className="text-muted-foreground">
                  {product.salesCount.toLocaleString("ru-RU")} продаж
                </span>
              </div>

              <p className="mb-6 text-muted-foreground leading-relaxed">{product.description}</p>

              {/* Price */}
              <div className="mb-6 flex items-baseline gap-3">
                <span className="text-4xl font-bold text-foreground">
                  {product.price.toLocaleString("ru-RU")} ₽
                </span>
                {product.originalPrice && (
                  <span className="text-xl text-muted-foreground line-through">
                    {product.originalPrice.toLocaleString("ru-RU")} ₽
                  </span>
                )}
              </div>

              {/* Actions */}
              <div className="mb-6 flex flex-wrap gap-3">
                <Button size="lg" className="flex-1 gap-2">
                  <ShoppingCart className="h-5 w-5" />
                  Добавить в корзину
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  onClick={() => setIsWishlisted(!isWishlisted)}
                  className={isWishlisted ? "text-destructive" : ""}
                >
                  <Heart className={`h-5 w-5 ${isWishlisted ? "fill-current" : ""}`} />
                </Button>
                <Button size="lg" variant="outline">
                  <Share2 className="h-5 w-5" />
                </Button>
              </div>

              {/* Features */}
              <div className="mb-6 grid grid-cols-2 gap-3">
                {product.features.map((feature, index) => (
                  <div key={index} className="flex items-center gap-2 text-sm text-foreground">
                    <CheckCircle className="h-4 w-4 text-accent" />
                    {feature}
                  </div>
                ))}
              </div>

              {/* Trust Badges */}
              <div className="flex flex-wrap gap-4 rounded-lg border border-border bg-muted/30 p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Download className="h-4 w-4 text-primary" />
                  Мгновенная доставка
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Shield className="h-4 w-4 text-primary" />
                  Безопасная оплата
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="h-4 w-4 text-primary" />
                  Поддержка 24/7
                </div>
              </div>

              {/* Author */}
              <Card className="mt-6">
                <CardContent className="flex items-center gap-4 p-4">
                  <Avatar className="h-14 w-14">
                    <AvatarImage src={product.author.avatar} />
                    <AvatarFallback>{product.author.name[0]}</AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <Link
                      href={`/author/${product.author.name}`}
                      className="font-semibold text-foreground hover:text-primary"
                    >
                      {product.author.name}
                    </Link>
                    <div className="flex items-center gap-3 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Star className="h-4 w-4 fill-chart-4 text-chart-4" />
                        {product.author.rating}
                      </div>
                      <span>{product.author.productsCount} товаров</span>
                      <span>{product.author.sales.toLocaleString("ru-RU")} продаж</span>
                    </div>
                  </div>
                  <Button variant="outline" size="sm">
                    <MessageSquare className="mr-2 h-4 w-4" />
                    Написать
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Tabs */}
          <Tabs defaultValue="description" className="mt-12">
            <TabsList className="w-full justify-start">
              <TabsTrigger value="description">Описание</TabsTrigger>
              <TabsTrigger value="files">Файлы</TabsTrigger>
              <TabsTrigger value="reviews">Отзывы ({product.reviews.length})</TabsTrigger>
            </TabsList>

            <TabsContent value="description" className="mt-6">
              <div className="prose prose-neutral max-w-none dark:prose-invert">
                <div className="whitespace-pre-line text-foreground">
                  {product.fullDescription}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="files" className="mt-6">
              <div className="space-y-3">
                {product.files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between rounded-lg border border-border bg-card p-4"
                  >
                    <div className="flex items-center gap-3">
                      <Download className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium text-foreground">{file.name}</p>
                        <p className="text-sm text-muted-foreground">{file.size}</p>
                      </div>
                    </div>
                    <Button variant="outline" size="sm" disabled>
                      Скачать после покупки
                    </Button>
                  </div>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="reviews" className="mt-6">
              <div className="space-y-6">
                {product.reviews.map((review) => (
                  <div key={review.id} className="border-b border-border pb-6 last:border-0">
                    <div className="mb-3 flex items-center gap-3">
                      <Avatar>
                        <AvatarImage src={review.avatar} />
                        <AvatarFallback>{review.author[0]}</AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium text-foreground">{review.author}</p>
                        <div className="flex items-center gap-2">
                          <div className="flex">
                            {Array.from({ length: 5 }).map((_, i) => (
                              <Star
                                key={i}
                                className={`h-4 w-4 ${
                                  i < review.rating
                                    ? "fill-chart-4 text-chart-4"
                                    : "text-muted-foreground"
                                }`}
                              />
                            ))}
                          </div>
                          <span className="text-sm text-muted-foreground">{review.date}</span>
                        </div>
                      </div>
                    </div>
                    <p className="text-foreground">{review.text}</p>
                  </div>
                ))}
              </div>
            </TabsContent>
          </Tabs>

          {/* Related Products */}
          <section className="mt-16">
            <h2 className="mb-6 text-2xl font-bold text-foreground">Похожие товары</h2>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {relatedProducts.map((item) => (
                <ProductCard key={item.id} product={item} />
              ))}
            </div>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  )
}
