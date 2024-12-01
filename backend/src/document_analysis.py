import os
import io
import logging
import html2text
from typing import Dict, Any, List, Union, Optional

# Updated imports
import docx
import PyPDF2
import mammoth
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models.chat_models import BaseChatModel

class DocumentAnalyzer:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Enhanced initialization with more flexible model selection
        
        Args:
            api_key (str): OpenAI API key
            model (str): Specific model to use, defaults to gpt-4o-mini
        """
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=0.5
        )
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = True
        self.html_converter.ignore_images = True
    
    def _extract_text_from_file(self, file_path: str) -> str:
        """
        Извлечение текста из различных типов документов
        
        Args:
            file_path (str): Путь к документу
        
        Returns:
            str: Извлеченный текстовый контент
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            with open(file_path, 'rb') as file:
                if file_extension == '.docx':
                    # Используем mammoth для лучшего парсинга DOCX
                    result = mammoth.convert_to_html(file)
                    # Конвертируем HTML в plain text
                    text = self.html_converter.handle(result.value)
                    return text
                
                elif file_extension == '.pdf':
                    # Используем PyPDF2 для парсинга PDF
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text
                
                elif file_extension == '.txt':
                    # Простой текстовый файл
                    return file.read().decode('utf-8')
                
                else:
                    raise ValueError(f"Неподдерживаемый тип файла: {file_extension}")
        
        except Exception as e:
            self.logger.error(f"Ошибка извлечения текста из {file_path}: {e}")
            raise
    
    def analyze_document(self, document_path: str) -> Dict[str, Any]:
        """
        Выполнение всестороннего анализа документа
        
        Args:
            document_path (str): Путь к файлу документа
        
        Returns:
            Dict с результатами анализа
        """
        try:
            # Извлечение текста из документа
            document_text = self._extract_text_from_file(document_path)
            
            # Усечение очень длинных документов для предотвращения проблем с токенами
            max_tokens = 15000  # Увеличено для более полного анализа
            document_text = document_text[:max_tokens]
            
            analysis_prompt = ChatPromptTemplate.from_messages([
                ("system", """
                Выполните всесторонний юридический анализ документа на русском языке:
                1. Выявите ключевые правовые положения
                2. Определите потенциальные риски и уязвимости
                3. Сравните с типовыми юридическими шаблонами
                4. Предоставьте оценку рисков и рекомендации
                
                Обратите особое внимание на:
                - Договорные обязательства
                - Потенциальные юридические лазейки
                - Соответствие российскому законодательству
                - Финансовые и правовые риски
                - Структурные и формальные особенности документа
                
                Формат ответа:
                Ключевые оложения: [список]
                Риски: [список]
                Рекомендации: [список]
                Примечания по соответствию: [список]
                """),
                ("human", "Проведите анализ следующего документа: {document_text}")
            ])
            
            chain = analysis_prompt | self.llm | StrOutputParser()
            
            analysis_result = chain.invoke({"document_text": document_text})
            
            return {
                "success": True,
                "file_path": document_path,
                "analysis": self._parse_analysis(analysis_result)
            }
        
        except Exception as e:
            self.logger.error(f"Не удалось выполнить анализ документа: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": document_path
            }
    
    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """
        Парсинг результатов анализа в структурированный формат
        
        Args:
            response (str): Текст результата анализа
        
        Returns:
            Словарь с структурированным анализом
        """
        sections = {
            "key_provisions": [],
            "risks": [],
            "recommendations": [],
            "compliance_notes": []
        }
        
        # Улучшенная логика парсинга
        current_section = None
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Более надежное определение секций
            if 'ключевые положения:' in line.lower():
                current_section = 'key_provisions'
                continue
            elif 'риски:' in line.lower():
                current_section = 'risks'
                continue
            elif 'рекомендации:' in line.lower():
                current_section = 'recommendations'
                continue
            elif 'примечания по соответствию:' in line.lower():
                current_section = 'compliance_notes'
                continue
            
            # Добавление строк в соответствующие секции
            if current_section and line and not line.endswith(':'):
                # ��е маркеров списка и лишних пробелов
                clean_line = line.lstrip('- ').lstrip('• ').strip()
                if clean_line:
                    sections[current_section].append(clean_line)
        
        return sections

