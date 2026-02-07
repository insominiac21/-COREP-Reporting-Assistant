"""Main application entry point"""
import sys
import uvicorn
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from corep_assistant.config import HOST, PORT, index_exists
from corep_assistant.server.api import app
from corep_assistant.server import ui  # Import to register UI routes


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="COREP Reporting Assistant")
    parser.add_argument(
        'command',
        nargs='?',
        default='serve',
        choices=['serve', 'ingest'],
        help='Command to run (serve or ingest)'
    )
    
    args = parser.parse_args()
    
    if args.command == 'ingest':
        # Run ingestion
        print("="*60)
        print("RUNNING DOCUMENT INGESTION")
        print("="*60)
        
        from corep_assistant.ingest.build_corpus import run_ingestion, save_corpus, load_corpus
        from corep_assistant.retrieval.faiss_index import build_faiss_index
        from corep_assistant.retrieval.bm25_index import build_bm25_index
        from corep_assistant.config import CORPUS_PATH, FAISS_INDEX_PATH, BM25_INDEX_PATH
        
        # Ingest
        run_ingestion()
        
        # Load corpus
        chunks = load_corpus(CORPUS_PATH)
        
        if not chunks:
            print("ERROR: No chunks created. Exiting.")
            return
        
        # Build indexes
        print("\nBuilding FAISS index...")
        build_faiss_index(chunks, FAISS_INDEX_PATH)
        
        print("\nBuilding BM25 index...")
        build_bm25_index(chunks, BM25_INDEX_PATH)
        
        print("\n" + "="*60)
        print("INGESTION COMPLETE!")
        print("="*60)
        print(f"\nRun `python app.py` to start the server.")
        
    else:
        # Serve application
        print("="*60)
        print("COREP REPORTING ASSISTANT")
        print("="*60)
        print(f"\nStarting server at http://{HOST}:{PORT}")
        
        if not index_exists():
            print("\n⚠️  WARNING: No indexes found!")
            print("Please run: python app.py ingest")
            print("Or use the 'Ingest & Build Index' button in the UI\n")
        
        print("="*60)
        
        # Run server
        uvicorn.run(
            app,
            host=HOST,
            port=PORT,
            log_level="info"
        )


if __name__ == "__main__":
    main()
