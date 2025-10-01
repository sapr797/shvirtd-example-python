# start-mysql.ps1 для Windows
Write-Host "Запуск MySQL в Docker..." -ForegroundColor Yellow

docker run -d `
  --name mysql-dev `
  -e MYSQL_ROOT_PASSWORD=rootpassword `
  -e MYSQL_DATABASE=example `
  -e MYSQL_USER=app `
  -e MYSQL_PASSWORD=very_strong `
  -p 3307:3306 `  # Обрати внимание на порт 3307
  mysql:8.0

Write-Host "MySQL запущен. Подождите 20 секунд для полной инициализации..." -ForegroundColor Yellow
Start-Sleep -Seconds 20
Write-Host "Проверка подключения к БД..." -ForegroundColor Yellow
docker exec mysql-dev mysql -u app -pvery_strong -e "SHOW DATABASES;"
