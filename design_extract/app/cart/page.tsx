"use client"

import { useState } from "react"
import Image from "next/image"
import Link from "next/link"
import { Header } from "@/components/layout/header"
import { Footer } from "@/components/layout/footer"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Trash2, Minus, Plus, Tag, ShieldCheck, CreditCard } from "lucide-react"

interface CartItem {
  id: string
  title: string
  price: number
  originalPrice?: number
  image: string
  author: string
  quantity: number
}

// Placeholder данные - будут заменены на данные из Django API
const initialCartItems: CartItem[] = [
  {
    id: "1",
    title: "SaaS Dashboard UI Kit",
    price: 4990,
    originalPrice: 7990,
    image: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=300&fit=crop",
    author: "DesignPro",
    quantity: 1,
  },
  {
    id: "2",
    title: "Курс по Python для начинающих",
    price: 2990,
    image: "https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=400&h=300&fit=crop",
    author: "CodeMaster",
    quantity: 1,
  },
  {
    id: "3",
    title: "E-commerce Starter Kit",
    price: 6990,
    originalPrice: 9990,
    image: "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=400&h=300&fit=crop",
    author: "WebStudio",
    quantity: 1,
  },
]

export default function CartPage() {
  const [cartItems, setCartItems] = useState(initialCartItems)
  const [promoCode, setPromoCode] = useState("")
  const [promoApplied, setPromoApplied] = useState(false)

  const removeItem = (id: string) => {
    setCartItems(cartItems.filter((item) => item.id !== id))
  }

  const subtotal = cartItems.reduce((sum, item) => sum + item.price * item.quantity, 0)
  const discount = promoApplied ? Math.round(subtotal * 0.1) : 0
  const total = subtotal - discount

  const applyPromoCode = () => {
    if (promoCode.toLowerCase() === "discount10") {
      setPromoApplied(true)
    }
  }

  if (cartItems.length === 0) {
    return (
      <div className="flex min-h-screen flex-col">
        <Header />
        <main className="flex flex-1 flex-col items-center justify-center bg-background px-4 py-16">
          <div className="text-center">
            <div className="mb-6 text-8xl opacity-30">🛒</div>
            <h1 className="mb-4 text-2xl font-bold text-foreground">Корзина пуста</h1>
            <p className="mb-8 text-muted-foreground">
              Добавьте товары из каталога, чтобы продолжить покупки
            </p>
            <Link href="/catalog">
              <Button size="lg">Перейти в каталог</Button>
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 bg-background">
        <div className="container mx-auto px-4 py-8">
          <h1 className="mb-8 text-3xl font-bold text-foreground">Корзина</h1>

          <div className="grid gap-8 lg:grid-cols-3">
            {/* Cart Items */}
            <div className="lg:col-span-2">
              <div className="space-y-4">
                {cartItems.map((item) => (
                  <Card key={item.id} className="overflow-hidden">
                    <CardContent className="flex gap-4 p-4">
                      <div className="relative h-24 w-32 shrink-0 overflow-hidden rounded-lg">
                        <Image
                          src={item.image}
                          alt={item.title}
                          fill
                          className="object-cover"
                        />
                      </div>
                      <div className="flex flex-1 flex-col justify-between">
                        <div>
                          <Link
                            href={`/product/${item.id}`}
                            className="font-semibold text-foreground hover:text-primary"
                          >
                            {item.title}
                          </Link>
                          <p className="text-sm text-muted-foreground">от {item.author}</p>
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-lg font-bold text-foreground">
                              {item.price.toLocaleString("ru-RU")} ₽
                            </span>
                            {item.originalPrice && (
                              <span className="text-sm text-muted-foreground line-through">
                                {item.originalPrice.toLocaleString("ru-RU")} ₽
                              </span>
                            )}
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-muted-foreground hover:text-destructive"
                            onClick={() => removeItem(item.id)}
                          >
                            <Trash2 className="h-5 w-5" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Continue Shopping */}
              <div className="mt-6">
                <Link href="/catalog">
                  <Button variant="outline">Продолжить покупки</Button>
                </Link>
              </div>
            </div>

            {/* Order Summary */}
            <div>
              <Card className="sticky top-24">
                <CardHeader>
                  <CardTitle>Итого</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Promo Code */}
                  <div className="flex gap-2">
                    <Input
                      placeholder="Промокод"
                      value={promoCode}
                      onChange={(e) => setPromoCode(e.target.value)}
                      disabled={promoApplied}
                    />
                    <Button
                      variant="outline"
                      onClick={applyPromoCode}
                      disabled={promoApplied}
                    >
                      <Tag className="h-4 w-4" />
                    </Button>
                  </div>
                  {promoApplied && (
                    <p className="text-sm text-accent">Промокод применён: -10%</p>
                  )}

                  <Separator />

                  {/* Summary */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Товары ({cartItems.length})</span>
                      <span className="text-foreground">
                        {subtotal.toLocaleString("ru-RU")} ₽
                      </span>
                    </div>
                    {discount > 0 && (
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Скидка</span>
                        <span className="text-accent">
                          -{discount.toLocaleString("ru-RU")} ₽
                        </span>
                      </div>
                    )}
                  </div>

                  <Separator />

                  <div className="flex justify-between">
                    <span className="text-lg font-semibold text-foreground">Итого</span>
                    <span className="text-2xl font-bold text-foreground">
                      {total.toLocaleString("ru-RU")} ₽
                    </span>
                  </div>
                </CardContent>
                <CardFooter className="flex flex-col gap-4">
                  <Link href="/checkout" className="w-full">
                    <Button size="lg" className="w-full gap-2">
                      <CreditCard className="h-5 w-5" />
                      Оформить заказ
                    </Button>
                  </Link>
                  <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                    <ShieldCheck className="h-4 w-4 text-accent" />
                    Безопасная оплата
                  </div>
                </CardFooter>
              </Card>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  )
}
