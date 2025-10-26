from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uuid
from pathlib import Path

app = FastAPI(title="PDF Upload Service")

# Создаем директории для загрузок
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Настраиваем шаблоны
templates = Jinja2Templates(directory="templates")

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
    """Загрузка PDF файла и перенаправление на просмотр"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате PDF")
    
    # Генерируем уникальное имя файла
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}.pdf"
    
    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Перенаправляем на прямой просмотр PDF
    return RedirectResponse(url=f"/pdf/{file_id}", status_code=303)

@app.get("/pdf/{file_id}")
async def get_pdf(file_id: str):
    """Получение PDF файла для прямого просмотра в браузере"""
    file_path = UPLOAD_DIR / f"{file_id}.pdf"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    return FileResponse(
        file_path, 
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline",  # Отображать в браузере, а не скачивать
            "Cache-Control": "no-cache"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