class EnhancedDocumentAnalyzer(DocumentAnalyzer):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        super().__init__(api_key, model)
        
        # Add text_splitter as an attribute
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000, 
            chunk_overlap=200
        )
        
        # Обновленный risk_prompt на русском
        self.risk_prompt = ChatPromptTemplate.from_template(
            """Проведите ОБЯЗАТЕЛЬНЫЙ анализ рисков в документе:

            Текст документа: {text}

            ТРЕБОВАНИЯ:
            1. Найдите МИНИМУМ 3 риска
            2. Для КАЖДОГО риска укажите:
               - Уровень риска (Low/Medium/High)
               - Полное описание
               - Потенциальные последствия

            Если рисков нет, напишите "Существенных рисков не обнаружено".
            """
        )
        
        # Обновленный summary_prompt на русском
        self.summary_prompt = ChatPromptTemplate.from_template(
            """Подготовьте профессиональное, детальное и информативное резюме документа:

            Текст документа: {text}

            СТРУКТУРА РЕЗЮМЕ:
            1. Общая характеристика документа
               - Тип документа
               - Основная цель
               - Контекст создания

            2. Ключевые содержательные блоки:
               - Детальное описание каждого значимого раздела
               - Логические связи между разделами
               - Смысловые акценты

            3. Критический анализ:
               - Сильные стороны документа
               - Потенциальные недостатки
               - Соответствие стандартам и нормам

            4. Экспертные выводы:
               - Общая оценка документа
               - Рекомендации по использованию
               - Возможные направления доработки

            ТРЕБОВАНИЯ:
            - Профессиональный стиль
            - Максимальная информативность
            - Логическая структурированность
            - Объективность оценок
            """
        )
        
        # Обновленный qa_prompt на русском
        self.qa_prompt = ChatPromptTemplate.from_template(
            """Используйте предоставленный контекст для максимально точного ответа на вопрос:
            
            Контекст документа: {context}
            
            Вопрос: {question}
            
            Инструкции:
            - Отвечайте только на основе имеющегося контекста
            - Если точный ответ невозможен, предоставьте наиболее релевантную информацию
            - Используйте русский язык
            - Если ответ найти не удается, четко объясните причину
            """
        )
    
    def comprehensive_document_analysis(
        self, 
        document_path: str
    ) -> Dict[str, Any]:
        """
        Perform comprehensive document analysis
        """
        try:
            # Извлечение документа
            document_text = self._extract_text_from_file(document_path)
            
            # Текстовое разделение
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=4000, 
                chunk_overlap=200
            )
            texts = text_splitter.split_text(document_text)
            docs = [Document(page_content=text) for text in texts]
            
            # Анализ рисков
            risks_analysis = self._analyze_document_risks(document_text)
            
            # Генерация саммари
            summary = self._generate_document_summary(docs)
            
            # Опциональная ревизия документа
            revised_document = self._revise_document(document_text)
            
            return {
                "success": True,
                "file_path": document_path,
                "risks": risks_analysis,
                "summary": summary,
                "revised_document": revised_document
            }
        
        except Exception as e:
            self.logger.error(f"Comprehensive analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": document_path
            }
    
    def _analyze_document_risks(self, document_text: str) -> List[Dict[str, str]]:
        """
        Enhanced risk analysis with more robust processing
        
        Args:
            document_text (str): Full document text
        
        Returns:
            List of structured risks
        """
        try:
            risk_chain = (
                {"text": RunnablePassthrough()} 
                | self.risk_prompt 
                | self.llm 
                | StrOutputParser()
            )
            
            risks_text = risk_chain.invoke(document_text)
            
            # Add logging here
            print("Raw Risks Text:", risks_text)
            
            return self._parse_risks(risks_text)
        
        except Exception as e:
            self.logger.error(f"Risk analysis failed: {e}")
            return []
    
    def _generate_document_summary(self, docs: List[Document]) -> str:
        """
        More robust summary generation
        
        Args:
            docs (List[Document]): Document chunks
        
        Returns:
            Summarized text
        """
        try:
            # Combine all document chunks
            text = " ".join([doc.page_content for doc in docs])
            
            # Use a more robust summary chain
            summary_chain = (
                {"text": RunnablePassthrough()} 
                | self.summary_prompt 
                | self.llm 
                | StrOutputParser()
            )
            
            summary = summary_chain.invoke(text)
            
            # Ensure non-empty summary
            return summary if summary.strip() else "Unable to generate summary"
        
        except Exception as e:
            self.logger.error(f"Summary generation failed: {e}")
            return "Unable to generate summary"
    
    def _revise_document(self, document_text: str) -> Optional[str]:
        """
        Placeholder for document revision logic
        
        Args:
            document_text (str): Original document text
        
        Returns:
            Potentially revised document text
        """
        # Future implementation for document revision
        # Could involve legal language refinement, risk mitigation suggestions
        return None
    
    def _parse_risks(self, risks_text: str) -> List[Dict[str, str]]:
        print("Parsing Risks Text:", risks_text)  # Debug print
        
        risks = []
        if not risks_text or len(risks_text.strip()) < 10:
            print("No meaningful risks text found")
            return risks

        # More flexible parsing
        risk_sections = risks_text.split('\n\n')
        for section in risk_sections:
            if any(keyword in section.lower() for keyword in ['low', 'medium', 'high']):
                risk = {
                    'severity': 'Unknown',
                    'description': section.strip(),
                    'mitigation': ''
                }
                risks.append(risk)

        print(f"Parsed {len(risks)} risks")
        return risks

