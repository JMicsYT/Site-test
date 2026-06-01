"use client"

import { useState } from "react"
import { Header } from "@/components/layout/header"
import { Footer } from "@/components/layout/footer"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { Camera, Save, Bell, Shield, Eye, Mail } from "lucide-react"

export default function SettingsPage() {
  const [isSaving, setIsSaving] = useState(false)

  const handleSave = () => {
    setIsSaving(true)
    setTimeout(() => setIsSaving(false), 1000)
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 bg-muted/30">
        <div className="container mx-auto px-4 py-8">
          <div className="mb-8">
            <h1 className="mb-2 text-3xl font-bold text-foreground">Настройки</h1>
            <p className="text-muted-foreground">
              Управляйте своим профилем и настройками аккаунта
            </p>
          </div>

          <Tabs defaultValue="profile" className="space-y-6">
            <TabsList>
              <TabsTrigger value="profile">Профиль</TabsTrigger>
              <TabsTrigger value="security">Безопасность</TabsTrigger>
              <TabsTrigger value="notifications">Уведомления</TabsTrigger>
            </TabsList>

            {/* Profile Tab */}
            <TabsContent value="profile">
              <div className="grid gap-6 lg:grid-cols-3">
                {/* Avatar Card */}
                <Card>
                  <CardHeader>
                    <CardTitle>Фото профиля</CardTitle>
                    <CardDescription>
                      Загрузите фото или аватар
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="flex flex-col items-center">
                    <div className="relative mb-4">
                      <Avatar className="h-32 w-32">
                        <AvatarImage src="" />
                        <AvatarFallback className="text-4xl">ИИ</AvatarFallback>
                      </Avatar>
                      <Button
                        size="icon"
                        className="absolute bottom-0 right-0 h-10 w-10 rounded-full"
                      >
                        <Camera className="h-5 w-5" />
                      </Button>
                    </div>
                    <p className="text-center text-sm text-muted-foreground">
                      JPG, PNG или GIF. Максимум 2MB.
                    </p>
                  </CardContent>
                </Card>

                {/* Profile Info Card */}
                <Card className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle>Личные данные</CardTitle>
                    <CardDescription>
                      Обновите информацию о себе
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="firstName">Имя</Label>
                        <Input id="firstName" defaultValue="Иван" />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="lastName">Фамилия</Label>
                        <Input id="lastName" defaultValue="Иванов" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <Input id="email" type="email" defaultValue="ivan@example.com" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="phone">Телефон</Label>
                      <Input id="phone" type="tel" defaultValue="+7 (999) 123-45-67" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="bio">О себе</Label>
                      <Input id="bio" placeholder="Расскажите о себе..." />
                    </div>
                    <Button onClick={handleSave} disabled={isSaving} className="gap-2">
                      <Save className="h-4 w-4" />
                      {isSaving ? "Сохранение..." : "Сохранить изменения"}
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Security Tab */}
            <TabsContent value="security">
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Shield className="h-5 w-5" />
                      Изменить пароль
                    </CardTitle>
                    <CardDescription>
                      Регулярно обновляйте пароль для безопасности аккаунта
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="currentPassword">Текущий пароль</Label>
                      <Input id="currentPassword" type="password" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="newPassword">Новый пароль</Label>
                      <Input id="newPassword" type="password" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="confirmPassword">Подтвердите пароль</Label>
                      <Input id="confirmPassword" type="password" />
                    </div>
                    <Button className="gap-2">
                      <Shield className="h-4 w-4" />
                      Обновить пароль
                    </Button>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Eye className="h-5 w-5" />
                      Двухфакторная аутентификация
                    </CardTitle>
                    <CardDescription>
                      Добавьте дополнительный уровень защиты
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-foreground">
                          Аутентификация через приложение
                        </p>
                        <p className="text-sm text-muted-foreground">
                          Используйте Google Authenticator или аналог
                        </p>
                      </div>
                      <Switch />
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-destructive">
                  <CardHeader>
                    <CardTitle className="text-destructive">Удаление аккаунта</CardTitle>
                    <CardDescription>
                      Это действие необратимо. Все ваши данные будут удалены.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button variant="destructive">Удалить аккаунт</Button>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Notifications Tab */}
            <TabsContent value="notifications">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Bell className="h-5 w-5" />
                    Настройки уведомлений
                  </CardTitle>
                  <CardDescription>
                    Выберите, какие уведомления вы хотите получать
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <h4 className="mb-4 font-medium text-foreground">Email уведомления</h4>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-foreground">Новости и обновления</p>
                          <p className="text-sm text-muted-foreground">
                            Получайте информацию о новых товарах и акциях
                          </p>
                        </div>
                        <Switch defaultChecked />
                      </div>
                      <Separator />
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-foreground">Обновления продуктов</p>
                          <p className="text-sm text-muted-foreground">
                            Уведомления о новых версиях купленных товаров
                          </p>
                        </div>
                        <Switch defaultChecked />
                      </div>
                      <Separator />
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-foreground">Заказы и доставка</p>
                          <p className="text-sm text-muted-foreground">
                            Подтверждения покупок и ссылки для скачивания
                          </p>
                        </div>
                        <Switch defaultChecked />
                      </div>
                      <Separator />
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-foreground">Маркетинговые рассылки</p>
                          <p className="text-sm text-muted-foreground">
                            Специальные предложения и скидки
                          </p>
                        </div>
                        <Switch />
                      </div>
                    </div>
                  </div>

                  <Button className="gap-2">
                    <Mail className="h-4 w-4" />
                    Сохранить настройки
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </main>
      <Footer />
    </div>
  )
}
