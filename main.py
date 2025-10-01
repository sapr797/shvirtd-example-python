from datetime import datetime
import os
from contextlib import contextmanager
import mysql.connector
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

app = FastAPI(
    title="Shvirtd Example FastAPI",
    description="Учебный проект для изучения Docker Compose и FastAPI.",
    version="1.0.0"
)

# Конфигурация БД из переменных окружения
db_config = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'user': os.getenv('DB_USER', 'app'),
    'password': os.getenv('DB_PASSWORD', 'very_strong'),
    'database': os.getenv('DB_NAME', 'example')
}

# Название таблицы также можно вынести в переменные окружения
TABLE_NAME = os.getenv('APP_TABLE_NAME', 'requests')

@contextmanager
def get_db_connection():
    """
    Контекстный менеджер для подключения к БД.
    Обеспечивает правильное закрытие соединения.
    """
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        yield conn
    except mysql.connector.Error as e:
        print(f"Ошибка подключения к БД: {e}")
        raise HTTPException(status_code=500, detail="Ошибка базы данных")
    finally:
        if conn is not None and conn.is_connected():
            conn.close()

@app.on_event("startup")
async def startup_event():
    """Инициализация базы данных при запуске приложения"""
    print("Приложение запускается...")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                request_date DATETIME,
                request_ip VARCHAR(255)
            )
            """
            cursor.execute(create_table_query)
            conn.commit()
            cursor.close()
            print(f"Таблица '{TABLE_NAME}' готова к работе.")
    except Exception as e:
        print(f"Ошибка при инициализации БД: {e}")

@app.get("/")
async def read_root(request: Request):
    """Главная страница - записывает запрос в БД и возвращает время и IP"""
    client_ip = request.client.host
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = f"INSERT INTO {TABLE_NAME} (request_date, request_ip) VALUES (%s, %s)"
            values = (current_time, client_ip)
            cursor.execute(query, values)
            conn.commit()
            cursor.close()
    except mysql.connector.Error as e:
        return {"error": f"Ошибка при работе с базой данных: {e}"}

    # Проверка правильности обращения через прокси
    x_real_ip = request.headers.get('x-real-ip')
    if x_real_ip is None:
        ip_display = "похоже, что вы направляете запрос в неверный порт (например curl http://127.0.0.1:5000). Правильное выполнение задания - отправить запрос в порт 8090."
    else:
        ip_display = x_real_ip

    return f'TIME: {current_time}, IP: {ip_display}'

@app.get("/health")
async def health_check():
    """Проверка состояния приложения и подключения к БД"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.get("/requests")
async def get_requests():
    """Возвращает последние записи из базы данных"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = f"SELECT id, request_date, request_ip FROM {TABLE_NAME} ORDER BY id DESC LIMIT 50"
            cursor.execute(query)
            records = cursor.fetchall()
            cursor.close()
            
            result = []
            for record in records:
                result.append({
                    "id": record[0],
                    "request_date": record[1].strftime("%Y-%m-%d %H:%M:%S") if record[1] else None,
                    "request_ip": record[2]
                })
            
            return {
                "total_records": len(result),
                "records": result
            }
    except mysql.connector.Error as e:
        return {"error": f"Ошибка при чтении из базы данных: {e}"}

@app.get("/debug")
async def debug_headers(request: Request):
    """Отладочная информация о заголовках запроса"""
    return {
        "headers": dict(request.headers),
        "client_host": request.client.host if request.client else None,
        "x_forwarded_for": request.headers.get('x-forwarded-for'),
        "x_real_ip": request.headers.get('x-real-ip'),
        "forwarded": request.headers.get('forwarded')
    }

# Точка входа для запуска приложения напрямую
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
