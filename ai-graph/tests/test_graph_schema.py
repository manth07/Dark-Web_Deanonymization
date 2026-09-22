"""Unit tests for Neo4j driver connection management and schema constraints."""
from unittest.mock import MagicMock
import pytest

from graph.driver import Neo4jDriver
from graph.schema import SCHEMA_CONSTRAINTS, SCHEMA_INDEXES, init_schema


def test_schema_constraints_and_indexes_syntax():
    """Verify constraint and index DDL strings conform to Neo4j 5+ specifications."""
    assert len(SCHEMA_CONSTRAINTS) == 6
    assert len(SCHEMA_INDEXES) == 3

    # All DDLs must be idempotent
    for stmt in SCHEMA_CONSTRAINTS:
        assert "IF NOT EXISTS" in stmt
        assert "CREATE CONSTRAINT" in stmt

    for stmt in SCHEMA_INDEXES:
        assert "IF NOT EXISTS" in stmt
        assert "CREATE INDEX" in stmt

    # Verify key labels
    combined = " ".join(SCHEMA_CONSTRAINTS)
    assert ":ThreatActor" in combined
    assert ":Persona" in combined
    assert ":CryptoWallet" in combined
    assert ":PGPKey" in combined
    assert ":IPAddress" in combined
    assert ":Post" in combined


def test_init_schema_idempotency_with_mock_driver():
    """Verify init_schema executes all statements and handles idempotency without raising errors."""
    mock_driver = MagicMock(spec=Neo4jDriver)
    mock_driver.verify_connectivity.return_value = True

    # 1. First execution
    statements_first_run = init_schema(driver=mock_driver)
    assert len(statements_first_run) == len(SCHEMA_CONSTRAINTS) + len(SCHEMA_INDEXES)
    assert mock_driver.execute_write.call_count == len(SCHEMA_CONSTRAINTS) + len(SCHEMA_INDEXES)

    # 2. Second execution (simulating existing constraints, zero duplicate errors)
    mock_driver.execute_write.side_effect = Exception("An equivalent constraint already exists")
    statements_second_run = init_schema(driver=mock_driver)
    assert len(statements_second_run) == len(SCHEMA_CONSTRAINTS) + len(SCHEMA_INDEXES)


def test_init_schema_offline_graceful_handling():
    """Verify init_schema returns statements safely when database connectivity is offline."""
    mock_driver = MagicMock(spec=Neo4jDriver)
    mock_driver.verify_connectivity.return_value = False

    statements = init_schema(driver=mock_driver)
    assert len(statements) == len(SCHEMA_CONSTRAINTS) + len(SCHEMA_INDEXES)
    # execute_write should not be called if connectivity check fails
    mock_driver.execute_write.assert_not_called()


def test_neo4j_driver_lifecycle():
    """Verify Neo4jDriver initializes with custom parameters and closes cleanly."""
    driver = Neo4jDriver(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="testpassword",
        database="neo4j",
    )
    assert driver.uri == "bolt://localhost:7687"
    assert driver.user == "neo4j"
    assert driver.database == "neo4j"

    # Context manager lifecycle
    with driver as d:
        assert d is not None

    # Driver should be closed after exiting context manager
    assert driver._driver is None
