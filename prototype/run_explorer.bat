@echo off
echo Starting Knowledge Graph Explorer...

REM Check if Docker is running Neo4j
docker ps | findstr neo4j-knowledge-graph > nul
if %errorlevel% neq 0 (
    echo Neo4j container not running. Starting it now...
    docker compose up -d
    echo Waiting for Neo4j to start...
    timeout /t 10 /nobreak > nul
)

REM Run the Streamlit app
echo Starting Streamlit server...
streamlit run knowledge_graph_explorer.py 