"""Hybrid retrieval combining FAISS and BM25"""
from typing import List, Dict, Optional
from collections import defaultdict
from corep_assistant.schemas import Chunk, EvidenceChunk
from .faiss_index import FAISSIndex
from .bm25_index import BM25Index


def normalize_scores(scores: List[float]) -> List[float]:
    """
    Normalize scores to [0, 1] range.
    
    Args:
        scores: List of scores
        
    Returns:
        Normalized scores
    """
    if not scores:
        return []
    
    min_score = min(scores)
    max_score = max(scores)
    
    if max_score == min_score:
        return [1.0] * len(scores)
    
    return [(s - min_score) / (max_score - min_score) for s in scores]


def merge_results(
    faiss_results: List[tuple[str, float]],
    bm25_results: List[tuple[str, float]],
    faiss_weight: float = 0.6,
    bm25_weight: float = 0.4
) -> List[tuple[str, float]]:
    """
    Merge FAISS and BM25 results with weighted scoring.
    
    Args:
        faiss_results: List of (chunk_id, score) from FAISS
        bm25_results: List of (chunk_id, score) from BM25
        faiss_weight: Weight for FAISS scores
        bm25_weight: Weight for BM25 scores
        
    Returns:
        Merged and sorted list of (chunk_id, score)
    """
    # Collect all scores per chunk
    chunk_scores = defaultdict(lambda: {'faiss': 0.0, 'bm25': 0.0})
    
    # Normalize FAISS scores
    if faiss_results:
        faiss_chunk_ids, faiss_scores_raw = zip(*faiss_results)
        faiss_scores_norm = normalize_scores(list(faiss_scores_raw))
        
        for chunk_id, score in zip(faiss_chunk_ids, faiss_scores_norm):
            chunk_scores[chunk_id]['faiss'] = score
    
    # Normalize BM25 scores
    if bm25_results:
        bm25_chunk_ids, bm25_scores_raw = zip(*bm25_results)
        bm25_scores_norm = normalize_scores(list(bm25_scores_raw))
        
        for chunk_id, score in zip(bm25_chunk_ids, bm25_scores_norm):
            chunk_scores[chunk_id]['bm25'] = score
    
    # Compute weighted scores
    merged = []
    for chunk_id, scores in chunk_scores.items():
        combined_score = (
            faiss_weight * scores['faiss'] +
            bm25_weight * scores['bm25']
        )
        merged.append((chunk_id, combined_score))
    
    # Sort by score descending
    merged.sort(key=lambda x: x[1], reverse=True)
    
    return merged


def apply_metadata_filter(
    results: List[tuple[str, float]],
    chunks_by_id: Dict[str, Chunk],
    template_id: Optional[str] = None
) -> List[tuple[str, float]]:
    """
    Filter results by metadata (e.g., template_id).
    
    Args:
        results: List of (chunk_id, score)
        chunks_by_id: Dictionary mapping chunk_id to Chunk
        template_id: Filter to specific template
        
    Returns:
        Filtered results
    """
    if not template_id:
        return results
    
    filtered = []
    for chunk_id, score in results:
        chunk = chunks_by_id.get(chunk_id)
        if chunk:
            chunk_template = chunk.metadata.template_id
            
            # Allow exact match or UNKNOWN
            if chunk_template == template_id or chunk_template == "UNKNOWN":
                # Boost exact matches slightly
                if chunk_template == template_id:
                    score *= 1.1
                filtered.append((chunk_id, score))
    
    # Re-sort after boosting
    filtered.sort(key=lambda x: x[1], reverse=True)
    
    return filtered


def hybrid_retrieve(
    query: str,
    faiss_index: FAISSIndex,
    bm25_index: Optional[BM25Index],
    chunks_by_id: Dict[str, Chunk],
    template_id: Optional[str] = None,
    top_k_faiss: int = 10,
    top_k_bm25: int = 10,
    final_top_k: int = 6,
    use_faiss: bool = True,
    use_bm25: bool = True
) -> List[EvidenceChunk]:
    """
    Hybrid retrieval combining FAISS and BM25.
    
    Args:
        query: Query string
        faiss_index: FAISS index
        bm25_index: BM25 index (optional)
        chunks_by_id: Dictionary mapping chunk_id to Chunk
        template_id: Filter results to this template
        top_k_faiss: Number of FAISS results to retrieve
        top_k_bm25: Number of BM25 results to retrieve
        final_top_k: Final number of results to return
        use_faiss: Whether to use FAISS
        use_bm25: Whether to use BM25
        
    Returns:
        List of EvidenceChunk objects
    """
    # Retrieve from FAISS
    faiss_results = []
    if use_faiss and faiss_index:
        faiss_results = faiss_index.search(query, k=top_k_faiss)
    
    # Retrieve from BM25
    bm25_results = []
    if use_bm25 and bm25_index:
        bm25_results = bm25_index.search(query, k=top_k_bm25)
    
    # Merge results
    merged = merge_results(faiss_results, bm25_results)
    
    # Apply metadata filter
    filtered = apply_metadata_filter(merged, chunks_by_id, template_id)
    
    # Select top-k
    top_results = filtered[:final_top_k]
    
    # Convert to EvidenceChunk objects
    evidence = []
    for chunk_id, score in top_results:
        chunk = chunks_by_id.get(chunk_id)
        if chunk:
            evidence.append(EvidenceChunk(
                chunk_id=chunk_id,
                text=chunk.text,
                score=score,
                metadata=chunk.metadata.model_dump()
            ))
    
    return evidence
