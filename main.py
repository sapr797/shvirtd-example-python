from datetime import datetime
import os
from contextlib import contextmanager
import mysql.connector
from fastapi import FastAPI, Request
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

app = FastAPI(
    title="FastAPI MySQL Application",
    description="Обновленное приложение с конфигурацией через переменные окружения",
    version="2.0.0"
)

# Конфигурация из переменных окружения
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'user': os.getenv('DB_USER', 'app'),
    'password': os.getenv('DB_PASSWORD', 'very_strong'),
    'database': os.getenv('DB_NAME', 'example'),
    'port': os.getenv('DB_PORT', '3306')
}

# Получаем название таблицы из переменной окружения
TABLE_NAME = os.getenv('APP_TABLE_NAME', 'requests')

@contextmanager
def get_db_connection():
    """Контекстный менеджер для подключения к БД"""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        yield conn
    except mysql.connector.Error as e:
        print(f"Ошибка подключения к БД: {e}")
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения"""
    print("Приложение запускается...")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Используем переменную TABLE_NAME вместо жестко заданного названия
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                request_date DATETIME,
                request_ip VARCHAR(255),
                user_agent TEXT
            )
            """
            cursor.execute(create_table_query)
            conn.commit()
            cursor.close()
            print(f"Таблица '{TABLE_NAME}' готова к работе")
    except Exception as e:
        print(f"Ошибка инициализации БД: {e}")

@app.get("/")
async def read_root(request: Request):
    """Главная страница с записью в БД"""
    client_ip = request.client.host
    user_agent = request.headers.get('user-agent', 'Unknown')
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Используем переменную TABLE_NAME
            query = f"INSERT INTO {TABLE_NAME} (request_date, request_ip, user_agent) VALUES (%s, %s, %s)"
            values = (current_time, client_ip, user_agent)
            cursor.execute(query, values)
            
            # Получаем общее количество записей
            cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
            total_requests = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()

        return {
            "message": "Добро пожаловать в обновленное приложение!",
            "your_ip": client_ip,
            "time": current_time,
            "total_requests": total_requests,
            "table_name": TABLE_NAME,
            "environment": "production"
        }

    except mysql.connector.Error as e:
        return {"error": f"Ошибка базы данных: {e}"}

@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
        return {
            "status": "healthy",
            "database": "connected",
            "table_name": TABLE_NAME,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

@app.get("/requests")
async def get_requests(limit: int = 10):
    """Получить последние запросы"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = f"SELECT id, request_date, request_ip, user_agent FROM {TABLE_NAME} ORDER BY id DESC LIMIT %s"
            cursor.execute(query, (limit,))
            records = cursor.fetchall()
            cursor.close()

        result = []
        for record in records:
            result.append({
                "id": record[0],
                "request_date": record[1].strftime("%Y-%m-%d %H:%M:%S") if record[1] else None,
                "request_ip": record[2],
                "user_agent": record[3]
            })

        return {
            "total": len(result),
            "limit": limit,
            "table_name": TABLE_NAME,
            "requests": result
        }
    except Exception as e:
        return {"error": f"Ошибка чтения данных: {e}"}

@app.get("/config")
async def get_config():
    """Показать текущую конфигурацию"""
    return {
        "database_config": {
            "host": DB_CONFIG['host'],
            "database": DB_CONFIG['database'],
            "port": DB_CONFIG['port']
        },
        "table_name": TABLE_NAME,
        "environment": os.getenv('ENVIRONMENT', 'development')
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
