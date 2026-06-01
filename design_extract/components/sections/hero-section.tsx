import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search, ArrowRight, Sparkles, Shield, Zap } from "lucide-react"

export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-background">
      {/* Background Pattern */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute left-1/4 top-1/4 h-96 w-96 rounded-full bg-primary/5 blur-3xl" />
        <div className="absolute right-1/4 bottom-1/4 h-96 w-96 rounded-full bg-accent/5 blur-3xl" />
      </div>

      <div className="container mx-auto px-4 py-20 lg:py-32">
        <div className="mx-auto max-w-4xl text-center">
          {/* Badge */}
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-sm text-muted-foreground">
            <Sparkles className="h-4 w-4 text-primary" />
            <span>Более 10 000 цифровых товаров</span>
          </div>

          {/* Heading */}
          <h1 className="mb-6 text-balance text-4xl font-bold tracking-tight text-foreground md:text-5xl lg:text-6xl">
            Маркетплейс{" "}
            <span className="text-primary">цифровых товаров</span>{" "}
            для вашего бизнеса
          </h1>

          {/* Description */}
          <p className="mx-auto mb-8 max-w-2xl text-pretty text-lg text-muted-foreground md:text-xl">
            Шаблоны, софт, курсы и электронные книги от проверенных авторов. 
            Мгновенная доставка и пожизненный доступ к покупкам.
          </p>

          {/* Search */}
          <div className="mx-auto mb-8 flex max-w-xl flex-col gap-3 sm:flex-row">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Что вы ищете?"
                className="h-12 pl-10 text-base"
              />
            </div>
            <Button size="lg" className="h-12 gap-2">
              Найти
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>

          {/* Features */}
          <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-accent" />
              <span>Мгновенная доставка</span>
            </div>
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-accent" />
              <span>Безопасная оплата</span>
            </div>
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-accent" />
              <span>Пожизненный доступ</span>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="mx-auto mt-16 grid max-w-3xl grid-cols-2 gap-8 md:grid-cols-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-foreground">10K+</div>
            <div className="text-sm text-muted-foreground">Товаров</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-foreground">50K+</div>
            <div className="text-sm text-muted-foreground">Клиентов</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-foreground">1K+</div>
            <div className="text-sm text-muted-foreground">Авторов</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-foreground">4.9</div>
            <div className="text-sm text-muted-foreground">Рейтинг</div>
          </div>
        </div>
      </div>
    </section>
  )
}
