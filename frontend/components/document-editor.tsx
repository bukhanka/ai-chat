"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"

export function DocumentEditor() {
  const [content, setContent] = React.useState("")

  const handleSave = async () => {
    // Add save document logic here
    console.log("Saving document:", content)
  }

  return (
    <div className="container mx-auto p-4">
      <Card className="w-full max-w-4xl mx-auto">
        <CardContent className="p-6">
          <h2 className="text-2xl font-bold mb-4">Редактор документов</h2>
          <div className="space-y-4">
            <Textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Введите или вставьте текст документа здесь..."
              className="min-h-[400px]"
            />
            <Button 
              onClick={handleSave}
              className="w-full bg-[#1A0066] text-white hover:bg-[#2A1076]"
            >
              Сохранить документ
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

