#!/bin/bash
echo "Starting Knowledge Graph Explorer..."

# Check if Docker is running Neo4j
if ! docker ps | grep -q neo4j-knowledge-graph; then
    echo "Neo4j container not running. Starting it now..."
    docker compose up -d
    echo "Waiting for Neo4j to start..."
    sleep 10
fi

# Run the Streamlit app
echo "Starting Streamlit server..."
streamlit run knowledge_graph_explorer.py 