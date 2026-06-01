"use client"

import Image from "next/image"
import Link from "next/link"
import { Header } from "@/components/layout/header"
import { Footer } from "@/components/layout/footer"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Download, Search, Clock, FileArchive, RefreshCw } from "lucide-react"

// Placeholder данные - будут заменены на данные из Django API
const downloads = [
  {
    id: "1",
    title: "SaaS Dashboard UI Kit",
    image: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=300&fit=crop",
    purchaseDate: "15 марта 2024",
    version: "2.1.0",
    lastUpdate: "10 марта 2024",
    files: [
      { name: "dashboard-ui-kit.zip", size: "45.2 MB" },
      { name: "documentation.pdf", size: "2.1 MB" },
    ],
    hasUpdate: true,
  },
  {
    id: "2",
    title: "Курс по Python для начинающих",
    image: "https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=400&h=300&fit=crop",
    purchaseDate: "10 марта 2024",
    version: "1.5.0",
    lastUpdate: "5 марта 2024",
    files: [
      { name: "python-course.zip", size: "1.2 GB" },
      { name: "materials.pdf", size: "15.3 MB" },
    ],
    hasUpdate: false,
  },
  {
    id: "3",
    title: "E-commerce Starter Kit",
    image: "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=400&h=300&fit=crop",
    purchaseDate: "5 марта 2024",
    version: "3.0.1",
    lastUpdate: "1 марта 2024",
    files: [
      { name: "ecommerce-kit.zip", size: "78.5 MB" },
      { name: "setup-guide.pdf", size: "3.2 MB" },
    ],
    hasUpdate: true,
  },
  {
    id: "4",
    title: "Mobile App UI Kit",
    image: "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=400&h=300&fit=crop",
    purchaseDate: "1 марта 2024",
    version: "1.8.0",
    lastUpdate: "28 февраля 2024",
    files: [
      { name: "mobile-ui-kit.zip", size: "52.1 MB" },
    ],
    hasUpdate: false,
  },
]

export default function DownloadsPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 bg-muted/30">
        <div className="container mx-auto px-4 py-8">
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="mb-2 text-3xl font-bold text-foreground">Мои загрузки</h1>
            <p className="text-muted-foreground">
              Все ваши приобретённые товары доступны для скачивания
            </p>
          </div>

          {/* Filters */}
          <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="relative flex-1 sm:max-w-xs">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Поиск по загрузкам..."
                className="pl-10"
              />
            </div>
            <div className="flex gap-3">
              <Select defaultValue="all">
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Категория" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Все категории</SelectItem>
                  <SelectItem value="templates">Шаблоны</SelectItem>
                  <SelectItem value="courses">Курсы</SelectItem>
                  <SelectItem value="software">Софт</SelectItem>
                </SelectContent>
              </Select>
              <Select defaultValue="newest">
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Сортировка" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="newest">Сначала новые</SelectItem>
                  <SelectItem value="oldest">Сначала старые</SelectItem>
                  <SelectItem value="name">По названию</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Downloads List */}
          <div className="space-y-4">
            {downloads.map((item) => (
              <Card key={item.id}>
                <CardContent className="flex flex-col gap-4 p-4 sm:flex-row">
                  {/* Image */}
                  <div className="relative h-32 w-full shrink-0 overflow-hidden rounded-lg sm:w-48">
                    <Image
                      src={item.image}
                      alt={item.title}
                      fill
                      className="object-cover"
                    />
                  </div>

                  {/* Info */}
                  <div className="flex flex-1 flex-col justify-between">
                    <div>
                      <div className="mb-2 flex items-center gap-2">
                        <Link
                          href={`/product/${item.id}`}
                          className="text-lg font-semibold text-foreground hover:text-primary"
                        >
                          {item.title}
                        </Link>
                        {item.hasUpdate && (
                          <Badge className="bg-accent text-accent-foreground">
                            Обновление
                          </Badge>
                        )}
                      </div>
                      <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          Куплено: {item.purchaseDate}
                        </div>
                        <div className="flex items-center gap-1">
                          <RefreshCw className="h-4 w-4" />
                          Версия: {item.version}
                        </div>
                      </div>
                    </div>

                    {/* Files */}
                    <div className="mt-4 flex flex-wrap gap-2">
                      {item.files.map((file, index) => (
                        <Button
                          key={index}
                          variant="outline"
                          size="sm"
                          className="gap-2"
                        >
                          <FileArchive className="h-4 w-4" />
                          {file.name}
                          <span className="text-muted-foreground">({file.size})</span>
                        </Button>
                      ))}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex shrink-0 flex-col gap-2 sm:items-end">
                    <Button className="gap-2">
                      <Download className="h-4 w-4" />
                      Скачать всё
                    </Button>
                    {item.hasUpdate && (
                      <Button variant="outline" size="sm" className="gap-2">
                        <RefreshCw className="h-4 w-4" />
                        Обновить
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </main>
      <Footer />
    </div>
  )
}
