import os
import hashlib
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.documents import Document
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
import sys
import tempfile
import chardet
import tiktoken

# Import the document analysis functionality
from .document_analysis import DocumentAnalyzer, EnhancedDocumentAnalyzer

class RussianContractAdvisorChat:
    def __init__(self, api_key: str, user_id: str, persist_directory: str = "./chroma_db"):
        """
        Initialize the advisor with user-specific settings
        
        Args:
            api_key (str): OpenAI API key
            user_id (str): Unique user identifier
            persist_directory (str): Directory for persistent storage
        """
        self.api_key = api_key
        self.user_id = user_id
        self.persist_directory = os.path.join(persist_directory, user_id)
        
        # Create user's persistent directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key,
            temperature=0.7
        )
        
        self.embeddings = OpenAIEmbeddings(api_key=api_key)
        
        # Updated Chroma initialization
        self.vector_store = Chroma(
            collection_name=f"user_{user_id}",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        self.rag_mode = False
        self.file_hashes = self._load_file_hashes()
        
        self.memory = ConversationBufferMemory(
            return_messages=True, 
            human_prefix="Пользователь", 
            ai_prefix="Ассистент"
        )
        
        # Define system prompt
        system_prompt_text = """
        Вы - профессиональный юридический ассистент, специализирующийся на российских правовх документах.
        
        Ваши возможности включают:
        1. Анализ юридических документов:
           - Выявление рисков и уязвимостей
           - Идентификация ключевых положений
           - Сравнительный анализ с типовыми шаблонами
        
        2. Консультирование по договорам:
           - Выбор подходящего типа договора
           - Объяснение юридических терминов
           - Рекомендации по снижению рисков
           
        3. Работа с документами:
           - Анализ существующих договоров
           - Предложения по улучшению
           - Выявление потенциальных проблем
        
        Если вопрос выходит за рамки ваших возможностей или требует специализированной юридической консультации,
        рекомендуйте обратиться к профессиональному юристу.
        
        При работе с загруженным документом:
        - Если информация есть в документе - используйте её
        - Если информации в документе нет - отвечайте на основе общих знаний
        - Всегда указывайте источник информации (документ или общие знания)
        """
        
        self.system_prompt = SystemMessage(content=system_prompt_text)
        
        # Base prompt without context
        self.base_prompt = ChatPromptTemplate.from_messages([
            self.system_prompt,
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{user_input}")
        ])
        
        # RAG prompt with context
        self.rag_prompt = ChatPromptTemplate.from_messages([
            self.system_prompt,
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", """Контекст из документа:
            {context}
            
            Вопрос: {user_input}""")
        ])
        
        # Update the chain based on current RAG mode
        self._update_chain()

    def _update_chain(self):
        """
        Update the chain based on RAG mode with improved error handling
        """
        try:
            if self.rag_mode and self.vector_store:
                retriever = self.vector_store.as_retriever()
                self.chain = (
                    RunnablePassthrough.assign(
                        chat_history=lambda x: self.memory.chat_memory.messages,
                        context=lambda x: self._get_relevant_context(x["user_input"], retriever)
                    )
                    | self.rag_prompt
                    | self.llm
                    | StrOutputParser()
                )
            else:
                self.chain = (
                    RunnablePassthrough.assign(
                        chat_history=lambda x: self.memory.chat_memory.messages
                    )
                    | self.base_prompt
                    | self.llm
                    | StrOutputParser()
                )
        except Exception as e:
            print(f"Error updating chain: {e}")
            # Fallback to base prompt if RAG fails
            self.chain = (
                RunnablePassthrough.assign(
                    chat_history=lambda x: self.memory.chat_memory.messages
                )
                | self.base_prompt
                | self.llm
                | StrOutputParser()
            )

    def _load_file_hashes(self) -> Dict[str, str]:
        """Load existing file hashes from storage"""
        hash_file = os.path.join(self.persist_directory, "file_hashes.txt")
        if os.path.exists(hash_file):
            with open(hash_file, 'r') as f:
                return dict(line.strip().split(':') for line in f if line.strip())
        return {}

    def _save_file_hashes(self):
        """Save file hashes to storage"""
        hash_file = os.path.join(self.persist_directory, "file_hashes.txt")
        with open(hash_file, 'w') as f:
            for filename, file_hash in self.file_hashes.items():
                f.write(f"{filename}:{file_hash}\n")

    def _calculate_file_hash(self, file_path: Union[str, Path]) -> str:
        """Calculate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def load_documents(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Load multiple documents using the enhanced document analysis approach
        
        Args:
            files: List of dictionaries containing file information
                  Each dict should have 'path' and 'name' keys
        
        Returns:
            Dict with status and processed files information
        """
        processed_files = []
        try:
            document_analyzer = EnhancedDocumentAnalyzer(self.api_key)
            
            # New attribute to store document contents
            if not hasattr(self, 'document_contents'):
                self.document_contents = {}
            
            for file_info in files:
                file_path = file_info['path']
                file_name = file_info['name']
                
                try:
                    # Perform comprehensive document analysis
                    analysis_result = document_analyzer.comprehensive_document_analysis(file_path)
                    
                    if analysis_result['success']:
                        # Extract text for memory storage
                        document_text = document_analyzer._extract_text_from_file(file_path)
                        
                        # Store document contents
                        self.document_contents[file_name] = document_text
                        
                        # Always store in memory, regardless of length
                        self.memory.chat_memory.add_user_message(
                            f"Uploaded Document: {file_name}\n\n{document_text}"
                        )
                        
                        # Disable RAG mode
                        self.rag_mode = False
                        
                        # Save file hash
                        file_hash = self._calculate_file_hash(file_path)
                        self.file_hashes[file_name] = file_hash
                        self._save_file_hashes()
                        
                        processed_files.append({
                            'name': file_name,
                            'status': 'success',
                            'message': 'File processed successfully',
                            'processing_method': 'memory',
                            'analysis': analysis_result
                        })
                    else:
                        processed_files.append({
                            'name': file_name,
                            'status': 'error',
                            'message': analysis_result.get('error', 'Unknown error')
                        })
                
                except Exception as file_error:
                    processed_files.append({
                        'name': file_name,
                        'status': 'error',
                        'message': str(file_error)
                    })
            
            # Update chain to use base prompt without context retrieval
            self._update_chain()
            
            return {
                'success': len(processed_files) > 0,
                'processed_files': processed_files
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processed_files': processed_files
            }

    def _count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text using tiktoken
        
        Args:
            text (str): Input text
        
        Returns:
            int: Number of tokens
        """
        try:
            # Use the most common encoding for OpenAI models
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception as e:
            print(f"Error counting tokens: {e}")
            # Fallback to approximate word count if token counting fails
            return len(text.split())

    def clear_user_data(self):
        """Clear all user data including vector store and file hashes"""
        try:
            self.vector_store.delete_collection()
            self.vector_store = Chroma(
                collection_name=f"user_{self.user_id}",
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            self.file_hashes = {}
            # Clear document contents
            if hasattr(self, 'document_contents'):
                self.document_contents.clear()
            self._save_file_hashes()
            return {'success': True, 'message': 'User data cleared successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _get_relevant_context(self, query: str, retriever) -> str:
        """
        Get relevant context from vector store with improved retrieval
        
        Args:
            query (str): User query
            retriever: Vector store retriever
        
        Returns:
            str: Relevant context
        """
        try:
            # Limit the number of retrieved documents
            docs = retriever.get_relevant_documents(query, k=3)
            
            # Combine and truncate context
            context = "\n\n".join(doc.page_content for doc in docs)
            max_context_tokens = 1500  # Limit context to prevent exceeding model's context window
            
            # Truncate context if it's too long
            tokens = self._count_tokens(context)
            if tokens > max_context_tokens:
                encoding = tiktoken.get_encoding("cl100k_base")
                truncated_tokens = encoding.encode(context)[:max_context_tokens]
                context = encoding.decode(truncated_tokens)
            
            return context
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return ""

    def toggle_rag_mode(self, enabled: bool = True):
        """Toggle RAG mode on/off"""
        self.rag_mode = enabled and self.vector_store is not None
        self._update_chain()

    def process_conversation(self, user_input: str) -> Dict[str, Any]:
        """
        Обработка пользовательского ввода с учетом контекста документов
        
        Args:
            user_input (str): Сообщение пользователя
        
        Returns:
            Dict с ответом и состоянием диалога
        """
        try:
            # Добавление ввода пользователя в память
            self.memory.chat_memory.add_user_message(user_input)
            
            # Проверка наличия загруженных документов
            if hasattr(self, 'document_contents') and self.document_contents:
                # Добавление контекста документов к вводу
                document_context = "\n\n".join([
                    f"Документ '{name}':\n{content}" 
                    for name, content in self.document_contents.items()
                ])
                
                # Модифицируем цепочку для включения контекста документов
                modified_chain = (
                    RunnablePassthrough.assign(
                        chat_history=lambda x: self.memory.chat_memory.messages,
                        document_context=lambda x: document_context
                    )
                    | ChatPromptTemplate.from_messages([
                        self.system_prompt,
                        MessagesPlaceholder(variable_name="chat_history"),
                        ("human", """Контекст документов:
                        {document_context}
                        
                        Вопрос: {user_input}""")
                    ])
                    | self.llm
                    | StrOutputParser()
                )
                
                # Генерация ответа с учетом контекста документов
                response = modified_chain.invoke({
                    "user_input": user_input
                })
            else:
                # Стандартная обработка без контекста документов
                response = self.chain.invoke({
                    "user_input": user_input
                })
            
            # Добавление ответа ИИ в память
            self.memory.chat_memory.add_ai_message(response)
            
            # Проверка готовности к рекомендации договора
            is_ready_for_recommendation = self._check_recommendation_readiness()
            
            return {
                "success": True,
                "response": response,
                "ready_for_recommendation": is_ready_for_recommendation
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _check_recommendation_readiness(self) -> bool:
        """
        Определение готовности к рекомедции договора
        
        Returns:
            bool: Можно ли рекомендовать договор
        """
        messages = self.memory.chat_memory.messages
        
        # Ключевые информационные ключевые слова
        key_info_keywords = [
            "предмет договора", 
            "условия", 
            "участники", 
            "обязательства", 
            "оплата"
        ]
        
        # Проверка покрытия ключевой информации
        info_coverage = sum(
            any(keyword in msg.content.lower() for keyword in key_info_keywords) 
            for msg in messages
        )
        
        # Критерии готовности к рекомендации:
        # 1. Покрыто не менее 4 ключевых информационных точек
        # 2. Не менее 5 обменов сообщениями
        # 3. Последнее сообщение ИИ указывает на готовность
        return (
            info_coverage >= 4 and 
            len(messages) >= 5 and 
            any("Я считаю, что теперь у меня достаточно информации" in msg.content for msg in messages)
        )
    
    def get_contract_recommendation(self) -> Dict[str, Any]:
        """
        Генерация рекомендации по договору на основе истории диалога
        
        Returns:
            Dict с деталями рекомендации
        """
        try:
            # Компиляция истории диалога
            conversation_context = "\n".join([
                f"{msg.type}: {msg.content}" 
                for msg in self.memory.chat_memory.messages
            ])
            
            # Создание специализированного прмпта для рекомендации
            recommendation_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""
                На основе всего диалога предоставьте comprehensive рекомендацию по договору.
                Включите:
                1. Рекомендованный тип договора
                2. Ключевые условия
                3. Потенциальные риски
                4. Рекомендации по модификации
                
                Испльзуйте терминологию и структуру, соответствующую ГК РФ.
                """),
                ("human", "{conversation_context}")
            ])
            
            recommendation_chain = (
                recommendation_prompt 
                | self.llm 
                | StrOutputParser()
            )
            
            recommendation = recommendation_chain.invoke({
                "conversation_context": conversation_context
            })
            
            return {
                "success": True,
                "recommendation": self._parse_recommendation(recommendation)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_recommendation(self, response: str) -> Dict[str, Any]:
        """
        Парсинг рекомендации в структурированный формат
        
        Args:
            response (str): Текст рекомендации
        
        Returns:
            Словарь с parsed рекомендацией
        """
        sections = response.split('\n\n')
        parsed = {}
        
        for section in sections:
            if ':' in section:
                key, value = section.split(':', 1)
                parsed[key.strip()] = value.strip()
        
        return parsed

    def get_document_contents(self, file_name: Optional[str] = None) -> Union[str, Dict[str, str]]:
        """
        Retrieve document contents
        
        Args:
            file_name (Optional[str]): Specific file name to retrieve. 
                                       If None, returns all documents
        
        Returns:
            Document contents as string or dictionary of document contents
        """
        if not hasattr(self, 'document_contents'):
            return {} if file_name is None else ""
        
        if file_name is None:
            return self.document_contents
        
        return self.document_contents.get(file_name, "")

# Функция для управления диалогом
def russian_contract_advisor_chat(api_key: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Управление сессией консультанта по договорам
    
    Args:
        api_key (str): API-ключ OpenAI
        messages (List[Dict]): История диалоа
    
    Returns:
        Dict с ответом диалога
    """
    advisor = RussianContractAdvisorChat(api_key)
    
    # Обработка существующей истории диалога
    for msg in messages:
        result = advisor.process_conversation(msg['content'])
        
        # Проверка готовности к рекомендации
        if result.get('ready_for_recommendation', False):
            return advisor.get_contract_recommendation()
    
    # Возврат последнего ответа диалога
    return result

def main():
    """Интерактивный режим консультанта по договорам"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Ошибка: Не установлена перменная окружения OPENAI_API_KEY")
        sys.exit(1)
    
    # Using test user ID for terminal interface
    advisor = RussianContractAdvisorChat(
        api_key=api_key,
        user_id="terminal_test_user"
    )
    
    print("\n=== Консультант по договорам ===")
    print("Команды:")
    print("- 'load <путь_к_файлу>' для загрузки докумета")
    print("- 'rag on/off' для включения/выключения режима RAG")
    print("- 'exit' или 'quit' для выхода")
    print("\nВведите ваш вопрос или команду:\n")
    
    while True:
        try:
            user_input = input("\nВы: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("\nЗавершение работ...")
                break
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower().startswith('load '):
                file_path = user_input[5:].strip()
                result = advisor.load_documents([{
                    'path': file_path,
                    'name': os.path.basename(file_path)
                }])
                if result['success']:
                    print("\nДокумент успешно загружен и обработан")
                else:
                    print(f"\nОшибка при загрузке документа: {result.get('error', 'Неизвестная ошибка')}")
                continue
                
            if user_input.lower() == 'rag on':
                advisor.toggle_rag_mode(True)
                print("\nРежим RAG включен")
                continue
                
            if user_input.lower() == 'rag off':
                advisor.toggle_rag_mode(False)
                print("\nРежим RAG выключен")
                continue
            
            # Process regular input
            result = advisor.process_conversation(user_input)
            
            if result["success"]:
                print("\nАссистент:", result["response"])
                
                if result.get("ready_for_recommendation"):
                    print("\n[Система: Готов предоставить рекомендацию по договору]")
                    proceed = input("\nХотите получить рекомендацию? (да/нет): ").strip().lower()
                    
                    if proceed in ['да', 'y', 'yes']:
                        recommendation = advisor.get_contract_recommendation()
                        if recommendation["success"]:
                            print("\n=== Рекомендация по договору ===")
                            for key, value in recommendation["recommendation"].items():
                                print(f"\n{key}:")
                                print(value)
                            print("\n===============================")
            else:
                print("\nОшибка:", result["error"])
                
        except KeyboardInterrupt:
            print("\n\nЗавершение работы...")
            break
        except Exception as e:
            print(f"\nПроизошла ошибка: {str(e)}")

# if __name__ == "__main__":
    # main()