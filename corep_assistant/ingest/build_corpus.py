"""Build corpus from raw documents"""
import json
from pathlib import Path
from typing import List
from corep_assistant.schemas import Chunk
from corep_assistant.config import RAW_DATA_DIR, CORPUS_PATH
from . import extract_document
from .normalize import normalize_text
from .chunking import chunk_corep_document


def build_corpus() -> List[Chunk]:
    """
    Build corpus from all documents in RAW_DATA_DIR.
    
    Returns:
        List of all chunks
    """
    all_chunks = []
    
    # Find all PDF and TXT files
    doc_files = list(RAW_DATA_DIR.glob("*.pdf")) + list(RAW_DATA_DIR.glob("*.txt"))
    
    if not doc_files:
        print(f"No documents found in {RAW_DATA_DIR}")
        return []
    
    print(f"Processing {len(doc_files)} documents...")
    
    for doc_path in doc_files:
        print(f"  Processing: {doc_path.name}")
        
        # Extract pages
        pages = extract_document(doc_path)
        
        if not pages:
            print(f"    Failed to extract text from {doc_path.name}")
            continue
        
        # Normalize page texts
        normalized_pages = [
            (page_num, normalize_text(text))
            for page_num, text in pages
        ]
        
        # Chunk document
        chunks = chunk_corep_document(normalized_pages, doc_path.name)
        
        print(f"    Created {len(chunks)} chunks")
        all_chunks.extend(chunks)
    
    print(f"\nTotal chunks created: {len(all_chunks)}")
    return all_chunks


def save_corpus(chunks: List[Chunk], output_path: Path) -> None:
    """
    Save corpus to JSONL file.
    
    Args:
        chunks: List of chunks to save
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            # Convert to dict
            chunk_dict = {
                "text": chunk.text,
                "metadata": chunk.metadata.model_dump()
            }
            f.write(json.dumps(chunk_dict, ensure_ascii=False) + '\n')
    
    print(f"Saved corpus to: {output_path}")


def load_corpus(corpus_path: Path) -> List[Chunk]:
    """
    Load corpus from JSONL file.
    
    Args:
        corpus_path: Path to corpus file
        
    Returns:
        List of Chunk objects
    """
    chunks = []
    
    if not corpus_path.exists():
        print(f"Corpus file not found: {corpus_path}")
        return []
    
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for line in f:
            chunk_dict = json.loads(line)
            chunk = Chunk(**chunk_dict)
            chunks.append(chunk)
    
    return chunks


def run_ingestion() -> None:
    """Run full ingestion pipeline"""
    print("="*60)
    print("COREP ASSISTANT - DOCUMENT INGESTION")
    print("="*60)
    
    # Build corpus
    chunks = build_corpus()
    
    if not chunks:
        print("ERROR: No chunks created. Check your documents.")
        return
    
    # Save corpus
    save_corpus(chunks, CORPUS_PATH)
    
    print("\nIngestion complete!")
    print(f"Next step: Build embeddings and indexes")


if __name__ == "__main__":
    run_ingestion()
