# legal-ai-assistant

## Запуск проекта

```
cp .env.example .env
```

```
cd backend
python3 -m venv .venv
# linux
source .venv/bin/activate
# windows
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

в новом терминале

```
cd frontend
npm install
npm run dev
```


## Содержимое проекта

* `backend` - бэкенд проекта
main.py - апи 
src/tools.py - инструменты для работы c чатом
src/document_analysis.py - анализ документов


src/parsers/rid_docs_parser.py - парсер документов рида

* `frontend` - фронтенд проекта
* `docs` - прочие файлы 
# ai-chat
