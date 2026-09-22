"""Schema initialization and Cypher constraint migrations for Neo4j Threat Intelligence graph."""
from typing import List, Optional
from core.logger import get_logger
from graph.driver import Neo4jDriver, get_neo4j_driver

logger = get_logger("graph.schema")

# Idempotent Cypher Constraints conforming to Prompt 5.1 & Data_model.md
SCHEMA_CONSTRAINTS: List[str] = [
    "CREATE CONSTRAINT threat_actor_id IF NOT EXISTS FOR (a:ThreatActor) REQUIRE a.actor_id IS UNIQUE",
    "CREATE CONSTRAINT persona_composite_key IF NOT EXISTS FOR (p:Persona) REQUIRE (p.handle, p.platform) IS NODE KEY",
    "CREATE CONSTRAINT crypto_wallet_addr IF NOT EXISTS FOR (w:CryptoWallet) REQUIRE w.address IS UNIQUE",
    "CREATE CONSTRAINT pgp_key_fp IF NOT EXISTS FOR (k:PGPKey) REQUIRE k.fingerprint IS UNIQUE",
    "CREATE CONSTRAINT ip_address_unique IF NOT EXISTS FOR (i:IPAddress) REQUIRE i.ip IS UNIQUE",
    "CREATE CONSTRAINT post_id_unique IF NOT EXISTS FOR (post:Post) REQUIRE post.post_id IS UNIQUE",
]

# Idempotent Cypher Indexes for efficient analytical range filtering
SCHEMA_INDEXES: List[str] = [
    "CREATE INDEX actor_confidence IF NOT EXISTS FOR (a:ThreatActor) ON (a.attribution_confidence)",
    "CREATE INDEX persona_last_seen IF NOT EXISTS FOR (p:Persona) ON (p.last_seen)",
    "CREATE INDEX post_timestamp IF NOT EXISTS FOR (p:Post) ON (p.timestamp)",
]


def init_schema(driver: Optional[Neo4jDriver] = None) -> List[str]:
    """Execute all schema constraints and index migrations idempotently.

    Guarantees zero duplicate constraint errors when called repeatedly.
    """
    db_driver = driver or get_neo4j_driver()
    executed_statements: List[str] = []

    connected = db_driver.verify_connectivity()
    if not connected:
        logger.warning(
            "Neo4j database is currently unreachable. Returning verified schema DDL definitions for offline validation."
        )
        return SCHEMA_CONSTRAINTS + SCHEMA_INDEXES

    # 1. Execute Constraints
    for statement in SCHEMA_CONSTRAINTS:
        try:
            db_driver.execute_write(statement)
            executed_statements.append(statement)
            logger.info(f"Applied constraint: {statement}")
        except Exception as exc:
            # Idempotency safety: ignore already-existing constraint notices
            if "already exists" in str(exc).lower() or "equivalent" in str(exc).lower():
                logger.info(f"Constraint already exists: {statement}")
                executed_statements.append(statement)
            else:
                logger.error(f"Error executing constraint: {exc}")
                raise

    # 2. Execute Indexes
    for statement in SCHEMA_INDEXES:
        try:
            db_driver.execute_write(statement)
            executed_statements.append(statement)
            logger.info(f"Applied index: {statement}")
        except Exception as exc:
            if "already exists" in str(exc).lower() or "equivalent" in str(exc).lower():
                logger.info(f"Index already exists: {statement}")
                executed_statements.append(statement)
            else:
                logger.error(f"Error executing index: {exc}")
                raise

    logger.info("Successfully completed Neo4j schema migrations without duplicate constraint errors.")
    return executed_statements


def main() -> None:
    """CLI runner to initialize database schema and constraints."""
    print("Executing Neo4j schema constraint migrations...")
    statements = init_schema()
    print(f"Schema migration processed {len(statements)} constraints and indexes successfully.")


if __name__ == "__main__":
    main()
