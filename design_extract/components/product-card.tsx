"use client"

import Image from "next/image"
import Link from "next/link"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { Star, ShoppingCart, Eye } from "lucide-react"

export interface Product {
  id: string
  title: string
  description: string
  price: number
  originalPrice?: number
  image: string
  category: string
  rating: number
  reviewCount: number
  author: string
  featured?: boolean
}

interface ProductCardProps {
  product: Product
}

export function ProductCard({ product }: ProductCardProps) {
  const discount = product.originalPrice
    ? Math.round((1 - product.price / product.originalPrice) * 100)
    : 0

  return (
    <Card className="group overflow-hidden border-border bg-card transition-all duration-300 hover:border-primary/50 hover:shadow-lg">
      <Link href={`/product/${product.id}`}>
        <div className="relative aspect-[4/3] overflow-hidden bg-muted">
          <Image
            src={product.image}
            alt={product.title}
            fill
            className="object-cover transition-transform duration-300 group-hover:scale-105"
          />
          {discount > 0 && (
            <Badge className="absolute left-3 top-3 bg-destructive text-destructive-foreground">
              -{discount}%
            </Badge>
          )}
          {product.featured && (
            <Badge className="absolute right-3 top-3 bg-accent text-accent-foreground">
              Популярное
            </Badge>
          )}
          <div className="absolute inset-0 flex items-center justify-center gap-2 bg-foreground/60 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
            <Button size="icon" variant="secondary" className="h-10 w-10">
              <Eye className="h-5 w-5" />
            </Button>
            <Button size="icon" className="h-10 w-10">
              <ShoppingCart className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </Link>
      <CardContent className="p-4">
        <div className="mb-2 flex items-center justify-between">
          <Badge variant="secondary" className="text-xs">
            {product.category}
          </Badge>
          <div className="flex items-center gap-1">
            <Star className="h-4 w-4 fill-chart-4 text-chart-4" />
            <span className="text-sm font-medium text-foreground">{product.rating}</span>
            <span className="text-xs text-muted-foreground">({product.reviewCount})</span>
          </div>
        </div>
        <Link href={`/product/${product.id}`}>
          <h3 className="mb-1 line-clamp-2 text-base font-semibold text-foreground transition-colors hover:text-primary">
            {product.title}
          </h3>
        </Link>
        <p className="mb-2 text-xs text-muted-foreground">от {product.author}</p>
        <p className="line-clamp-2 text-sm text-muted-foreground">{product.description}</p>
      </CardContent>
      <CardFooter className="flex items-center justify-between border-t border-border p-4">
        <div className="flex items-baseline gap-2">
          <span className="text-xl font-bold text-foreground">
            {product.price.toLocaleString("ru-RU")} ₽
          </span>
          {product.originalPrice && (
            <span className="text-sm text-muted-foreground line-through">
              {product.originalPrice.toLocaleString("ru-RU")} ₽
            </span>
          )}
        </div>
        <Button size="sm" className="gap-2">
          <ShoppingCart className="h-4 w-4" />
          <span className="hidden sm:inline">В корзину</span>
        </Button>
      </CardFooter>
    </Card>
  )
}
