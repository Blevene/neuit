#!/bin/bash
set -e

echo "🚀 Starting Knowledge Graph Application in Docker..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker and Docker Compose first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Build and start containers
echo "🐳 Building and starting containers..."
docker compose build
docker compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 5

# Check Neo4j health status
echo "🔍 Checking Neo4j status..."
ATTEMPTS=0
MAX_ATTEMPTS=10
while [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    if docker ps | grep -q neo4j-knowledge-graph && docker exec neo4j-knowledge-graph wget --quiet --tries=1 --spider http://localhost:7474; then
        echo "✅ Neo4j is running!"
        break
    fi
    ATTEMPTS=$((ATTEMPTS+1))
    echo "⏳ Waiting for Neo4j to start (attempt $ATTEMPTS/$MAX_ATTEMPTS)..."
    sleep 5
done

if [ $ATTEMPTS -eq $MAX_ATTEMPTS ]; then
    echo "❌ Neo4j failed to start. Check the logs with 'docker logs neo4j-knowledge-graph'"
    exit 1
fi

# Check if data needs to be imported
echo "🔍 Checking if data has been imported..."
if docker exec neo4j-knowledge-graph cypher-shell -u neo4j -p password "MATCH (c:Concept) RETURN count(c) AS count" | grep -q "0 records"; then
    echo "📊 No data found. Importing data..."
    echo "⚙️ Running the graph import script inside the container..."
    docker exec knowledge-graph-frontend python graph_to_neo4j.py
else
    echo "✅ Data already exists in the database."
fi

# Show URLs to access the services
echo ""
echo "✨ All services are running!"
echo "📊 Access Neo4j Browser: http://localhost:7474"
echo "   Username: neo4j"
echo "   Password: password"
echo ""
echo "🔍 Access Knowledge Graph Explorer: http://localhost:8501"
echo ""
echo "🛑 To stop the services: docker compose down"
echo "🧹 To stop and remove all data: docker compose down -v" 