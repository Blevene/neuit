"""
Unit tests for Neo4j Integration
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from backend.neo4j_integration import (
    Neo4jConfig,
    Neo4jConnector,
    create_neo4j_connector,
    NEO4J_AVAILABLE
)


class TestNeo4jConfig:
    """Tests for Neo4jConfig dataclass"""

    def test_neo4j_config_creation(self):
        """Test creating Neo4j configuration"""
        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="test-password",
            database="neo4j"
        )

        assert config.uri == "bolt://localhost:7687"
        assert config.username == "neo4j"
        assert config.password == "test-password"
        assert config.database == "neo4j"

    def test_neo4j_config_defaults(self):
        """Test Neo4j configuration with defaults"""
        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )

        assert config.database == "neo4j"
        assert config.max_connection_lifetime == 3600


@pytest.mark.skipif(not NEO4J_AVAILABLE, reason="neo4j package not installed")
class TestNeo4jConnector:
    """Tests for Neo4jConnector"""

    @patch('backend.neo4j_integration.GraphDatabase')
    def test_connect(self, mock_graph_db):
        """Test connecting to Neo4j"""
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver

        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )
        connector = Neo4jConnector(config)
        connector.connect()

        assert connector._connected is True
        mock_driver.verify_connectivity.assert_called_once()

    @patch('backend.neo4j_integration.GraphDatabase')
    def test_close(self, mock_graph_db):
        """Test closing Neo4j connection"""
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver

        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )
        connector = Neo4jConnector(config)
        connector.connect()
        connector.close()

        assert connector._connected is False
        mock_driver.close.assert_called_once()

    @patch('backend.neo4j_integration.GraphDatabase')
    def test_context_manager(self, mock_graph_db):
        """Test using connector as context manager"""
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver

        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )

        with Neo4jConnector(config) as connector:
            assert connector._connected is True

        mock_driver.close.assert_called_once()

    @patch('backend.neo4j_integration.GraphDatabase')
    def test_execute_query(self, mock_graph_db):
        """Test executing a Cypher query"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = MagicMock()

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result
        mock_result.__iter__.return_value = [{"name": "test"}]

        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )
        connector = Neo4jConnector(config)
        connector.connect()

        results = connector.execute_query("MATCH (n) RETURN n")

        assert len(results) == 1
        assert results[0]["name"] == "test"
        mock_session.run.assert_called_once()

    @patch('backend.neo4j_integration.GraphDatabase')
    def test_create_schema_constraints(self, mock_graph_db):
        """Test creating schema constraints"""
        mock_driver = MagicMock()
        mock_session = MagicMock()

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session

        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )
        connector = Neo4jConnector(config)
        connector.connect()
        connector.create_schema_constraints()

        # Should have called run multiple times for different constraints
        assert mock_session.run.call_count > 0
        assert connector._schema_created is True

    @patch('backend.neo4j_integration.GraphDatabase')
    def test_import_entities(self, mock_graph_db, sample_entities):
        """Test importing entities"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = MagicMock()

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result
        mock_result.__iter__.return_value = [{"created": 3}]

        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )
        connector = Neo4jConnector(config)
        connector.connect()

        count = connector.import_entities(sample_entities, "test.pdf")

        assert count == 3
        mock_session.run.assert_called()

    @patch('backend.neo4j_integration.GraphDatabase')
    def test_import_relationships(self, mock_graph_db, sample_relationships):
        """Test importing relationships"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = MagicMock()

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result
        mock_result.__iter__.return_value = [{"created": 2}]

        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )
        connector = Neo4jConnector(config)
        connector.connect()

        count = connector.import_relationships(sample_relationships, "test.pdf")

        assert count == 2
        mock_session.run.assert_called()

    @patch('backend.neo4j_integration.GraphDatabase')
    def test_import_rules(self, mock_graph_db, sample_rules):
        """Test importing rules"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = MagicMock()

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result
        mock_result.__iter__.return_value = [{"created": 2}]

        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )
        connector = Neo4jConnector(config)
        connector.connect()

        count = connector.import_rules(sample_rules, "test.pdf")

        assert count == 2
        mock_session.run.assert_called()

    @patch('backend.neo4j_integration.GraphDatabase')
    def test_import_knowledge_graph(self, mock_graph_db, sample_entities, sample_relationships, sample_rules):
        """Test importing complete knowledge graph"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = MagicMock()

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result
        mock_result.__iter__.return_value = [{"created": 1}]

        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )
        connector = Neo4jConnector(config)
        connector.connect()

        stats = connector.import_knowledge_graph(
            entities=sample_entities,
            relationships=sample_relationships,
            rules=sample_rules,
            document_name="test.pdf"
        )

        assert 'entities' in stats
        assert 'relationships' in stats
        assert 'rules' in stats
        assert stats['entities'] > 0

    @patch('backend.neo4j_integration.GraphDatabase')
    def test_validate_graph_schema(self, mock_graph_db):
        """Test validating graph schema"""
        mock_driver = MagicMock()
        mock_session = MagicMock()

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session

        # Mock different query results
        def run_side_effect(query, *args):
            mock_result = MagicMock()
            if "SHOW CONSTRAINTS" in query:
                mock_result.__iter__.return_value = [{"name": "constraint1"}]
            elif "SHOW INDEXES" in query:
                mock_result.__iter__.return_value = [{"name": "index1"}]
            elif "db.labels()" in query:
                mock_result.__iter__.return_value = [{"label": "Entity"}]
            elif "db.relationshipTypes()" in query:
                mock_result.__iter__.return_value = [{"relationshipType": "RELATES_TO"}]
            elif "count(n)" in query:
                mock_result.__iter__.return_value = [{"count": 100}]
            elif "count(r)" in query:
                mock_result.__iter__.return_value = [{"count": 50}]
            else:
                mock_result.__iter__.return_value = []
            return mock_result

        mock_session.run.side_effect = run_side_effect

        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )
        connector = Neo4jConnector(config)
        connector.connect()

        validation = connector.validate_graph_schema()

        assert 'constraints' in validation
        assert 'indexes' in validation
        assert 'node_labels' in validation
        assert 'relationship_types' in validation
        assert validation['node_count'] == 100
        assert validation['relationship_count'] == 50

    @patch('backend.neo4j_integration.GraphDatabase')
    def test_query_knowledge(self, mock_graph_db):
        """Test querying knowledge graph"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = MagicMock()

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result
        mock_result.__iter__.return_value = [
            {
                "entity": "Mitochondria",
                "category": "Organelle",
                "aliases": ["Powerhouse"],
                "relationships": []
            }
        ]

        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )
        connector = Neo4jConnector(config)
        connector.connect()

        results = connector.query_knowledge(entity_name="Mitochondria")

        assert len(results) == 1
        assert results[0]["entity"] == "Mitochondria"

    @patch('backend.neo4j_integration.GraphDatabase')
    def test_clear_database(self, mock_graph_db):
        """Test clearing database"""
        mock_driver = MagicMock()
        mock_session = MagicMock()

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session

        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )
        connector = Neo4jConnector(config)
        connector.connect()

        # Should not clear without confirmation
        connector.clear_database(confirm=False)
        mock_session.run.assert_not_called()

        # Should clear with confirmation
        connector.clear_database(confirm=True)
        mock_session.run.assert_called_once()

    @patch('backend.neo4j_integration.GraphDatabase')
    def test_load_config_from_env(self, mock_graph_db, monkeypatch):
        """Test loading configuration from environment"""
        monkeypatch.setenv("NEO4J_URI", "bolt://testhost:7687")
        monkeypatch.setenv("NEO4J_USERNAME", "testuser")
        monkeypatch.setenv("NEO4J_PASSWORD", "testpass")
        monkeypatch.setenv("NEO4J_DATABASE", "testdb")

        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver

        connector = Neo4jConnector()

        assert connector.config.uri == "bolt://testhost:7687"
        assert connector.config.username == "testuser"
        assert connector.config.password == "testpass"
        assert connector.config.database == "testdb"


class TestNeo4jFactory:
    """Tests for Neo4j connector factory"""

    @patch('backend.neo4j_integration.NEO4J_AVAILABLE', True)
    @patch('backend.neo4j_integration.Neo4jConnector')
    def test_create_neo4j_connector_success(self, mock_connector_class):
        """Test successful connector creation"""
        mock_connector = MagicMock()
        mock_connector_class.return_value = mock_connector

        connector = create_neo4j_connector()

        assert connector is not None
        mock_connector_class.assert_called_once()

    @patch('backend.neo4j_integration.NEO4J_AVAILABLE', False)
    def test_create_neo4j_connector_not_available(self):
        """Test connector creation when Neo4j not available"""
        connector = create_neo4j_connector()

        assert connector is None

    @patch('backend.neo4j_integration.NEO4J_AVAILABLE', True)
    @patch('backend.neo4j_integration.Neo4jConnector')
    def test_create_neo4j_connector_with_config(self, mock_connector_class):
        """Test connector creation with custom config"""
        config = Neo4jConfig(
            uri="bolt://custom:7687",
            username="custom",
            password="custom"
        )

        connector = create_neo4j_connector(config)

        mock_connector_class.assert_called_once_with(config)

    @patch('backend.neo4j_integration.NEO4J_AVAILABLE', True)
    @patch('backend.neo4j_integration.Neo4jConnector')
    def test_create_neo4j_connector_error(self, mock_connector_class):
        """Test connector creation with error"""
        mock_connector_class.side_effect = Exception("Connection error")

        connector = create_neo4j_connector()

        assert connector is None
