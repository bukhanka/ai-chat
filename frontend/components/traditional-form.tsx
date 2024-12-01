"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"

export function TraditionalForm() {
  const [documentType, setDocumentType] = useState("")

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    console.log("Форма отправлена")
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="document-type">Выберите тип документа</Label>
        <Select onValueChange={setDocumentType}>
          <SelectTrigger id="document-type">
            <SelectValue placeholder="Выберите тип документа" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="contract">Договор</SelectItem>
            <SelectItem value="claim">Претензия</SelectItem>
            <SelectItem value="complaint">Жалоба</SelectItem>
            <SelectItem value="power-of-attorney">Доверенность</SelectItem>
          </SelectContent>
        </Select>
      </div>
      {documentType && (
        <>
          <div className="space-y-2">
            <Label htmlFor="party1">Сторона 1</Label>
            <Input id="party1" placeholder="Введите имя первой стороны" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="party2">Сторона 2</Label>
            <Input id="party2" placeholder="Введите имя второй стороны" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="details">Детали документа</Label>
            <Textarea id="details" placeholder="Введите детали документа" />
          </div>
          <Button type="submit" className="bg-[#1A0066] text-white hover:bg-[#2A1076]">
            Создать документ
          </Button>
        </>
      )}
    </form>
  )
}

