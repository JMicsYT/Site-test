import Link from "next/link"
import { Card, CardContent } from "@/components/ui/card"
import { FileCode, Monitor, GraduationCap, BookOpen, Palette, Music } from "lucide-react"

const categories = [
  {
    id: "templates",
    name: "Шаблоны",
    description: "Веб-шаблоны и UI-киты",
    icon: FileCode,
    count: 2500,
    color: "text-chart-1",
    bgColor: "bg-chart-1/10",
  },
  {
    id: "software",
    name: "Софт",
    description: "Приложения и плагины",
    icon: Monitor,
    count: 1800,
    color: "text-chart-2",
    bgColor: "bg-chart-2/10",
  },
  {
    id: "courses",
    name: "Курсы",
    description: "Онлайн-обучение",
    icon: GraduationCap,
    count: 3200,
    color: "text-chart-3",
    bgColor: "bg-chart-3/10",
  },
  {
    id: "ebooks",
    name: "Книги",
    description: "Электронные издания",
    icon: BookOpen,
    count: 1500,
    color: "text-chart-4",
    bgColor: "bg-chart-4/10",
  },
  {
    id: "graphics",
    name: "Графика",
    description: "Иконки, иллюстрации",
    icon: Palette,
    count: 4200,
    color: "text-chart-5",
    bgColor: "bg-chart-5/10",
  },
  {
    id: "audio",
    name: "Аудио",
    description: "Музыка и звуки",
    icon: Music,
    count: 890,
    color: "text-primary",
    bgColor: "bg-primary/10",
  },
]

export function CategoriesSection() {
  return (
    <section className="bg-muted/30 py-16">
      <div className="container mx-auto px-4">
        <div className="mb-10 text-center">
          <h2 className="mb-3 text-3xl font-bold text-foreground">Категории</h2>
          <p className="mx-auto max-w-2xl text-muted-foreground">
            Выберите категорию и найдите то, что вам нужно
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {categories.map((category) => {
            const Icon = category.icon
            return (
              <Link key={category.id} href={`/catalog?category=${category.id}`}>
                <Card className="group h-full border-border bg-card transition-all duration-300 hover:border-primary/50 hover:shadow-md">
                  <CardContent className="flex items-center gap-4 p-6">
                    <div className={`flex h-14 w-14 items-center justify-center rounded-xl ${category.bgColor}`}>
                      <Icon className={`h-7 w-7 ${category.color}`} />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-foreground group-hover:text-primary">
                        {category.name}
                      </h3>
                      <p className="text-sm text-muted-foreground">{category.description}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-lg font-bold text-foreground">{category.count.toLocaleString()}</span>
                      <p className="text-xs text-muted-foreground">товаров</p>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            )
          })}
        </div>
      </div>
    </section>
  )
}
