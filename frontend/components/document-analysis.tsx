"use client"

import React from "react"
import axios from "axios"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { toast } from "sonner"
import { Textarea } from "@/components/ui/textarea"

// Enhanced type definitions for document analysis
interface DocumentRisk {
  severity: 'low' | 'medium' | 'high'
  description: string
  mitigation: string
}

interface DocumentAnalysisResult {
  success: boolean
  file_path?: string
  risks?: DocumentRisk[]
  summary?: string
  qa_results?: Record<string, string>
  error?: string
}

export function DocumentAnalysis() {
  const [file, setFile] = React.useState<File | null>(null)
  const [analysis, setAnalysis] = React.useState<DocumentAnalysisResult | null>(null)
  const [question, setQuestion] = React.useState("")
  const [isLoading, setIsLoading] = React.useState(false)

  // Update BASE_URL to match backend
  const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      toast.info("Файл загружен успешно")
    }
  }

  const analyzeDocument = async () => {
    if (!file) {
      toast.error("Пожалуйста, загрузите документ")
      return
    }

    setIsLoading(true)
    toast.loading("Начинаем анализ документа...", { duration: 2000 })
    
    const formData = new FormData()
    formData.append("file", file)

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 second timeout

      const response = await axios.post<DocumentAnalysisResult>(
        `${BASE_URL}/document/analyze`, 
        formData, 
        {
          headers: { "Content-Type": "multipart/form-data" },
          signal: controller.signal
        }
      )

      clearTimeout(timeoutId)

      if (response.data.success) {
        setAnalysis(response.data)
        toast.success("Анализ документа успешно завершен")
      } else {
        toast.error(response.data.error || "Не удалось проанализировать документ")
      }
    } catch (error) {
      if (axios.isAxiosError(error) && error.code === 'ECONNABORTED') {
        toast.error("Превышено время ожидания. Пожалуйста, попробуйте еще раз")
      } else {
        toast.error("Ошибка при анализе документа. Попробуйте еще раз")
      }
      console.error(error)
    } finally {
      setIsLoading(false)
    }
  }

  const askQuestion = async () => {
    if (!file || !question.trim()) {
      toast.error("Пожалуйста, загрузите документ и введите вопрос")
      return
    }

    setIsLoading(true)
    const formData = new FormData()
    formData.append("file", file)
    formData.append("questions", JSON.stringify([question]))

    try {
      const response = await axios.post(`${BASE_URL}/analyze/qa`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      })

      if (response.data.success) {
        setAnalysis(prev => ({
          ...prev,
          qa_results: {
            ...prev?.qa_results,
            [question]: response.data.qa_results?.answer || "Не удалось найти ответ"
          }
        }))
        toast.success("Ответ получен")
      } else {
        toast.error(response.data.error || "Не удалось получить ответ")
      }
    } catch (error) {
      toast.error("Ошибка при получении ответа")
      console.error(error)
    } finally {
      setIsLoading(false)
      setQuestion("")
    }
  }

  return (
    <div className="container mx-auto p-4">
      <Card className="w-full max-w-4xl mx-auto">
        <CardContent className="p-6">
          <h2 className="text-2xl font-bold mb-4">Анализ документов</h2>
          <div className="space-y-4">
            <div className="space-y-2">
              <Input
                type="file"
                onChange={handleFileUpload}
                accept=".pdf,.doc,.docx"
                className="w-full"
              />
              <Button 
                onClick={analyzeDocument}
                className="w-full bg-[#1A0066] text-white hover:bg-[#2A1076]"
                disabled={!file || isLoading}
              >
                {isLoading ? "Анализируем..." : "Анализировать документ"}
              </Button>
            </div>

            {analysis && (
              <div className="space-y-6">
                {/* Risks Section */}
                {analysis.risks && analysis.risks.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-xl font-semibold">Риски</h3>
                    <div className="space-y-2">
                      {analysis.risks.map((risk, index) => (
                        <div key={index} className="p-3 border rounded-lg">
                          <div className="font-semibold">
                            Уровень: {risk.severity.toUpperCase()}
                          </div>
                          <div>Описание: {risk.description}</div>
                          <div>Рекомендации: {risk.mitigation}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Summary Section */}
                {analysis.summary && (
                  <div className="space-y-2">
                    <h3 className="text-xl font-semibold">Краткое содержание</h3>
                    <div className="p-3 border rounded-lg">
                      {analysis.summary}
                    </div>
                  </div>
                )}

                {/* Q&A Section */}
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">Задать вопрос по документу</h3>
                  <div className="flex gap-2">
                    <Textarea
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      placeholder="Введите ваш вопрос..."
                      className="flex-grow"
                    />
                    <Button
                      onClick={askQuestion}
                      className="bg-[#1A0066] text-white hover:bg-[#2A1076]"
                      disabled={isLoading || !question.trim()}
                    >
                      Спросить
                    </Button>
                  </div>
                  {analysis.qa_results && Object.entries(analysis.qa_results).length > 0 && (
                    <div className="space-y-2">
                      {Object.entries(analysis.qa_results).map(([q, a], index) => (
                        <div key={index} className="p-3 border rounded-lg">
                          <div className="font-semibold">Q: {q}</div>
                          <div>A: {a}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 