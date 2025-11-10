from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from fastapi.templating import Jinja2Templates
import uuid
import aiosqlite
from datetime import datetime

app = FastAPI(title="PDF Upload Service")

# Путь к базе данных
DB_PATH = "pdf_storage.db"

# Настраиваем шаблоны
templates = Jinja2Templates(directory="templates")

# Инициализация базы данных
async def init_db():
    """Создание таблицы для хранения PDF файлов"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pdf_files (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_data BLOB NOT NULL,
                upload_date TEXT NOT NULL,
                file_size INTEGER NOT NULL
            )
        """)
        await db.commit()

@app.on_event("startup")
async def startup_event():
    """Инициализация БД при запуске приложения"""
    await init_db()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Главная страница - временно не работает"""
    return templates.TemplateResponse("maintenance.html", {"request": request})

@app.get("/upload-files", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Страница загрузки PDF файлов"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Загрузка PDF файла и сохранение в SQLite"""
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате PDF")
    
    # Генерируем уникальный ID
    file_id = str(uuid.uuid4())
    
    # Читаем содержимое файла
    content = await file.read()
    file_size = len(content)
    
    # Сохраняем в базу данных
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO pdf_files (id, filename, file_data, upload_date, file_size)
            VALUES (?, ?, ?, ?, ?)
        """, (file_id, file.filename, content, datetime.now().isoformat(), file_size))
        await db.commit()
    
    # Перенаправляем на прямой просмотр PDF
    return RedirectResponse(url=f"/pdf/{file_id}", status_code=303)

@app.get("/pdf/{file_id}")
async def get_pdf(file_id: str):
    """Получение PDF файла из SQLite для прямого просмотра в браузере"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT file_data, filename FROM pdf_files WHERE id = ?
        """, (file_id,))
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Файл не найден")
        
        file_data = row["file_data"]
        filename = row["filename"]
    
    # Возвращаем PDF файл напрямую из базы данных
    return Response(
        content=file_data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=\"{filename}\"",  # Отображать в браузере, а не скачивать
            "Cache-Control": "no-cache"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
