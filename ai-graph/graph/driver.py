"""Thread-safe Neo4j driver connection manager with connection pooling and graceful teardown."""
from typing import Any, Dict, List, Optional
import neo4j
from neo4j import GraphDatabase, Driver

from core.config import settings
from core.logger import get_logger

logger = get_logger("graph.driver")


class Neo4jDriver:
    """Thread-safe connection pool manager for Neo4j Graph Database."""

    _instance: Optional["Neo4jDriver"] = None

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        max_connection_pool_size: int = 50,
        connection_timeout: float = 5.0,
    ) -> None:
        self.uri = uri or settings.NEO4J_URI
        self.user = user or settings.NEO4J_USER
        self.password = password or settings.NEO4J_PASSWORD
        self.database = database or settings.NEO4J_DATABASE

        self._driver: Optional[Driver] = None
        self._max_pool = max_connection_pool_size
        self._conn_timeout = connection_timeout
        self._initialize_driver()

    def _initialize_driver(self) -> None:
        """Create underlying Neo4j driver connection pool."""
        try:
            auth = (self.user, self.password) if self.user and self.password else None
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=auth,
                max_connection_pool_size=self._max_pool,
                connection_timeout=self._conn_timeout,
            )
            logger.info(f"Initialized Neo4j driver connection pool to {self.uri}")
        except Exception as exc:
            logger.warning(f"Neo4j driver pool initialization warning: {exc}")
            self._driver = None

    def verify_connectivity(self) -> bool:
        """Verify database reachability and authentication on startup."""
        if self._driver is None:
            return False
        try:
            self._driver.verify_connectivity()
            logger.info("Successfully verified Neo4j connectivity")
            return True
        except Exception as exc:
            logger.warning(f"Neo4j connectivity verification failed: {exc}")
            return False

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a parameterized Cypher statement against the database."""
        if self._driver is None:
            raise ConnectionError("Neo4j driver is not connected")

        db = database or self.database
        params = parameters or {}

        try:
            records, summary, keys = self._driver.execute_query(
                query,
                parameters_=params,
                database_=db,
            )
            return [record.data() for record in records]
        except Exception as exc:
            logger.error(
                f"Cypher query execution error: {exc}",
                extra={"query": query, "params": params},
            )
            raise

    def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a parameterized Cypher write transaction."""
        return self.execute_query(query, parameters=parameters, database=database)

    def close(self) -> None:
        """Cleanly close connection pools."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None
            logger.info("Closed Neo4j driver connection pool")

    def __enter__(self) -> "Neo4jDriver":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


_global_driver: Optional[Neo4jDriver] = None


def get_neo4j_driver() -> Neo4jDriver:
    """Return or initialize global singleton Neo4j driver instance."""
    global _global_driver
    if _global_driver is None or _global_driver._driver is None:
        _global_driver = Neo4jDriver()
    return _global_driver
