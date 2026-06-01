"use client"

import { useState } from "react"
import Link from "next/link"
import { Header } from "@/components/layout/header"
import { Footer } from "@/components/layout/footer"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Checkbox } from "@/components/ui/checkbox"
import { Separator } from "@/components/ui/separator"
import { 
  CreditCard, 
  Smartphone, 
  Building2, 
  ShieldCheck, 
  Lock,
  ChevronLeft,
  CheckCircle,
} from "lucide-react"

export default function CheckoutPage() {
  const [paymentMethod, setPaymentMethod] = useState("card")
  const [isProcessing, setIsProcessing] = useState(false)
  const [isComplete, setIsComplete] = useState(false)

  // Placeholder данные - будут заменены на данные из Django API
  const orderSummary = {
    items: [
      { title: "SaaS Dashboard UI Kit", price: 4990 },
      { title: "Курс по Python для начинающих", price: 2990 },
      { title: "E-commerce Starter Kit", price: 6990 },
    ],
    subtotal: 14970,
    discount: 1497,
    total: 13473,
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setIsProcessing(true)
    // Simulate payment processing
    setTimeout(() => {
      setIsProcessing(false)
      setIsComplete(true)
    }, 2000)
  }

  if (isComplete) {
    return (
      <div className="flex min-h-screen flex-col">
        <Header />
        <main className="flex flex-1 flex-col items-center justify-center bg-background px-4 py-16">
          <div className="text-center">
            <div className="mb-6 flex justify-center">
              <div className="flex h-24 w-24 items-center justify-center rounded-full bg-accent/20">
                <CheckCircle className="h-12 w-12 text-accent" />
              </div>
            </div>
            <h1 className="mb-4 text-3xl font-bold text-foreground">Заказ оформлен!</h1>
            <p className="mb-2 text-muted-foreground">
              Спасибо за покупку! Ваш заказ #DG-2024-001 успешно оплачен.
            </p>
            <p className="mb-8 text-muted-foreground">
              Ссылки для скачивания отправлены на вашу почту.
            </p>
            <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
              <Link href="/dashboard/downloads">
                <Button size="lg">Перейти к загрузкам</Button>
              </Link>
              <Link href="/catalog">
                <Button size="lg" variant="outline">
                  Продолжить покупки
                </Button>
              </Link>
            </div>
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
          {/* Back Link */}
          <Link
            href="/cart"
            className="mb-6 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <ChevronLeft className="h-4 w-4" />
            Вернуться в корзину
          </Link>

          <h1 className="mb-8 text-3xl font-bold text-foreground">Оформление заказа</h1>

          <form onSubmit={handleSubmit}>
            <div className="grid gap-8 lg:grid-cols-3">
              {/* Checkout Form */}
              <div className="space-y-6 lg:col-span-2">
                {/* Contact Info */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Контактные данные</CardTitle>
                  </CardHeader>
                  <CardContent className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <Input
                        id="email"
                        type="email"
                        placeholder="your@email.com"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="phone">Телефон</Label>
                      <Input
                        id="phone"
                        type="tel"
                        placeholder="+7 (999) 123-45-67"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="firstName">Имя</Label>
                      <Input id="firstName" placeholder="Иван" required />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="lastName">Фамилия</Label>
                      <Input id="lastName" placeholder="Иванов" required />
                    </div>
                  </CardContent>
                </Card>

                {/* Payment Method */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Способ оплаты</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <RadioGroup
                      value={paymentMethod}
                      onValueChange={setPaymentMethod}
                      className="space-y-3"
                    >
                      <label className="flex cursor-pointer items-center gap-4 rounded-lg border border-border p-4 transition-colors hover:bg-muted/50 has-[:checked]:border-primary has-[:checked]:bg-primary/5">
                        <RadioGroupItem value="card" id="card" />
                        <CreditCard className="h-5 w-5 text-muted-foreground" />
                        <div className="flex-1">
                          <p className="font-medium text-foreground">Банковская карта</p>
                          <p className="text-sm text-muted-foreground">
                            Visa, Mastercard, МИР
                          </p>
                        </div>
                      </label>
                      <label className="flex cursor-pointer items-center gap-4 rounded-lg border border-border p-4 transition-colors hover:bg-muted/50 has-[:checked]:border-primary has-[:checked]:bg-primary/5">
                        <RadioGroupItem value="sbp" id="sbp" />
                        <Smartphone className="h-5 w-5 text-muted-foreground" />
                        <div className="flex-1">
                          <p className="font-medium text-foreground">СБП</p>
                          <p className="text-sm text-muted-foreground">
                            Система быстрых платежей
                          </p>
                        </div>
                      </label>
                      <label className="flex cursor-pointer items-center gap-4 rounded-lg border border-border p-4 transition-colors hover:bg-muted/50 has-[:checked]:border-primary has-[:checked]:bg-primary/5">
                        <RadioGroupItem value="invoice" id="invoice" />
                        <Building2 className="h-5 w-5 text-muted-foreground" />
                        <div className="flex-1">
                          <p className="font-medium text-foreground">Счёт для юр. лиц</p>
                          <p className="text-sm text-muted-foreground">
                            Оплата по реквизитам
                          </p>
                        </div>
                      </label>
                    </RadioGroup>

                    {/* Card Details */}
                    {paymentMethod === "card" && (
                      <div className="mt-6 space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="cardNumber">Номер карты</Label>
                          <Input
                            id="cardNumber"
                            placeholder="1234 5678 9012 3456"
                            required
                          />
                        </div>
                        <div className="grid gap-4 sm:grid-cols-2">
                          <div className="space-y-2">
                            <Label htmlFor="expiry">Срок действия</Label>
                            <Input id="expiry" placeholder="MM/YY" required />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="cvv">CVV</Label>
                            <Input id="cvv" placeholder="123" required />
                          </div>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Terms */}
                <div className="flex items-start gap-3">
                  <Checkbox id="terms" required />
                  <label
                    htmlFor="terms"
                    className="text-sm leading-relaxed text-muted-foreground"
                  >
                    Я согласен с{" "}
                    <Link href="/terms" className="text-primary hover:underline">
                      условиями использования
                    </Link>{" "}
                    и{" "}
                    <Link href="/privacy" className="text-primary hover:underline">
                      политикой конфиденциальности
                    </Link>
                  </label>
                </div>
              </div>

              {/* Order Summary */}
              <div>
                <Card className="sticky top-24">
                  <CardHeader>
                    <CardTitle className="text-lg">Ваш заказ</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {orderSummary.items.map((item, index) => (
                      <div key={index} className="flex justify-between text-sm">
                        <span className="text-muted-foreground">{item.title}</span>
                        <span className="text-foreground">
                          {item.price.toLocaleString("ru-RU")} ₽
                        </span>
                      </div>
                    ))}

                    <Separator />

                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Подытог</span>
                        <span className="text-foreground">
                          {orderSummary.subtotal.toLocaleString("ru-RU")} ₽
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Скидка</span>
                        <span className="text-accent">
                          -{orderSummary.discount.toLocaleString("ru-RU")} ₽
                        </span>
                      </div>
                    </div>

                    <Separator />

                    <div className="flex justify-between">
                      <span className="text-lg font-semibold text-foreground">Итого</span>
                      <span className="text-2xl font-bold text-foreground">
                        {orderSummary.total.toLocaleString("ru-RU")} ₽
                      </span>
                    </div>
                  </CardContent>
                  <CardFooter className="flex flex-col gap-4">
                    <Button
                      type="submit"
                      size="lg"
                      className="w-full gap-2"
                      disabled={isProcessing}
                    >
                      {isProcessing ? (
                        <>Обработка...</>
                      ) : (
                        <>
                          <Lock className="h-5 w-5" />
                          Оплатить {orderSummary.total.toLocaleString("ru-RU")} ₽
                        </>
                      )}
                    </Button>
                    <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                      <ShieldCheck className="h-4 w-4 text-accent" />
                      Защищённое соединение
                    </div>
                  </CardFooter>
                </Card>
              </div>
            </div>
          </form>
        </div>
      </main>
      <Footer />
    </div>
  )
}
