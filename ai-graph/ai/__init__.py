"""AI services layer for local Ollama embeddings, stylometric profiling, and entity resolution."""
from ai.ollama_client import OllamaStylometryService
from ai.entity_resolution import EntityResolver, LinkageDecision

__all__ = ["OllamaStylometryService", "EntityResolver", "LinkageDecision"]
