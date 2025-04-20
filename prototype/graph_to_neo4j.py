import json
import re
import time
import sys
import os
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

# Neo4j Docker connection settings from environment variables or default values
URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
USERNAME = os.environ.get("NEO4J_USER", "neo4j")
PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")
MAX_RETRIES = 5
RETRY_DELAY = 3  # seconds

def slugify(text):
    """Convert text to a normalized form suitable for URIs."""
    # Convert to lowercase
    text = text.lower()
    # Replace spaces with underscores
    text = re.sub(r'\s+', '_', text)
    # Remove special characters
    text = re.sub(r'[^\w\s_]', '', text)
    return text

def connect_with_retry():
    """Connect to Neo4j with retry mechanism for Docker startup."""
    retries = 0
    while retries < MAX_RETRIES:
        try:
            print(f"Connecting to Neo4j at {URI} (attempt {retries + 1}/{MAX_RETRIES})...")
            driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
            # Verify connection
            with driver.session() as session:
                session.run("RETURN 1").single()
            print("✅ Successfully connected to Neo4j")
            return driver
        except ServiceUnavailable:
            print(f"⚠️ Neo4j is not available yet. Waiting {RETRY_DELAY} seconds...")
            retries += 1
            time.sleep(RETRY_DELAY)
        except AuthError:
            print("❌ Authentication failed. Check your username and password.")
            print(f"   Attempted connection to {URI} with user {USERNAME}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
            print("\nDocker troubleshooting tips:")
            print("1. Check if Neo4j container is running: docker ps")
            print("2. View container logs: docker logs neo4j-knowledge-graph")
            print("3. Restart container: docker compose restart neo4j")
            sys.exit(1)
    
    print("❌ Failed to connect to Neo4j after multiple attempts")
    print("   Please make sure Docker is running and the Neo4j container is healthy")
    print("   Run: docker compose ps")
    print("   Run: docker logs neo4j-knowledge-graph")
    sys.exit(1)

def create_knowledge_graph():
    """Main function to read JSONL and create Neo4j graph."""
    # Connect to Neo4j with retry logic
    driver = connect_with_retry()
    
    print("🔍 Creating knowledge graph from improved_graph.jsonl...")
    
    # Determine the correct file path whether running in Docker or not
    file_path = 'data/corpus/graph/improved_graph.jsonl'
    if not os.path.exists(file_path):
        file_path = 'prototype/data/corpus/graph/improved_graph.jsonl'
    
    if not os.path.exists(file_path):
        print(f"❌ Could not find the data file at {file_path}")
        print("   Please make sure the file exists and is accessible.")
        sys.exit(1)
    
    try:
        with driver.session() as session:
            # Create constraints for unique node IDs
            print("📊 Creating constraints for unique node IDs...")
            session.run("CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE")
            session.run("CREATE CONSTRAINT label_id IF NOT EXISTS FOR (l:Label) REQUIRE l.id IS UNIQUE")
            session.run("CREATE CONSTRAINT rule_id IF NOT EXISTS FOR (r:Rule) REQUIRE r.id IS UNIQUE")
            session.run("CREATE CONSTRAINT ontology_class_id IF NOT EXISTS FOR (o:OntologyClass) REQUIRE o.id IS UNIQUE")
            
            # Read and process JSONL file
            print(f"📖 Reading JSONL data from {file_path}...")
            concepts = []
            with open(file_path, 'r') as file:
                for line in file:
                    if line.strip():
                        concepts.append(json.loads(line))
            
            # Create nodes and relationships
            print(f"🔨 Creating nodes for {len(concepts)} concepts...")
            for i, concept in enumerate(concepts):
                create_concept_nodes(session, concept)
                if (i + 1) % 10 == 0 or i + 1 == len(concepts):
                    print(f"   Progress: {i + 1}/{len(concepts)} concepts processed")
            
            # Create relationship edges after all nodes are created
            print("🔗 Creating relationships between nodes...")
            for i, concept in enumerate(concepts):
                create_relationships(session, concept)
                if (i + 1) % 10 == 0 or i + 1 == len(concepts):
                    print(f"   Progress: {i + 1}/{len(concepts)} relationships processed")
                
            print(f"✅ Successfully created knowledge graph with {len(concepts)} concepts")
    
    finally:
        driver.close()

def create_concept_nodes(session, concept_data):
    """Create concept nodes and associated label nodes."""
    # Create Concept node
    concept_id = concept_data["concept"]
    concept_name = concept_data["concept_name"]
    from_ontology = concept_data["from_ontology"]
    sources = json.dumps(concept_data["sources"])
    
    session.run("""
        MERGE (c:Concept {id: $id})
        SET c.name = $name,
            c.from_ontology = $from_ontology,
            c.sources = $sources
    """, id=concept_id, name=concept_name, from_ontology=from_ontology, sources=sources)
    
    # Create Label nodes and HAS_LABEL relationships
    for i, label_data in enumerate(concept_data.get("labels", [])):
        label_id = f"{concept_id}_label_{i}"
        label_text = label_data["text"]
        label_type = label_data["type"]
        justification = label_data["justification"]
        
        session.run("""
            MERGE (l:Label {id: $id})
            SET l.text = $text,
                l.type = $type,
                l.justification = $justification
            WITH l
            MATCH (c:Concept {id: $concept_id})
            MERGE (c)-[:HAS_LABEL]->(l)
        """, id=label_id, text=label_text, type=label_type, justification=justification, concept_id=concept_id)
    
    # Create Rule nodes
    for rule_data in concept_data.get("rule_data", []):
        rule_id = rule_data["id"]
        if_text = rule_data["if_text"]
        then_text = rule_data["then_text"]
        confidence = rule_data["confidence"]
        justification = rule_data.get("justification", "")
        ontology_classes = json.dumps(rule_data.get("ontology_classes", []))
        
        session.run("""
            MERGE (r:Rule {id: $id})
            SET r.if_text = $if_text,
                r.then_text = $then_text,
                r.confidence = $confidence,
                r.justification = $justification,
                r.ontology_classes = $ontology_classes
        """, id=rule_id, if_text=if_text, then_text=then_text, confidence=confidence, 
            justification=justification, ontology_classes=ontology_classes)
    
    # Create OntologyClass node if from_ontology is true
    if from_ontology and "ontology_data" in concept_data:
        ont_data = concept_data["ontology_data"]
        superclass = ont_data.get("superclass", "")
        superclass_name = ont_data.get("superclass_name", "")
        description = ont_data.get("description", "")
        properties = json.dumps(ont_data.get("properties", []))
        
        session.run("""
            MERGE (o:OntologyClass {id: $id})
            SET o.name = $name,
                o.superclass = $superclass,
                o.superclass_name = $superclass_name,
                o.description = $description,
                o.properties = $properties
            WITH o
            MATCH (c:Concept {id: $concept_id})
            MERGE (c)-[:INSTANCE_OF]->(o)
        """, id=concept_id, name=concept_name, superclass=superclass, superclass_name=superclass_name,
            description=description, properties=properties, concept_id=concept_id)

def create_relationships(session, concept_data):
    """Create relationships between nodes."""
    concept_id = concept_data["concept"]
    
    # Create PREREQUISITE_FOR relationships (rules_if -> rules_then)
    for rule_id in concept_data.get("rules_if", []):
        session.run("""
            MATCH (c:Concept {id: $concept_id})
            MATCH (r:Rule {id: $rule_id})
            MERGE (r)-[:SUPPORTS_RULE]->(c)
        """, concept_id=concept_id, rule_id=rule_id)
    
    for rule_id in concept_data.get("rules_then", []):
        session.run("""
            MATCH (c:Concept {id: $concept_id})
            MATCH (r:Rule {id: $rule_id})
            MERGE (c)-[:SUPPORTS_RULE]->(r)
        """, concept_id=concept_id, rule_id=rule_id)
    
    # Create relationships between concepts based on related_concepts
    for related_concept in concept_data.get("related_concepts", []):
        session.run("""
            MATCH (c1:Concept {id: $concept_id})
            MATCH (c2:Concept {id: $related_id})
            MERGE (c1)-[:RELATED_TO]->(c2)
        """, concept_id=concept_id, related_id=related_concept)
    
    # If concept is from ontology, create superclass relationship
    if concept_data["from_ontology"] and "ontology_data" in concept_data:
        superclass = concept_data["ontology_data"].get("superclass", "")
        if superclass:
            session.run("""
                MATCH (c1:Concept {id: $concept_id})
                MATCH (c2:Concept {id: $superclass_id})
                MERGE (c1)-[:SUBCLASS_OF]->(c2)
            """, concept_id=concept_id, superclass_id=superclass)

def main():
    print("🚀 Starting conversion of improved_graph.jsonl to Neo4j knowledge graph...")
    print(f"   Using Neo4j at {URI}")
    create_knowledge_graph()
    print("✨ Conversion complete! You can access the Neo4j browser at:")
    print("   http://localhost:7474")
    print("   Username: neo4j")
    print("   Password: password")

if __name__ == "__main__":
    main() 