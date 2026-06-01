"use client"

import Link from "next/link"
import { Header } from "@/components/layout/header"
import { Footer } from "@/components/layout/footer"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import {
  Download,
  ShoppingBag,
  Heart,
  Settings,
  CreditCard,
  Clock,
  Package,
  Star,
  ChevronRight,
} from "lucide-react"

// Placeholder данные - будут заменены на данные из Django API
const user = {
  name: "Иван Иванов",
  email: "ivan@example.com",
  avatar: "",
  memberSince: "Март 2024",
}

const stats = [
  { label: "Покупки", value: "12", icon: ShoppingBag, color: "text-chart-1" },
  { label: "Загрузки", value: "28", icon: Download, color: "text-chart-2" },
  { label: "Избранное", value: "7", icon: Heart, color: "text-chart-3" },
  { label: "Отзывы", value: "5", icon: Star, color: "text-chart-4" },
]

const recentOrders = [
  {
    id: "DG-2024-001",
    date: "15 марта 2024",
    items: ["SaaS Dashboard UI Kit", "Mobile App UI Kit"],
    total: 8980,
    status: "completed",
  },
  {
    id: "DG-2024-002",
    date: "10 марта 2024",
    items: ["Курс по Python для начинающих"],
    total: 2990,
    status: "completed",
  },
  {
    id: "DG-2024-003",
    date: "5 марта 2024",
    items: ["E-commerce Starter Kit"],
    total: 6990,
    status: "completed",
  },
]

const menuItems = [
  { label: "Мои загрузки", href: "/dashboard/downloads", icon: Download },
  { label: "История заказов", href: "/dashboard/orders", icon: ShoppingBag },
  { label: "Избранное", href: "/dashboard/wishlist", icon: Heart },
  { label: "Способы оплаты", href: "/dashboard/payments", icon: CreditCard },
  { label: "Настройки", href: "/dashboard/settings", icon: Settings },
]

export default function DashboardPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 bg-muted/30">
        <div className="container mx-auto px-4 py-8">
          {/* Profile Header */}
          <Card className="mb-8">
            <CardContent className="flex flex-col items-center gap-6 p-6 sm:flex-row">
              <Avatar className="h-20 w-20">
                <AvatarImage src={user.avatar} />
                <AvatarFallback className="text-2xl">
                  {user.name.split(" ").map((n) => n[0]).join("")}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 text-center sm:text-left">
                <h1 className="text-2xl font-bold text-foreground">{user.name}</h1>
                <p className="text-muted-foreground">{user.email}</p>
                <div className="mt-2 flex items-center justify-center gap-2 text-sm text-muted-foreground sm:justify-start">
                  <Clock className="h-4 w-4" />
                  <span>Участник с {user.memberSince}</span>
                </div>
              </div>
              <Link href="/dashboard/settings">
                <Button variant="outline" className="gap-2">
                  <Settings className="h-4 w-4" />
                  Редактировать профиль
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Stats */}
          <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {stats.map((stat) => {
              const Icon = stat.icon
              return (
                <Card key={stat.label}>
                  <CardContent className="flex items-center gap-4 p-6">
                    <div className={`flex h-12 w-12 items-center justify-center rounded-lg bg-muted`}>
                      <Icon className={`h-6 w-6 ${stat.color}`} />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-foreground">{stat.value}</p>
                      <p className="text-sm text-muted-foreground">{stat.label}</p>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>

          <div className="grid gap-8 lg:grid-cols-3">
            {/* Recent Orders */}
            <div className="lg:col-span-2">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle>Последние заказы</CardTitle>
                  <Link href="/dashboard/orders">
                    <Button variant="ghost" size="sm" className="gap-1">
                      Все заказы
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </Link>
                </CardHeader>
                <CardContent className="space-y-4">
                  {recentOrders.map((order) => (
                    <div
                      key={order.id}
                      className="flex items-center gap-4 rounded-lg border border-border p-4"
                    >
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                        <Package className="h-5 w-5 text-muted-foreground" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-foreground">
                            {order.id}
                          </span>
                          <Badge
                            variant="secondary"
                            className="bg-accent/20 text-accent"
                          >
                            Выполнен
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {order.items.join(", ")}
                        </p>
                        <p className="text-xs text-muted-foreground">{order.date}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-foreground">
                          {order.total.toLocaleString("ru-RU")} ₽
                        </p>
                        <Link href={`/dashboard/orders/${order.id}`}>
                          <Button variant="ghost" size="sm">
                            Подробнее
                          </Button>
                        </Link>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            {/* Quick Links */}
            <div>
              <Card>
                <CardHeader>
                  <CardTitle>Быстрые ссылки</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {menuItems.map((item) => {
                    const Icon = item.icon
                    return (
                      <Link key={item.href} href={item.href}>
                        <div className="flex items-center gap-3 rounded-lg p-3 transition-colors hover:bg-muted">
                          <Icon className="h-5 w-5 text-muted-foreground" />
                          <span className="flex-1 font-medium text-foreground">
                            {item.label}
                          </span>
                          <ChevronRight className="h-4 w-4 text-muted-foreground" />
                        </div>
                      </Link>
                    )
                  })}
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  )
}
