# run-venv.ps1 для Windows
Write-Host "=== Настройка и запуск FastAPI приложения через Venv ===" -ForegroundColor Green

# Создание виртуального окружения (если его нет)
if (!(Test-Path "venv")) {
    Write-Host "Создание виртуального окружения..." -ForegroundColor Yellow
    python -m venv venv
}

# Активация venv
Write-Host "Активация виртуального окружения..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Установка зависимостей
Write-Host "Установка зависимостей из requirements.txt..." -ForegroundColor Yellow
pip install -r requirements.txt

# Запуск приложения
Write-Host "Запуск FastAPI приложения..." -ForegroundColor Green
Write-Host "Приложение доступно по адресу: http://localhost:5000" -ForegroundColor Cyan
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
