"use client"

import { useState, useRef } from "react"
import axios from "axios"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"
import { toast } from "sonner"
import ReactMarkdown from 'react-markdown'
import { Upload, Send, X } from 'lucide-react'

export function AIAssistant() {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [attachedFiles, setAttachedFiles] = useState<string[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Update BASE_URL to match backend
  const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

  const handleSend = async () => {
    if (!input.trim()) return

    setMessages([...messages, { role: "user", content: input }])
    setIsLoading(true)

    try {
      const response = await axios.post(`${BASE_URL}/chat`, {
        message: input
      })

      if (response.data.success) {
        setMessages(prev => [...prev, { role: "assistant", content: response.data.response }])
        
        // Check if recommendation is ready
        if (response.data.ready_for_recommendation) {
          const recommendationResponse = await axios.get(`${BASE_URL}/recommendations`)
          if (recommendationResponse.data.success) {
            setMessages(prev => [...prev, { 
              role: "assistant", 
              content: "### Рекомендация по договору\n\n" + 
                Object.entries(recommendationResponse.data.recommendation)
                  .map(([key, value]) => `**${key}:**\n${value}`)
                  .join("\n\n")
            }])
          }
        }
      } else {
        toast.error(response.data.error || "Не у��алось получить ответ")
      }
    } catch (error) {
      toast.error("Ошибка при отправке сообщения")
      console.error(error)
    } finally {
      setIsLoading(false)
      setInput("")
    }
  }

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return

    setIsUploading(true)
    const formData = new FormData()
    
    Array.from(files).forEach(file => {
      formData.append('files', file)
    })

    try {
      const response = await axios.post(`${BASE_URL}/documents/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (response.data.success) {
        const processedFiles = response.data.processed_files
        const successFiles = processedFiles
          .filter((file: any) => file.status === 'success')
          .map((file: any) => file.name)
        
        setAttachedFiles(prev => [...prev, ...successFiles])
        
        const message = processedFiles.map((file: any) => 
          `${file.name}: ${file.status === 'success' ? '✓ загружен' : `⚠ ${file.message}`}`
        ).join('\n')
        
        setMessages(prev => [...prev, {
          role: "assistant",
          content: `Загрузка документов завершена:\n${message}`
        }])
        toast.success("Документы успешно загружены")
      } else {
        toast.error(response.data.error || "Ошибка при загрузке документов")
      }
    } catch (error) {
      toast.error("Ошибка при загрузке документов")
      console.error(error)
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const removeFile = (fileName: string) => {
    setAttachedFiles(prev => prev.filter(f => f !== fileName))
  }

  const handleQuickOption = (option: string) => {
    setInput(option)
    handleSend()
  }

  const clearUserData = async () => {
    try {
      const response = await axios.delete(`${BASE_URL}/user/data`)
      if (response.data.success) {
        setMessages([])
        toast.success("История очищена")
      } else {
        toast.error(response.data.error || "Ошибка при очистке истории")
      }
    } catch (error) {
      toast.error("Ошибка при очистке истории")
      console.error(error)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto p-4 space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold">AI-Ассистент для Работы с Документами</h1>
          <div className="flex items-center gap-4">
            <Button
              onClick={clearUserData}
              variant="outline"
              className="text-red-600 hover:text-red-700"
            >
              Очистить историю
            </Button>
            <Link href="/" className="text-sm text-blue-600 hover:text-blue-800">
              Назад на главную
            </Link>
          </div>
        </div>

        <div className="flex gap-6">
          <div className="w-1/4 space-y-4">
            <Card className="bg-white border shadow-sm">
              <CardContent className="p-4">
                <h3 className="font-semibold text-lg mb-4">Частые вопросы:</h3>
                <div className="flex flex-col gap-2">
                  <Button 
                    variant="outline" 
                    onClick={() => handleQuickOption("Какие основные элементы договора?")}
                    className="justify-start text-left h-auto py-3 px-4 bg-white hover:bg-gray-50"
                  >
                    Элементы договора
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={() => handleQuickOption("Как подать юридическую претензию?")}
                    className="justify-start text-left h-auto py-3 px-4 bg-white hover:bg-gray-50"
                  >
                    Подача претензии
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={() => handleQuickOption("Какой процесс подачи жалобы?")}
                    className="justify-start text-left h-auto py-3 px-4 bg-white hover:bg-gray-50"
                  >
                    Процесс жалобы
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="flex-1 space-y-4">
            {attachedFiles.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {attachedFiles.map((fileName, index) => (
                  <Badge 
                    key={index} 
                    variant="secondary"
                    className="flex items-center gap-2 py-1 px-3"
                  >
                    {fileName}
                    <X 
                      className="h-4 w-4 cursor-pointer hover:text-red-500" 
                      onClick={() => removeFile(fileName)}
                    />
                  </Badge>
                ))}
              </div>
            )}

            <Card className="bg-white border shadow-sm">
              <CardContent className="p-6">
                <div className="h-[600px] overflow-y-auto space-y-4 scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-transparent">
                  {messages.map((message, index) => (
                    <div key={index} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div
                        className={`max-w-[80%] p-3 rounded-lg ${
                          message.role === "user" 
                            ? "bg-blue-50 text-gray-900" 
                            : "bg-gray-50 text-gray-900"
                        }`}
                      >
                        <ReactMarkdown>{message.content}</ReactMarkdown>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <div className="flex gap-2">
              <input
                type="file"
                ref={fileInputRef}
                onChange={(e) => handleFileUpload(e.target.files)}
                multiple
                accept=".pdf,.txt,.doc,.docx"
                className="hidden"
              />
              <Button
                onClick={() => fileInputRef.current?.click()}
                variant="outline"
                className="px-3"
                disabled={isUploading}
              >
                <Upload className="h-5 w-5" />
              </Button>
              <Input
                type="text"
                placeholder="Введите ваше сообщение..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSend()}
                className="bg-white shadow-sm"
              />
              <Button 
                onClick={handleSend} 
                className="bg-[#1A0066] text-white hover:bg-[#2A1076] px-4"
                disabled={isLoading}
              >
                {isLoading ? (
                  "..."
                ) : (
                  <Send className="h-5 w-5" />
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

