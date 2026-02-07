"""FAISS index builder and searcher"""
import faiss
import numpy as np
from pathlib import Path
from typing import List, Tuple
from corep_assistant.schemas import Chunk
from .embeddings import get_embedder


class FAISSIndex:
    """FAISS vector index for semantic search"""
    
    def __init__(self):
        self.index = None
        self.chunk_ids = []  # Parallel array: index position -> chunk_id
        self.dimension = None
    
    def build(self, chunks: List[Chunk]) -> None:
        """
        Build FAISS index from chunks.
        
        Args:
            chunks: List of chunks to index
        """
        if not chunks:
            print("ERROR: No chunks to index")
            return
        
        print(f"Building FAISS index for {len(chunks)} chunks...")
        
        # Get embedder
        embedder = get_embedder()
        self.dimension = embedder.dimension
        
        # Extract texts
        texts = [chunk.text for chunk in chunks]
        
        # Embed all texts
        embeddings = embedder.embed_texts(texts)
        
        # Build index (L2 distance)
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings.astype('float32'))
        
        # Store chunk IDs
        self.chunk_ids = [chunk.metadata.chunk_id for chunk in chunks]
        
        print(f"FAISS index built with {self.index.ntotal} vectors")
    
    def search(self, query: str, k: int = 10) -> List[Tuple[str, float]]:
        """
        Search index for query.
        
        Args:
            query: Query string
            k: Number of results to return
            
        Returns:
            List of (chunk_id, distance) tuples
        """
        if self.index is None:
            print("ERROR: Index not loaded")
            return []
        
        # Embed query
        embedder = get_embedder()
        query_embedding = embedder.embed_query(query)
        
        # Search
        distances, indices = self.index.search(
            query_embedding.reshape(1, -1).astype('float32'),
            k
        )
        
        # Convert to results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.chunk_ids):
                # Convert L2 distance to similarity score (inverse)
                # Normalize to 0-1 range approximately
                similarity = 1.0 / (1.0 + dist)
                results.append((self.chunk_ids[idx], float(similarity)))
        
        return results
    
    def save(self, index_path: Path, metadata_path: Path) -> None:
        """
        Save index to disk.
        
        Args:
            index_path: Path to save FAISS index
            metadata_path: Path to save chunk ID mapping (text file)
        """
        if self.index is None:
            print("ERROR: No index to save")
            return
        
        # Save FAISS index
        faiss.write_index(self.index, str(index_path))
        
        # Save chunk IDs mapping
        with open(metadata_path, 'w') as f:
            for chunk_id in self.chunk_ids:
                f.write(chunk_id + '\n')
        
        print(f"FAISS index saved to: {index_path}")
    
    def load(self, index_path: Path, metadata_path: Path) -> None:
        """
        Load index from disk.
        
        Args:
            index_path: Path to FAISS index
            metadata_path: Path to chunk ID mapping
        """
        # Load FAISS index
        self.index = faiss.read_index(str(index_path))
        self.dimension = self.index.d
        
        # Load chunk IDs
        with open(metadata_path, 'r') as f:
            self.chunk_ids = [line.strip() for line in f]
        
        print(f"FAISS index loaded: {self.index.ntotal} vectors, dim={self.dimension}")


def build_faiss_index(chunks: List[Chunk], output_path: Path) -> FAISSIndex:
    """
    Build and save FAISS index.
    
    Args:
        chunks: List of chunks
        output_path: Path to save index
        
    Returns:
        Built FAISSIndex
    """
    index = FAISSIndex()
    index.build(chunks)
    
    # Save with metadata
    metadata_path = output_path.with_suffix('.txt')
    index.save(output_path, metadata_path)
    
    return index


def load_faiss_index(index_path: Path) -> FAISSIndex:
    """
    Load FAISS index from disk.
    
    Args:
        index_path: Path to index file
        
    Returns:
        Loaded FAISSIndex
    """
    metadata_path = index_path.with_suffix('.txt')
    
    index = FAISSIndex()
    index.load(index_path, metadata_path)
    
    return index
