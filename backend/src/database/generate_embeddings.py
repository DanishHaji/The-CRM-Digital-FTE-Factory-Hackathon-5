"""
Digital FTE Customer Success Agent - Generate Embeddings
Generate pgvector embeddings for knowledge base entries using OpenAI API
"""

import asyncio
from openai import AsyncOpenAI

from .connection import get_connection
from ..utils.config import get_settings
from ..utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)
settings = get_settings()

# Initialize OpenAI client
client = AsyncOpenAI(api_key=settings.openai_api_key)


async def generate_embedding(text: str) -> list[float]:
    """
    Generate embedding vector for text using OpenAI API.

    Args:
        text: Text to embed

    Returns:
        list[float]: Embedding vector (1536 dimensions for text-embedding-3-small)
    """
    try:
        response = await client.embeddings.create(
            model=settings.openai_embedding_model,
            input=text
        )
        return response.data[0].embedding

    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise


async def generate_all_embeddings():
    """
    Generate embeddings for all knowledge base entries without embeddings.
    """
    logger.info("Starting embedding generation...")

    async with get_connection() as conn:
        # Get all entries without embeddings
        entries = await conn.fetch("""
            SELECT entry_id, title, content
            FROM knowledge_base
            WHERE embedding IS NULL
        """)

        logger.info(f"Found {len(entries)} entries without embeddings")

        for i, entry in enumerate(entries, 1):
            entry_id = entry['entry_id']
            title = entry['title']
            content = entry['content']

            # Combine title and content for embedding
            text = f"{title}\n\n{content}"

            logger.info(f"Generating embedding {i}/{len(entries)}: {title[:50]}...")

            try:
                # Generate embedding
                embedding = await generate_embedding(text)

                # Update database with embedding
                await conn.execute("""
                    UPDATE knowledge_base
                    SET embedding = $1
                    WHERE entry_id = $2
                """, embedding, entry_id)

                logger.info(f"✓ Updated entry {i}/{len(entries)}")

            except Exception as e:
                logger.error(f"✗ Failed to process entry {entry_id}: {e}")
                continue

    logger.info("Embedding generation completed successfully!")


async def test_vector_search(query: str, top_k: int = 3):
    """
    Test vector similarity search with a query.

    Args:
        query: Search query
        top_k: Number of results to return
    """
    logger.info(f"Testing vector search: '{query}'")

    # Generate query embedding
    query_embedding = await generate_embedding(query)

    async with get_connection() as conn:
        # Perform vector similarity search using cosine distance
        results = await conn.fetch("""
            SELECT
                title,
                content,
                category,
                1 - (embedding <=> $1::vector) AS similarity
            FROM knowledge_base
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> $1::vector
            LIMIT $2
        """, query_embedding, top_k)

        logger.info(f"Found {len(results)} results:")

        for i, result in enumerate(results, 1):
            logger.info(
                f"{i}. {result['title']} (similarity: {result['similarity']:.3f})",
                category=result['category']
            )
            logger.info(f"   {result['content'][:100]}...")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test mode: run a sample search
        query = sys.argv[2] if len(sys.argv) > 2 else "How do I contact support?"
        asyncio.run(test_vector_search(query))
    else:
        # Normal mode: generate all embeddings
        asyncio.run(generate_all_embeddings())
