"""
Neo4j Integration Module
Provides direct graph database writes, Cypher query interface, and schema validation
"""

import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import os

try:
    from neo4j import GraphDatabase, basic_auth
    from neo4j.exceptions import ServiceUnavailable, AuthError
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("neo4j package not installed. Install with: pip install neo4j")

logger = logging.getLogger(__name__)


@dataclass
class Neo4jConfig:
    """Configuration for Neo4j connection"""
    uri: str
    username: str
    password: str
    database: str = "neo4j"
    max_connection_lifetime: int = 3600
    max_connection_pool_size: int = 50
    connection_timeout: int = 30


class Neo4jConnector:
    """Neo4j database connector with schema validation and query interface"""

    def __init__(self, config: Optional[Neo4jConfig] = None):
        """
        Initialize Neo4j connector

        Args:
            config: Neo4j configuration. If None, loads from environment variables
        """
        if not NEO4J_AVAILABLE:
            raise ImportError("neo4j package is required. Install with: pip install neo4j")

        self.config = config or self._load_config_from_env()
        self.driver = None
        self._connected = False
        self._schema_created = False

    @staticmethod
    def _load_config_from_env() -> Neo4jConfig:
        """Load Neo4j configuration from environment variables"""
        return Neo4jConfig(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            username=os.getenv("NEO4J_USERNAME", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password"),
            database=os.getenv("NEO4J_DATABASE", "neo4j")
        )

    def connect(self):
        """Establish connection to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=basic_auth(self.config.username, self.config.password),
                max_connection_lifetime=self.config.max_connection_lifetime,
                max_connection_pool_size=self.config.max_connection_pool_size,
                connection_timeout=self.config.connection_timeout
            )
            # Verify connectivity
            self.driver.verify_connectivity()
            self._connected = True
            logger.info(f"Connected to Neo4j at {self.config.uri}")
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            self._connected = False
            logger.info("Neo4j connection closed")

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        if not self._connected:
            self.connect()

        parameters = parameters or {}
        results = []

        with self.driver.session(database=self.config.database) as session:
            try:
                result = session.run(query, parameters)
                results = [dict(record) for record in result]
                logger.info(f"Query executed successfully. Returned {len(results)} records.")
            except Exception as e:
                logger.error(f"Query execution failed: {e}\nQuery: {query}")
                raise

        return results

    def create_schema_constraints(self):
        """Create indexes and constraints for optimal performance"""
        if not self._connected:
            self.connect()

        constraints = [
            # Entity constraints
            "CREATE CONSTRAINT entity_name_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
            "CREATE INDEX entity_category IF NOT EXISTS FOR (e:Entity) ON (e.category)",

            # Concept constraints (alias for Entity)
            "CREATE CONSTRAINT concept_name_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE",
            "CREATE INDEX concept_category IF NOT EXISTS FOR (c:Concept) ON (c.category)",

            # Document tracking
            "CREATE INDEX document_filename IF NOT EXISTS FOR (d:Document) ON (d.filename)",
        ]

        with self.driver.session(database=self.config.database) as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"Schema constraint created: {constraint[:50]}...")
                except Exception as e:
                    # Constraint might already exist
                    logger.debug(f"Schema constraint skipped: {e}")

        self._schema_created = True
        logger.info("Neo4j schema constraints created successfully")

    def clear_database(self, confirm: bool = False):
        """
        Clear all nodes and relationships from the database

        Args:
            confirm: Must be True to actually clear the database (safety check)
        """
        if not confirm:
            logger.warning("Database clear not confirmed. Set confirm=True to clear.")
            return

        if not self._connected:
            self.connect()

        query = "MATCH (n) DETACH DELETE n"
        with self.driver.session(database=self.config.database) as session:
            session.run(query)
            logger.warning("Database cleared!")

    def import_entities(
        self,
        entities: List[Dict[str, Any]],
        document_name: Optional[str] = None
    ) -> int:
        """
        Import entities into Neo4j

        Args:
            entities: List of entity dictionaries
            document_name: Source document name for tracking

        Returns:
            Number of entities created
        """
        if not self._connected:
            self.connect()

        if not self._schema_created:
            self.create_schema_constraints()

        query = """
        UNWIND $entities AS entity
        MERGE (e:Entity {name: entity.name})
        SET e.category = entity.category,
            e.aliases = entity.aliases,
            e.last_updated = datetime()
        WITH e, entity
        WHERE $doc_name IS NOT NULL
        MERGE (d:Document {filename: $doc_name})
        MERGE (e)-[:EXTRACTED_FROM]->(d)
        RETURN count(e) as created
        """

        parameters = {
            "entities": entities,
            "doc_name": document_name
        }

        results = self.execute_query(query, parameters)
        count = results[0]["created"] if results else 0
        logger.info(f"Imported {count} entities to Neo4j")

        return count

    def import_relationships(
        self,
        relationships: List[Dict[str, Any]],
        document_name: Optional[str] = None
    ) -> int:
        """
        Import relationships into Neo4j

        Args:
            relationships: List of relationship dictionaries
            document_name: Source document name for tracking

        Returns:
            Number of relationships created
        """
        if not self._connected:
            self.connect()

        if not self._schema_created:
            self.create_schema_constraints()

        # Neo4j doesn't support dynamic relationship types in MERGE, so we'll use properties
        query = """
        UNWIND $relationships AS rel
        MERGE (subject:Entity {name: rel.subject})
        MERGE (object:Entity {name: rel.object})
        CREATE (subject)-[r:RELATES_TO {
            predicate: rel.predicate,
            justification: rel.justification,
            created: datetime()
        }]->(object)
        WITH r, rel
        WHERE $doc_name IS NOT NULL
        MERGE (d:Document {filename: $doc_name})
        CREATE (r)-[:FROM_DOCUMENT]->(d)
        RETURN count(r) as created
        """

        parameters = {
            "relationships": relationships,
            "doc_name": document_name
        }

        results = self.execute_query(query, parameters)
        count = results[0]["created"] if results else 0
        logger.info(f"Imported {count} relationships to Neo4j")

        return count

    def import_rules(
        self,
        rules: List[Dict[str, Any]],
        document_name: Optional[str] = None
    ) -> int:
        """
        Import logical rules into Neo4j

        Args:
            rules: List of rule dictionaries
            document_name: Source document name for tracking

        Returns:
            Number of rules created
        """
        if not self._connected:
            self.connect()

        query = """
        UNWIND $rules AS rule
        CREATE (r:Rule {
            id: rule.id,
            if_clause: rule.if,
            then_clause: rule.then,
            confidence: rule.confidence,
            created: datetime()
        })
        WITH r, rule
        WHERE $doc_name IS NOT NULL
        MERGE (d:Document {filename: $doc_name})
        CREATE (r)-[:EXTRACTED_FROM]->(d)
        RETURN count(r) as created
        """

        parameters = {
            "rules": rules,
            "doc_name": document_name
        }

        results = self.execute_query(query, parameters)
        count = results[0]["created"] if results else 0
        logger.info(f"Imported {count} rules to Neo4j")

        return count

    def import_knowledge_graph(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        rules: Optional[List[Dict[str, Any]]] = None,
        document_name: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Import complete knowledge graph into Neo4j

        Args:
            entities: List of entities
            relationships: List of relationships
            rules: Optional list of rules
            document_name: Source document name

        Returns:
            Dictionary with counts of imported items
        """
        logger.info(f"Importing knowledge graph for document: {document_name}")

        stats = {
            "entities": self.import_entities(entities, document_name),
            "relationships": self.import_relationships(relationships, document_name),
            "rules": 0
        }

        if rules:
            stats["rules"] = self.import_rules(rules, document_name)

        logger.info(f"Knowledge graph import complete: {stats}")
        return stats

    def validate_graph_schema(self) -> Dict[str, Any]:
        """
        Validate the current graph schema

        Returns:
            Schema validation report
        """
        if not self._connected:
            self.connect()

        validation = {
            "constraints": [],
            "indexes": [],
            "node_labels": [],
            "relationship_types": [],
            "node_count": 0,
            "relationship_count": 0
        }

        # Get constraints
        constraints = self.execute_query("SHOW CONSTRAINTS")
        validation["constraints"] = [c.get("name", "unknown") for c in constraints]

        # Get indexes
        indexes = self.execute_query("SHOW INDEXES")
        validation["indexes"] = [i.get("name", "unknown") for i in indexes]

        # Get node labels
        labels = self.execute_query("CALL db.labels()")
        validation["node_labels"] = [l.get("label", "unknown") for l in labels]

        # Get relationship types
        rel_types = self.execute_query("CALL db.relationshipTypes()")
        validation["relationship_types"] = [r.get("relationshipType", "unknown") for r in rel_types]

        # Get counts
        node_count = self.execute_query("MATCH (n) RETURN count(n) as count")
        validation["node_count"] = node_count[0]["count"] if node_count else 0

        rel_count = self.execute_query("MATCH ()-[r]->() RETURN count(r) as count")
        validation["relationship_count"] = rel_count[0]["count"] if rel_count else 0

        logger.info(f"Graph schema validation: {validation}")
        return validation

    def query_knowledge(
        self,
        entity_name: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query knowledge graph

        Args:
            entity_name: Optional entity name to filter by
            category: Optional category to filter by
            limit: Maximum number of results

        Returns:
            List of matching entities with their relationships
        """
        if not self._connected:
            self.connect()

        query_parts = ["MATCH (e:Entity)"]
        where_clauses = []
        parameters = {"limit": limit}

        if entity_name:
            where_clauses.append("e.name CONTAINS $entity_name")
            parameters["entity_name"] = entity_name

        if category:
            where_clauses.append("e.category = $category")
            parameters["category"] = category

        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))

        query_parts.append("""
        OPTIONAL MATCH (e)-[r:RELATES_TO]->(other:Entity)
        RETURN e.name as entity,
               e.category as category,
               e.aliases as aliases,
               collect({
                   predicate: r.predicate,
                   target: other.name,
                   justification: r.justification
               }) as relationships
        LIMIT $limit
        """)

        query = "\n".join(query_parts)
        results = self.execute_query(query, parameters)

        logger.info(f"Query returned {len(results)} entities")
        return results


def create_neo4j_connector(config: Optional[Neo4jConfig] = None) -> Optional[Neo4jConnector]:
    """
    Factory function to create Neo4j connector

    Args:
        config: Optional Neo4j configuration

    Returns:
        Neo4jConnector instance or None if Neo4j is not available
    """
    if not NEO4J_AVAILABLE:
        logger.warning("Neo4j integration not available. Install neo4j package.")
        return None

    try:
        connector = Neo4jConnector(config)
        return connector
    except Exception as e:
        logger.error(f"Failed to create Neo4j connector: {e}")
        return None
