"""
Digital FTE Customer Success Agent - Knowledge Base Pydantic Models
Knowledge base entry models with pgvector embedding support
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class KnowledgeBaseEntryBase(BaseModel):
    """Base knowledge base entry model with common fields."""
    title: str = Field(..., max_length=500, description="Entry title")
    content: str = Field(..., description="Entry content (product documentation)")
    category: Optional[str] = Field(None, max_length=100, description="Entry category")
    source_url: Optional[str] = Field(None, max_length=500, description="Source URL")


class KnowledgeBaseEntryCreate(KnowledgeBaseEntryBase):
    """Model for creating a new knowledge base entry (without embedding)."""
    pass


class KnowledgeBaseEntryWithEmbedding(KnowledgeBaseEntryBase):
    """Model for creating a knowledge base entry with embedding."""
    embedding: List[float] = Field(..., description="OpenAI embedding vector (1536 dimensions)")

    @property
    def embedding_dimension(self) -> int:
        """Get embedding dimension."""
        return len(self.embedding)


class KnowledgeBaseEntry(KnowledgeBaseEntryBase):
    """Complete knowledge base entry model with database fields."""
    entry_id: UUID
    # Note: embedding field is not included in responses by default (large vector)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeBaseEntryWithScore(KnowledgeBaseEntry):
    """
    Knowledge base entry with similarity score.
    Used for search results from pgvector similarity queries.
    """
    similarity_score: float = Field(..., description="Cosine similarity score (0-1, higher is better)")


class KnowledgeBaseSearchResult(BaseModel):
    """
    Search result from knowledge base query.
    Contains relevant entries sorted by similarity.
    """
    query: str = Field(..., description="Original search query")
    results: List[KnowledgeBaseEntryWithScore] = Field(default_factory=list, description="Search results")
    total_results: int = Field(..., description="Total number of results")

    @property
    def has_results(self) -> bool:
        """Check if search returned any results."""
        return len(self.results) > 0

    @property
    def best_match(self) -> Optional[KnowledgeBaseEntryWithScore]:
        """Get the best matching result."""
        return self.results[0] if self.has_results else None
