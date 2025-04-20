#!/bin/bash
set -e

echo "🚀 Setting up Neo4j Knowledge Graph environment..."

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

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Start Neo4j container
echo "🐳 Starting Neo4j Docker container..."
docker-compose up -d

# Wait for Neo4j to start up
echo "⏳ Waiting for Neo4j to start (this may take a minute)..."
sleep 10

# Test connection
echo "🔌 Testing connection to Neo4j..."
python test_neo4j_connection.py
if [ $? -ne 0 ]; then
    echo "❌ Connection test failed. Please check the logs above for troubleshooting."
    exit 1
fi

# Run the import script
echo "📊 Importing graph data..."
python graph_to_neo4j.py

echo "✅ Setup and import completed successfully!"
echo "🌐 You can access the Neo4j browser at http://localhost:7474"
echo "   Username: neo4j"
echo "   Password: password" 