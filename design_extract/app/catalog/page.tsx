"use client"

import { useState } from "react"
import { Header } from "@/components/layout/header"
import { Footer } from "@/components/layout/footer"
import { ProductCard, type Product } from "@/components/product-card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Slider } from "@/components/ui/slider"
import { 
  Sheet, 
  SheetContent, 
  SheetHeader, 
  SheetTitle, 
  SheetTrigger 
} from "@/components/ui/sheet"
import { Search, SlidersHorizontal, X, Grid3X3, List } from "lucide-react"

// Placeholder данные - будут заменены на данные из Django API
const allProducts: Product[] = [
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
  {
    id: "5",
    title: "Figma Plugin Pack",
    description: "Набор из 20+ полезных плагинов для Figma",
    price: 1990,
    image: "https://images.unsplash.com/photo-1609921212029-bb5a28e60960?w=800&h=600&fit=crop",
    category: "Софт",
    rating: 4.6,
    reviewCount: 78,
    author: "PluginLab",
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
  {
    id: "7",
    title: "JavaScript: Продвинутый курс",
    description: "Паттерны проектирования и архитектура приложений",
    price: 4490,
    image: "https://images.unsplash.com/photo-1627398242454-45a1465c2479?w=800&h=600&fit=crop",
    category: "Курсы",
    rating: 4.9,
    reviewCount: 312,
    author: "JSMaster",
  },
  {
    id: "8",
    title: "Icon Pack Pro",
    description: "5000+ векторных иконок в различных стилях",
    price: 990,
    image: "https://images.unsplash.com/photo-1558655146-9f40138edfeb?w=800&h=600&fit=crop",
    category: "Графика",
    rating: 4.7,
    reviewCount: 445,
    author: "IconStudio",
  },
]

const categories = [
  { id: "all", name: "Все категории" },
  { id: "templates", name: "Шаблоны" },
  { id: "software", name: "Софт" },
  { id: "courses", name: "Курсы" },
  { id: "ebooks", name: "Книги" },
  { id: "graphics", name: "Графика" },
]

function FilterSidebar({ 
  priceRange, 
  setPriceRange,
  selectedCategories,
  setSelectedCategories,
}: {
  priceRange: number[]
  setPriceRange: (value: number[]) => void
  selectedCategories: string[]
  setSelectedCategories: (value: string[]) => void
}) {
  const toggleCategory = (categoryId: string) => {
    if (selectedCategories.includes(categoryId)) {
      setSelectedCategories(selectedCategories.filter(c => c !== categoryId))
    } else {
      setSelectedCategories([...selectedCategories, categoryId])
    }
  }

  return (
    <div className="space-y-6">
      {/* Categories */}
      <div>
        <h3 className="mb-4 text-sm font-semibold text-foreground">Категории</h3>
        <div className="space-y-3">
          {categories.slice(1).map((category) => (
            <label key={category.id} className="flex cursor-pointer items-center gap-3">
              <Checkbox
                checked={selectedCategories.includes(category.id)}
                onCheckedChange={() => toggleCategory(category.id)}
              />
              <span className="text-sm text-foreground">{category.name}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Price Range */}
      <div>
        <h3 className="mb-4 text-sm font-semibold text-foreground">Цена</h3>
        <Slider
          value={priceRange}
          onValueChange={setPriceRange}
          max={10000}
          min={0}
          step={100}
          className="mb-4"
        />
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>{priceRange[0].toLocaleString("ru-RU")} ₽</span>
          <span>{priceRange[1].toLocaleString("ru-RU")} ₽</span>
        </div>
      </div>

      {/* Rating */}
      <div>
        <h3 className="mb-4 text-sm font-semibold text-foreground">Рейтинг</h3>
        <div className="space-y-3">
          {[4.5, 4.0, 3.5].map((rating) => (
            <label key={rating} className="flex cursor-pointer items-center gap-3">
              <Checkbox />
              <span className="text-sm text-foreground">От {rating} и выше</span>
            </label>
          ))}
        </div>
      </div>

      <Button variant="outline" className="w-full">
        Сбросить фильтры
      </Button>
    </div>
  )
}

export default function CatalogPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [sortBy, setSortBy] = useState("popular")
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")
  const [priceRange, setPriceRange] = useState([0, 10000])
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])

  // Placeholder фильтрация - будет заменена на API вызовы к Django
  const filteredProducts = allProducts.filter((product) => {
    const matchesSearch = product.title.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesPrice = product.price >= priceRange[0] && product.price <= priceRange[1]
    return matchesSearch && matchesPrice
  })

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 bg-background">
        <div className="container mx-auto px-4 py-8">
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="mb-2 text-3xl font-bold text-foreground">Каталог</h1>
            <p className="text-muted-foreground">
              Найдите идеальный цифровой продукт для вашего проекта
            </p>
          </div>

          {/* Search and Filters Bar */}
          <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex flex-1 items-center gap-4">
              <div className="relative flex-1 lg:max-w-md">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  type="search"
                  placeholder="Поиск товаров..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* Mobile Filter Button */}
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="outline" className="gap-2 lg:hidden">
                    <SlidersHorizontal className="h-4 w-4" />
                    Фильтры
                  </Button>
                </SheetTrigger>
                <SheetContent side="left">
                  <SheetHeader>
                    <SheetTitle>Фильтры</SheetTitle>
                  </SheetHeader>
                  <div className="mt-6">
                    <FilterSidebar
                      priceRange={priceRange}
                      setPriceRange={setPriceRange}
                      selectedCategories={selectedCategories}
                      setSelectedCategories={setSelectedCategories}
                    />
                  </div>
                </SheetContent>
              </Sheet>
            </div>

            <div className="flex items-center gap-4">
              {/* Active Filters */}
              {selectedCategories.length > 0 && (
                <div className="hidden items-center gap-2 lg:flex">
                  {selectedCategories.map((catId) => {
                    const category = categories.find((c) => c.id === catId)
                    return (
                      <Badge key={catId} variant="secondary" className="gap-1">
                        {category?.name}
                        <button
                          onClick={() =>
                            setSelectedCategories(selectedCategories.filter((c) => c !== catId))
                          }
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    )
                  })}
                </div>
              )}

              {/* Sort */}
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Сортировка" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="popular">Популярные</SelectItem>
                  <SelectItem value="newest">Новинки</SelectItem>
                  <SelectItem value="price-asc">Цена: по возрастанию</SelectItem>
                  <SelectItem value="price-desc">Цена: по убыванию</SelectItem>
                  <SelectItem value="rating">По рейтингу</SelectItem>
                </SelectContent>
              </Select>

              {/* View Mode */}
              <div className="hidden items-center rounded-lg border border-border p-1 lg:flex">
                <Button
                  variant={viewMode === "grid" ? "secondary" : "ghost"}
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setViewMode("grid")}
                >
                  <Grid3X3 className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === "list" ? "secondary" : "ghost"}
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setViewMode("list")}
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          <div className="flex gap-8">
            {/* Desktop Sidebar */}
            <aside className="hidden w-64 shrink-0 lg:block">
              <div className="sticky top-24 rounded-lg border border-border bg-card p-6">
                <FilterSidebar
                  priceRange={priceRange}
                  setPriceRange={setPriceRange}
                  selectedCategories={selectedCategories}
                  setSelectedCategories={setSelectedCategories}
                />
              </div>
            </aside>

            {/* Products Grid */}
            <div className="flex-1">
              <div className="mb-4 text-sm text-muted-foreground">
                Найдено {filteredProducts.length} товаров
              </div>

              <div
                className={
                  viewMode === "grid"
                    ? "grid gap-6 sm:grid-cols-2 xl:grid-cols-3"
                    : "space-y-4"
                }
              >
                {filteredProducts.map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>

              {filteredProducts.length === 0 && (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <div className="mb-4 text-6xl">🔍</div>
                  <h3 className="mb-2 text-xl font-semibold text-foreground">
                    Ничего не найдено
                  </h3>
                  <p className="text-muted-foreground">
                    Попробуйте изменить параметры поиска или фильтры
                  </p>
                </div>
              )}

              {/* Pagination */}
              {filteredProducts.length > 0 && (
                <div className="mt-8 flex items-center justify-center gap-2">
                  <Button variant="outline" disabled>
                    Назад
                  </Button>
                  <Button variant="secondary">1</Button>
                  <Button variant="ghost">2</Button>
                  <Button variant="ghost">3</Button>
                  <span className="px-2 text-muted-foreground">...</span>
                  <Button variant="ghost">10</Button>
                  <Button variant="outline">Вперёд</Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  )
}
