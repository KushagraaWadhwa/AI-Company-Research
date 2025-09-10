"""
Embeddings utilities for vector generation using Ollama.
"""

import logging
from typing import List, Optional
from langchain_ollama import OllamaEmbeddings

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global embeddings instance
_embeddings_model: Optional[OllamaEmbeddings] = None


def get_embeddings_model() -> OllamaEmbeddings:
    """
    Get or create an Ollama embeddings model instance.
    
    Returns:
        OllamaEmbeddings: The embeddings model
    """
    global _embeddings_model
    
    if _embeddings_model is None:
        try:
            _embeddings_model = OllamaEmbeddings(
                model=settings.EMBEDDING_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                # Additional configuration for better performance
                num_ctx=2048,  # Context window
                num_thread=4,  # Number of threads
            )
            
            logger.info(f"✅ Embeddings model initialized: {settings.EMBEDDING_MODEL}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize embeddings model: {e}")
            raise
    
    return _embeddings_model


def generate_embedding(text: str) -> List[float]:
    """
    Generate embeddings for a single text.
    
    Args:
        text: The text to embed
        
    Returns:
        List[float]: The embedding vector
    """
    try:
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return []
        
        # Get the embeddings model
        embeddings_model = get_embeddings_model()
        
        # Generate embedding
        logger.info(f"Generating embedding for text ({len(text)} characters)")
        embedding = embeddings_model.embed_query(text)
        
        logger.info(f"✅ Generated embedding vector of dimension {len(embedding)}")
        return embedding
        
    except Exception as e:
        logger.error(f"❌ Failed to generate embedding: {e}")
        raise


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in batch.
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List[List[float]]: List of embedding vectors
    """
    try:
        if not texts:
            logger.warning("Empty text list provided for batch embedding")
            return []
        
        # Filter out empty texts
        valid_texts = [text for text in texts if text and text.strip()]
        
        if not valid_texts:
            logger.warning("No valid texts found for batch embedding")
            return []
        
        # Get the embeddings model
        embeddings_model = get_embeddings_model()
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(valid_texts)} texts")
        embeddings = embeddings_model.embed_documents(valid_texts)
        
        logger.info(f"✅ Generated {len(embeddings)} embedding vectors")
        return embeddings
        
    except Exception as e:
        logger.error(f"❌ Failed to generate batch embeddings: {e}")
        raise


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        float: Cosine similarity score (0 to 1)
    """
    try:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            logger.warning("Invalid vectors for cosine similarity calculation")
            return 0.0
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Calculate magnitudes
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        # Avoid division by zero
        if magnitude1 == 0.0 or magnitude2 == 0.0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)
        
        # Ensure result is between 0 and 1
        return max(0.0, min(1.0, similarity))
        
    except Exception as e:
        logger.error(f"❌ Failed to calculate cosine similarity: {e}")
        return 0.0


async def test_embeddings_connection() -> dict:
    """
    Test the embeddings model connection.
    
    Returns:
        dict: Test result
    """
    try:
        # Test with a simple text
        test_text = "This is a test for the embeddings model."
        embedding = generate_embedding(test_text)
        
        return {
            "status": "healthy",
            "model": settings.EMBEDDING_MODEL,
            "base_url": settings.OLLAMA_BASE_URL,
            "test_embedding_dimension": len(embedding),
            "test_text_length": len(test_text)
        }
        
    except Exception as e:
        logger.error(f"Embeddings connection test failed: {e}")
        return {
            "status": "unhealthy",
            "model": settings.EMBEDDING_MODEL,
            "base_url": settings.OLLAMA_BASE_URL,
            "error": str(e)
        }
