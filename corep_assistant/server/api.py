"""FastAPI application and routes"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import uuid
from typing import Dict, Any
from datetime import datetime

from corep_assistant.schemas import AskRequest, AskResponse, EvidenceChunk
from corep_assistant.config import (
    index_exists, CORPUS_PATH, FAISS_INDEX_PATH, BM25_INDEX_PATH,
    TOP_K_FAISS, TOP_K_BM25, FINAL_TOP_K
)
from corep_assistant.ingest.build_corpus import run_ingestion, load_corpus
from corep_assistant.retrieval.faiss_index import build_faiss_index, load_faiss_index
from corep_assistant.retrieval.bm25_index import build_bm25_index, load_bm25_index
from corep_assistant.retrieval.hybrid import hybrid_retrieve
from corep_assistant.llm.generate import generate_structured_output, create_field_audit_log
from corep_assistant.validation.report import run_all_validations
from corep_assistant.storage import get_audit_db
from corep_assistant.rendering import render_template_table, render_evidence_list, render_validation_findings
from corep_assistant.schemas.template_registry import get_all_templates, get_template_metadata

# Initialize FastAPI app
app = FastAPI(title="COREP Assistant", version="0.1.0")

# Global state
_faiss_index = None
_bm25_index = None
_chunks_by_id = {}

# Get base directory for templates/static
BASE_DIR = Path(__file__).parent

# Mount static files
STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    print(f"Static files mounted from: {STATIC_DIR}")
else:
    print(f"WARNING: Static directory not found at {STATIC_DIR}")


@app.on_event("startup")
async def startup_event():
    """Load indexes on startup if they exist"""
    global _faiss_index, _bm25_index, _chunks_by_id
    
    if index_exists():
        print("Loading existing indexes...")
        
        # Load corpus
        chunks = load_corpus(CORPUS_PATH)
        _chunks_by_id = {chunk.metadata.chunk_id: chunk for chunk in chunks}
        print(f"Loaded {len(chunks)} chunks")
        
        # Load FAISS
        _faiss_index = load_faiss_index(FAISS_INDEX_PATH)
        
        # Load BM25
        _bm25_index = load_bm25_index(BM25_INDEX_PATH)
        
        print("Indexes loaded successfully!")
    else:
        print("No indexes found. Please run ingestion first.")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "indexes_loaded": _faiss_index is not None and _bm25_index is not None,
        "chunks_count": len(_chunks_by_id)
    }


@app.post("/api/ingest")
async def ingest_documents():
    """Ingest raw documents and build indexes"""
    global _faiss_index, _bm25_index, _chunks_by_id
    
    try:
        # Run ingestion
        print("Starting ingestion...")
        run_ingestion()
        
        # Load corpus
        chunks = load_corpus(CORPUS_PATH)
        if not chunks:
            raise HTTPException(status_code=500, detail="No chunks created during ingestion")
        
        _chunks_by_id = {chunk.metadata.chunk_id: chunk for chunk in chunks}
        
        # Build FAISS index
        print("Building FAISS index...")
        _faiss_index = build_faiss_index(chunks, FAISS_INDEX_PATH)
        
        # Build BM25 index
        print("Building BM25 index...")
        _bm25_index = build_bm25_index(chunks, BM25_INDEX_PATH)
        
        return {
            "status": "success",
            "chunks_created": len(chunks),
            "message": "Ingestion and indexing complete!"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.get("/api/templates")
async def list_templates():
    """List available templates"""
    templates = get_all_templates()
    
    result = []
    for template_id in templates:
        metadata = get_template_metadata(template_id)
        result.append(metadata)
    
    return {"templates": result}


@app.post("/api/ask")
async def ask_question(request: AskRequest):
    """Main API endpoint for asking questions"""
    print("\n" + "="*60, flush=True)
    print(f"NEW REQUEST RECEIVED", flush=True)
    print(f"Template: {request.template_id}", flush=True)
    print(f"Question: {request.question[:50]}...", flush=True)
    print("="*60, flush=True)
    
    if not _faiss_index or not _bm25_index:
        raise HTTPException(
            status_code=503,
            detail="Indexes not loaded. Please run ingestion first."
        )
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    print(f"[{request_id}] Generated request ID", flush=True)
    
    try:
        # 1. Hybrid retrieval
        print(f"[{request_id}] Step 1: Starting hybrid retrieval...", flush=True)
        query = f"{request.question}\n\n{request.scenario}"
        
        evidence = hybrid_retrieve(
            query=query,
            faiss_index=_faiss_index if request.use_faiss else None,
            bm25_index=_bm25_index if request.use_bm25 else None,
            chunks_by_id=_chunks_by_id,
            template_id=request.template_id,
            top_k_faiss=TOP_K_FAISS,
            top_k_bm25=TOP_K_BM25,
            final_top_k=request.top_k,
            use_faiss=request.use_faiss,
            use_bm25=request.use_bm25
        )
        print(f"[{request_id}] Step 1 complete: Retrieved {len(evidence)} evidence chunks")
        
        # 2. Generate structured output
        print(f"[{request_id}] Step 2: Calling LLM for structured output...")
        try:
            structured_output = generate_structured_output(
                template_id=request.template_id,
                as_of_date=request.as_of_date,
                scenario=request.scenario,
                question=request.question,
                evidence=evidence
            )
            print(f"[{request_id}] Step 2 complete: Generated output with {len(structured_output.answers) if structured_output else 0} answers")
        except Exception as e:
            err_msg = str(e)
            if "rate limit" in err_msg.lower():
                print(f"[{request_id}] RATE LIMIT ERROR: {err_msg}")
                raise HTTPException(status_code=429, detail=f"API Rate Limit Reached: {err_msg}")
            
            print(f"[{request_id}] ERROR in Step 2 (LLM generation): {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}")
        
        if not structured_output:
            raise HTTPException(status_code=500, detail="Failed to generate output")
        
        # 3. Run validation
        print(f"[{request_id}] Step 3: Running validation...")
        try:
            validation_report = run_all_validations(structured_output, request.scenario)
            print(f"[{request_id}] Step 3 complete: Validation status = {validation_report.get('overall_status')}")
        except Exception as e:
            print(f"[{request_id}] ERROR in Step 3 (validation): {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")
        
        # 4. Render template
        print(f"[{request_id}] Step 4: Rendering template...")
        try:
            rendered_html = render_template_table(structured_output)
            print(f"[{request_id}] Step 4 complete: Rendered HTML ({len(rendered_html)} chars)")
        except Exception as e:
            print(f"[{request_id}] ERROR in Step 4 (rendering): {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Rendering failed: {str(e)}")
        
        # 5. Create audit log
        print(f"[{request_id}] Step 5: Creating audit log...")
        try:
            field_audit = create_field_audit_log(structured_output)
            print(f"[{request_id}] Step 5 complete: Created {len(field_audit)} audit entries")
        except Exception as e:
            print(f"[{request_id}] ERROR in Step 5 (audit log): {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Audit log creation failed: {str(e)}")
        
        # 6. Store in audit DB
        print(f"[{request_id}] Step 6: Storing in audit DB...")
        try:
            audit_db = get_audit_db()
            
            settings = {
                "top_k": request.top_k,
                "use_bm25": request.use_bm25,
                "use_faiss": request.use_faiss,
                "citation_strict": request.citation_strict,
                "confidence_threshold": request.confidence_threshold
            }
            
            audit_db.log_request(
                request_id=request_id,
                template_id=request.template_id,
                question=request.question,
                scenario=request.scenario,
                as_of_date=request.as_of_date,
                settings=settings
            )
            
            audit_db.log_evidence(request_id, [ev.model_dump() for ev in evidence])
            audit_db.log_output(request_id, structured_output.model_dump(), validation_report)
            audit_db.log_field_audit(request_id, field_audit)
            print(f"[{request_id}] Step 6 complete: Audit data stored")
        except Exception as e:
            print(f"[{request_id}] ERROR in Step 6 (audit DB): {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            # Don't fail the request if audit logging fails
            print(f"[{request_id}] WARNING: Continuing despite audit DB error")
        
        # 7. Build response
        print(f"[{request_id}] Step 7: Building response...")
        try:
            response = AskResponse(
                request_id=request_id,
                template_id=request.template_id,
                evidence=evidence,
                structured_output=structured_output,
                rendered_template_html=rendered_html,
                validation=validation_report
            )
            print(f"[{request_id}] Step 7 complete: Response object created")
        except Exception as e:
            print(f"[{request_id}] ERROR in Step 7 (response building): {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Response building failed: {str(e)}")
        
        print(f"[{request_id}] SUCCESS: Returning response")
        return response.model_dump()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/api/audit/{request_id}")
async def get_audit(request_id: str):
    """Retrieve audit information for a request"""
    audit_db = get_audit_db()
    audit = audit_db.get_audit(request_id)
    
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    return audit
