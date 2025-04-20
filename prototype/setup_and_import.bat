@echo off
echo 🚀 Setting up Neo4j Knowledge Graph environment...

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

REM Install Python dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

REM Start Neo4j container
echo 🐳 Starting Neo4j Docker container...
docker-compose up -d

REM Wait for Neo4j to start up
echo ⏳ Waiting for Neo4j to start (this may take a minute)...
timeout /t 10 /nobreak >nul

REM Test connection
echo 🔌 Testing connection to Neo4j...
python test_neo4j_connection.py
if %errorlevel% neq 0 (
    echo ❌ Connection test failed. Please check the logs above for troubleshooting.
    exit /b 1
)

REM Run the import script
echo 📊 Importing graph data...
python graph_to_neo4j.py

echo ✅ Setup and import completed successfully!
echo 🌐 You can access the Neo4j browser at http://localhost:7474
echo    Username: neo4j
echo    Password: password 