def analyze_legal_document(api_key: str, document_path: str) -> Dict[str, Any]:
    """
    Функция-обертка для анализа документа
    
    Args:
        api_key (str): API-ключ OpenAI
        document_path (str): Путь к документу для анализа
    
    Returns:
        Результаты анализа
    """
    analyzer = DocumentAnalyzer(api_key)
    return analyzer.analyze_document(document_path)

def analyze_comprehensive_document(
    api_key: str, 
    document_path: str
) -> Dict[str, Any]:
    """
    Wrapper function for comprehensive document analysis
    
    Args:
        api_key (str): OpenAI API key
        document_path (str): Path to document
    
    Returns:
        Comprehensive analysis results
    """
    analyzer = EnhancedDocumentAnalyzer(api_key)
    return analyzer.comprehensive_document_analysis(document_path)

# Пример использования при прямом запуске скрипта
# if __name__ == "__main__":
#     import os
#     import json
    
#     # Получение API-ключа из переменных окружения
#     api_key = os.getenv("OPENAI_API_KEY")
    
#     # Путь к тестовому документу
#     sample_document = "/home/dukhanin/fic/docs/Приказ о начале разработки.docx"
    
#     try:
#         # Создаем экземпляр расширенного анализатора документов
#         analyzer = EnhancedDocumentAnalyzer(api_key)
        
#         print("=" * 50)
#         print(" Comprehensive Document Analysis")
#         print("=" * 50)
        
#         # 1. Выполнение полного анализа документа
#         comprehensive_result = analyzer.comprehensive_document_analysis(
#             sample_document
#         )
        
#         # 2. Отдельный анализ рисков
#         print("\n📊 Риски в документе:")
#         risks = analyzer._analyze_document_risks(
#             analyzer._extract_text_from_file(sample_document)
#         )
#         for risk in risks:
#             print(f"- {risk}")
        
#         # 3. Генерация саммари
#         print("\n📝 Саммари документа:")
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=4000, 
#             chunk_overlap=200
#         )
#         document_text = analyzer._extract_text_from_file(sample_document)
#         texts = text_splitter.split_text(document_text)
#         docs = [Document(page_content=text) for text in texts]
        
#         summary = analyzer._generate_document_summary(docs)
#         print(summary)
        
#         # Красивый вывод полного результата
#         print("\n🏁 Полный результат анализа:")
#         print(json.dumps(comprehensive_result, indent=2, ensure_ascii=False))
    
#     except Exception as e:
#         print(f"Произошла ошибка при анализе документа: {e}")