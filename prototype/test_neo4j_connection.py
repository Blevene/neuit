import sys
from neo4j import GraphDatabase

# Neo4j connection settings - same as in graph_to_neo4j.py
URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "password"

def test_connection():
    """Test connection to Neo4j database."""
    print("Testing connection to Neo4j Docker container...")
    
    try:
        driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
        
        # Test basic query
        with driver.session() as session:
            result = session.run("RETURN 'Connection successful!' AS message")
            message = result.single()[0]
            print(f"✅ {message}")
            
            # Get Neo4j version
            result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions")
            record = result.single()
            print(f"✅ Connected to {record['name']} version {record['versions'][0]}")
            
        driver.close()
        print("✅ Connection test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Make sure Docker is running")
        print("2. Check if the Neo4j container is up with: docker ps")
        print("3. If container isn't running, start it with: docker-compose up -d")
        print("4. Check container logs with: docker logs neo4j-knowledge-graph")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1) 