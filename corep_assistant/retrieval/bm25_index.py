"""BM25 index builder and searcher"""
import pickle
from pathlib import Path
from typing import List, Tuple
from rank_bm25 import BM25Okapi
from corep_assistant.schemas import Chunk


class BM25Index:
    """BM25 keyword-based index"""
    
    def __init__(self):
        self.bm25 = None
        self.chunk_ids = []
        self.tokenized_corpus = []
    
    def tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        # Simple whitespace + lowercase tokenization
        # Could be improved with stemming/lemmatization
        tokens = text.lower().split()
        return tokens
    
    def build(self, chunks: List[Chunk]) -> None:
        """
        Build BM25 index from chunks.
        
        Args:
            chunks: List of chunks to index
        """
        if not chunks:
            print("ERROR: No chunks to index")
            return
        
        print(f"Building BM25 index for {len(chunks)} chunks...")
        
        # Tokenize all texts
        self.tokenized_corpus = [self.tokenize(chunk.text) for chunk in chunks]
        
        # Build BM25 index
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        
        # Store chunk IDs
        self.chunk_ids = [chunk.metadata.chunk_id for chunk in chunks]
        
        print(f"BM25 index built with {len(self.tokenized_corpus)} documents")
    
    def search(self, query: str, k: int = 10) -> List[Tuple[str, float]]:
        """
        Search index for query.
        
        Args:
            query: Query string
            k: Number of results to return
            
        Returns:
            List of (chunk_id, score) tuples
        """
        if self.bm25 is None:
            print("ERROR: Index not loaded")
            return []
        
        # Tokenize query
        tokenized_query = self.tokenize(query)
        
        # Get scores
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top-k indices
        top_k_indices = scores.argsort()[-k:][::-1]
        
        # Convert to results
        results = []
        for idx in top_k_indices:
            if idx < len(self.chunk_ids):
                score = float(scores[idx])
                if score > 0:  # Only include non-zero scores
                    results.append((self.chunk_ids[idx], score))
        
        return results
    
    def save(self, output_path: Path) -> None:
        """
        Save index to disk.
        
        Args:
            output_path: Path to save index (pickle file)
        """
        if self.bm25 is None:
            print("ERROR: No index to save")
            return
        
        data = {
            'bm25': self.bm25,
            'chunk_ids': self.chunk_ids,
            'tokenized_corpus': self.tokenized_corpus
        }
        
        with open(output_path, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"BM25 index saved to: {output_path}")
    
    def load(self, index_path: Path) -> None:
        """
        Load index from disk.
        
        Args:
            index_path: Path to index file
        """
        with open(index_path, 'rb') as f:
            data = pickle.load(f)
        
        self.bm25 = data['bm25']
        self.chunk_ids = data['chunk_ids']
        self.tokenized_corpus = data['tokenized_corpus']
        
        print(f"BM25 index loaded: {len(self.chunk_ids)} documents")


def build_bm25_index(chunks: List[Chunk], output_path: Path) -> BM25Index:
    """
    Build and save BM25 index.
    
    Args:
        chunks: List of chunks
        output_path: Path to save index
        
    Returns:
        Built BM25Index
    """
    index = BM25Index()
    index.build(chunks)
    index.save(output_path)
    return index


def load_bm25_index(index_path: Path) -> BM25Index:
    """
    Load BM25 index from disk.
    
    Args:
        index_path: Path to index file
        
    Returns:
        Loaded BM25Index
    """
    index = BM25Index()
    index.load(index_path)
    return index
