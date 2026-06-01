"use client"

import Link from "next/link"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ThemeToggle } from "@/components/theme-toggle"
import { Search, ShoppingCart, User, Menu, X, Package, Download, Settings, LogOut } from "lucide-react"

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)

  const cartItemCount = 3 // Placeholder - будет подключено к Django

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <Package className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="text-xl font-bold text-foreground">DigiStore</span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden items-center gap-6 md:flex">
          <Link href="/catalog" className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
            Каталог
          </Link>
          <Link href="/catalog?category=templates" className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
            Шаблоны
          </Link>
          <Link href="/catalog?category=software" className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
            Софт
          </Link>
          <Link href="/catalog?category=courses" className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
            Курсы
          </Link>
          <Link href="/catalog?category=ebooks" className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
            Книги
          </Link>
        </nav>

        {/* Search, Cart, User */}
        <div className="flex items-center gap-2">
          {/* Search */}
          <div className="hidden items-center md:flex">
            {searchOpen ? (
              <div className="flex items-center gap-2">
                <Input
                  type="search"
                  placeholder="Поиск товаров..."
                  className="w-64"
                  autoFocus
                  onBlur={() => setSearchOpen(false)}
                />
              </div>
            ) : (
              <Button variant="ghost" size="icon" onClick={() => setSearchOpen(true)}>
                <Search className="h-5 w-5" />
                <span className="sr-only">Поиск</span>
              </Button>
            )}
          </div>

          <ThemeToggle />

          {/* Cart */}
          <Link href="/cart">
            <Button variant="ghost" size="icon" className="relative">
              <ShoppingCart className="h-5 w-5" />
              {cartItemCount > 0 && (
                <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-xs font-medium text-primary-foreground">
                  {cartItemCount}
                </span>
              )}
              <span className="sr-only">Корзина</span>
            </Button>
          </Link>

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <User className="h-5 w-5" />
                <span className="sr-only">Меню пользователя</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuItem asChild>
                <Link href="/dashboard" className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Личный кабинет
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href="/dashboard/downloads" className="flex items-center gap-2">
                  <Download className="h-4 w-4" />
                  Мои загрузки
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href="/dashboard/settings" className="flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  Настройки
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-destructive">
                <LogOut className="mr-2 h-4 w-4" />
                Выйти
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            <span className="sr-only">Меню</span>
          </Button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="border-t border-border bg-background md:hidden">
          <div className="container mx-auto px-4 py-4">
            <div className="mb-4">
              <Input type="search" placeholder="Поиск товаров..." className="w-full" />
            </div>
            <nav className="flex flex-col gap-2">
              <Link
                href="/catalog"
                className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-muted"
                onClick={() => setMobileMenuOpen(false)}
              >
                Каталог
              </Link>
              <Link
                href="/catalog?category=templates"
                className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-muted"
                onClick={() => setMobileMenuOpen(false)}
              >
                Шаблоны
              </Link>
              <Link
                href="/catalog?category=software"
                className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-muted"
                onClick={() => setMobileMenuOpen(false)}
              >
                Софт
              </Link>
              <Link
                href="/catalog?category=courses"
                className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-muted"
                onClick={() => setMobileMenuOpen(false)}
              >
                Курсы
              </Link>
              <Link
                href="/catalog?category=ebooks"
                className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-muted"
                onClick={() => setMobileMenuOpen(false)}
              >
                Книги
              </Link>
            </nav>
          </div>
        </div>
      )}
    </header>
  )
}
