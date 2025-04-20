# Knowledge Graph Generator

This tool converts the JSON lines data from `improved_graph.jsonl` into a Neo4j knowledge graph that follows the schema design specified in `schema_design.md`.

## Requirements

- Docker and Docker Compose

That's it! All other dependencies are managed within the Docker containers.

## Setup & Usage

### Option 1: Full Docker Setup (Recommended)

The easiest way to run the complete application is using our Docker setup, which includes:
- Neo4j database container
- Streamlit frontend container
- Automatic data import

Simply run:

**Windows:**
```
docker-run.bat
```

**Linux/Mac:**
```
chmod +x docker-run.sh
./docker-run.sh
```

This will:
1. Build and start all necessary containers
2. Check if Neo4j is running properly
3. Import the data if needed
4. Provide URLs to access the applications

**Access the applications:**
- Neo4j Browser: http://localhost:7474 (username: neo4j, password: password)
- Knowledge Graph Explorer: http://localhost:8501

### Option 2: Manual Setup

If you prefer to run components separately, you can still do so.

#### 1. Install Python Dependencies

```
pip install -r requirements.txt
```

#### 2. Setup Neo4j with Docker

```
cd prototype
docker compose up -d neo4j
```

#### 3. Run the Graph Import Script

```
python graph_to_neo4j.py
```

#### 4. Start the Streamlit Frontend

**Windows:**
```
run_explorer.bat
```

**Linux/Mac:**
```
chmod +x run_explorer.sh
./run_explorer.sh
```

## Knowledge Graph Explorer Features

The frontend provides several ways to interact with your knowledge graph:

- **Overview**: Get statistics and a high-level visualization of the graph
- **Concept Explorer**: Browse individual concepts, their labels, and relationships
- **Relationship Visualizer**: Explore connections between multiple concepts
- **Rule Browser**: View educational rules and their related concepts
- **Search**: Find concepts and relationships by keyword

## Schema Design

The knowledge graph follows this schema:

### Node Types
- **Concept**: Core concepts from the JSONL file
- **Label**: Text descriptions with type and justification
- **Rule**: Educational rules with if-then logic
- **OntologyClass**: Class definitions for concepts from an ontology

### Relationships
- **HAS_LABEL**: Links a concept to its labels
- **SUPPORTS_RULE**: Connects concepts to rules they support
- **RELATED_TO**: Links related concepts together
- **SUBCLASS_OF**: Shows hierarchical relationships between concepts
- **INSTANCE_OF**: Links concepts to their ontology class definitions

## Example Queries

You can run these queries in the Neo4j Browser:

```cypher
// Get all concepts with their labels
MATCH (c:Concept)-[:HAS_LABEL]->(l:Label)
RETURN c.name, l.text, l.type;

// Find concepts related to "neuron"
MATCH (c1:Concept {name: "Neuron"})-[:RELATED_TO]->(c2:Concept)
RETURN c2.name;

// Find prerequisite relationships through rules
MATCH (c1:Concept)-[:SUPPORTS_RULE]->(r:Rule)-[:SUPPORTS_RULE]->(c2:Concept)
RETURN c1.name, r.if_text, r.then_text, c2.name;
```

## Shutting Down

To stop all containers:

```
docker compose down
```

To remove all data volumes as well:

```
docker compose down -v
``` 