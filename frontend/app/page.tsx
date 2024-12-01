import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function Home() {
  return (
    <main className="container mx-auto p-4 min-h-screen flex flex-col items-center justify-center">
      <h1 className="text-4xl font-bold mb-8 text-center">Сервис генерации юридических документов</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-8 w-full max-w-4xl">
        <Card className="bg-white border shadow-sm">
          <CardHeader>
            <CardTitle>ИИ Ассистент</CardTitle>
            <CardDescription>Создавайте юридические документы с помощью нашего ИИ ассистента.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="mb-4">Используйте наш чат-интерфейс с ИИ для простого создания и настройки юридических документов.</p>
            <Link href="/ai-assistant" passHref>
              <Button className="w-full bg-[#1A0066] text-white hover:bg-[#2A1076]">Начать чат с ИИ</Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="bg-gray-50 border shadow-sm">
          <CardHeader>
            <CardTitle>Традиционная форма</CardTitle>
            <CardDescription>Создавайте юридические документы, используя форму.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="mb-4">Заполните структурированные формы для быстрого создания стандартизированных юридических документов.</p>
            <Link href="/traditional-form" passHref>
              <Button className="w-full bg-[#1A0066] text-white hover:bg-[#2A1076]">Использовать форму</Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="bg-white border shadow-sm">
          <CardHeader>
            <CardTitle>Анализ документов</CardTitle>
            <CardDescription>Анализируйте юридические документы с помощью ИИ.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="mb-4">Загрузите документ для анализа его содержания и получения рекомендаций.</p>
            <Link href="/document-analysis" passHref>
              <Button className="w-full bg-[#1A0066] text-white hover:bg-[#2A1076]">Анализировать документ</Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="bg-gray-50 border shadow-sm">
          <CardHeader>
            <CardTitle>Редактор документов</CardTitle>
            <CardDescription>Редактируйте и форматируйте документы.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="mb-4">Используйте наш редактор для создания и редактирования юридических документов.</p>
            <Link href="/document-editor" passHref>
              <Button className="w-full bg-[#1A0066] text-white hover:bg-[#2A1076]">Открыть редактор</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </main>
  )
}

