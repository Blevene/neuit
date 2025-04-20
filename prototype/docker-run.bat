@echo off
echo 🚀 Starting Knowledge Graph Application in Docker...

REM Check if Docker is installed
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker and Docker Compose first.
    exit /b 1
)

REM Check if Docker Compose is installed
where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

REM Build and start containers
echo 🐳 Building and starting containers...
docker compose build
docker compose up -d

REM Wait for services to start
echo ⏳ Waiting for services to start...
timeout /t 5 /nobreak >nul

REM Check Neo4j health status
echo 🔍 Checking Neo4j status...
set ATTEMPTS=0
set MAX_ATTEMPTS=10

:CHECK_NEO4J
if %ATTEMPTS% geq %MAX_ATTEMPTS% (
    echo ❌ Neo4j failed to start. Check the logs with 'docker logs neo4j-knowledge-graph'
    exit /b 1
)

docker ps | findstr neo4j-knowledge-graph >nul
if %errorlevel% neq 0 (
    set /a ATTEMPTS+=1
    echo ⏳ Waiting for Neo4j to start (attempt %ATTEMPTS%/%MAX_ATTEMPTS%)...
    timeout /t 5 /nobreak >nul
    goto CHECK_NEO4J
)

echo ✅ Neo4j is running!

REM Check if data needs to be imported
echo 🔍 Checking if data has been imported...
docker exec neo4j-knowledge-graph cypher-shell -u neo4j -p password "MATCH (c:Concept) RETURN count(c) AS count" | findstr "0 records" >nul
if %errorlevel% equ 0 (
    echo 📊 No data found. Importing data...
    echo ⚙️ Running the graph import script inside the container...
    docker exec knowledge-graph-frontend python graph_to_neo4j.py
) else (
    echo ✅ Data already exists in the database.
)

REM Show URLs to access the services
echo.
echo ✨ All services are running!
echo 📊 Access Neo4j Browser: http://localhost:7474
echo    Username: neo4j
echo    Password: password
echo.
echo 🔍 Access Knowledge Graph Explorer: http://localhost:8501
echo.
echo 🛑 To stop the services: docker compose down
echo 🧹 To stop and remove all data: docker compose down -v 