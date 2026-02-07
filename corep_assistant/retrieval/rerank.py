"""Reranker stub interface (optional enhancement)"""
from typing import List
from corep_assistant.schemas import EvidenceChunk


class Reranker:
    """Stub interface for reranking retrieved chunks"""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize reranker.
        
        Future implementation would load a cross-encoder model.
        
        Args:
            model_name: HuggingFace cross-encoder model name
        """
        self.model_name = model_name
        print(f"Reranker stub initialized (model: {model_name})")
    
    def rerank(
        self,
        query: str,
        evidence: List[EvidenceChunk],
        top_k: int = 6
    ) -> List[EvidenceChunk]:
        """
        Rerank evidence chunks.
        
        Future implementation would:
        - Use cross-encoder to score (query, chunk) pairs
        - Re-sort by cross-encoder scores
        - Return top-k
        
        Args:
            query: Query string
            evidence: List of evidence chunks
            top_k: Number of top results to return
            
        Returns:
            Reranked evidence (currently returns input unchanged)
        """
        print(f"Reranker stub: returning {len(evidence)} chunks unchanged")
        return evidence[:top_k]


def get_reranker() -> Reranker:
    """Get reranker instance"""
    return Reranker()
