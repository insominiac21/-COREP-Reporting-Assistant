"""Embeddings wrapper using sentence-transformers"""
from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from corep_assistant.config import EMBED_MODEL_NAME


class Embedder:
    """Wrapper for embedding model"""
    
    def __init__(self, model_name: str = EMBED_MODEL_NAME):
        """
        Initialize embedder.
        
        Args:
            model_name: HuggingFace model name
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"Embedding dimension: {self.dimension}")
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Embed multiple texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            Numpy array of embeddings (n_texts, dimension)
        """
        embeddings = self.model.encode(
            texts,
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True
        )
        return embeddings
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed single query.
        
        Args:
            query: Query string
            
        Returns:
            Numpy array embedding (dimension,)
        """
        return self.model.encode(query, convert_to_numpy=True)


# Global instance
_embedder_instance = None


def get_embedder() -> Embedder:
    """Get global embedder instance (lazy loading)"""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = Embedder()
    return _embedder_instance
