# COREP Reporting Assistant (Prototype)

**LLM-assisted regulatory template population system using RAG + FAISS + Groq Llama**

This is a complete local prototype demonstrating how large language models combined with retrieval-augmented generation (RAG) can assist with COREP (Common Reporting) template population for banking supervision.

## 🎯 Scope

The prototype implements support for two COREP templates:
- **C 01.00**: Own Funds
- **C 07.00**: Credit Risk Exposures – Standardised Approach (CR SA)

## ✨ Features

- ✅ **Python-only**: No Node.js, no npm, single `python app.py` starts everything
- ✅ **Hybrid retrieval**: FAISS (semantic) + BM25 (keyword) with metadata filtering
- ✅ **Structured JSON output**: LLM forced to output valid JSON matching strict schemas
- ✅ **Citation enforcement**: Every populated field must cite evidence chunks
- ✅ **Multi-layer validation**: Structural, template-specific arithmetic, and rule-based checks
- ✅ **Audit trail**: SQLite database logging requests, evidence, outputs, and field-level justifications
- ✅ **Template registry**: Extendable registry for rows/columns with validation rules
- ✅ **Modern web UI**: Clean interface with tabbed results, no external dependencies

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Request                                │
│  (Template ID + Scenario + Question + As-of Date)                   │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Hybrid Retrieval                                  │
│  ┌──────────────┐         ┌──────────────┐                          │
│  │  BM25 Index  │         │ FAISS Index  │                          │
│  │  (keywords)  │         │  (semantic)  │                          │
│  └──────┬───────┘         └──────┬───────┘                          │
│         │                        │                                   │
│         └────────┬───────────────┘                                   │
│                  │ Merge + Normalize                                 │
│                  ▼                                                    │
│        Template-based Filtering                                      │
│                  │                                                    │
│                  ▼                                                    │
│           Top-K Evidence Chunks                                      │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Groq LLM (Llama)                                  │
│  • System prompt: "Use ONLY provided evidence"                       │
│  • User prompt: Evidence blocks + JSON schema                        │
│  • JSON mode: Forces structured output                               │
│  • Citation requirement: Each cell → chunk_ids                       │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Validation Layer                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Structural   │  │ C01 Arith.   │  │ C07 Rules    │              │
│  │ - Schema     │  │ - Own Funds  │  │ - Off-bal    │              │
│  │ - Row/Col IDs│  │ - Tier calc  │  │ - Default    │              │
│  │ - Citations  │  │              │  │ - Memo rows  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                          │                                           │
│                          ▼                                           │
│               Validation Report (PASS/WARN/FAIL)                     │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Output & Audit                                     │
│  • Rendered template table (HTML)                                    │
│  • Structured JSON with answers                                      │
│  • Validation findings                                               │
│  • Audit log → SQLite (field → evidence mapping)                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 📦 Installation & Setup

### 1. Clone/Navigate to Project

```bash
cd path/to/AKION
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment

Copy `.env.example` to `.env` and set your Groq API key:

```bash
copy .env.example .env
```

Edit `.env` and add your key:
```
GROQ_API_KEY=your_actual_groq_api_key_here
```

**Get a Groq API key**: https://console.groq.com/keys

### 6. Run Ingestion (First Time Only)

```bash
python app.py ingest
```

This will:
- Process sample documents from `data/raw/`
- Extract and normalize text while preserving codes
- Create COREP-aware semantic chunks
- Build FAISS and BM25 indexes
- Save corpus to `data/processed/`

### 7. Start the Server

```bash
python app.py
```

The application will be available at: **http://127.0.0.1:8000**

## ☁️ Deployment (Vercel)

This project is configured for easy deployment on **Vercel** using the `@vercel/python` builder.

### 1. Import to Vercel
Connect your GitHub repository to Vercel.

### 2. Configure Environment Variables
In the Vercel Project Settings, add the following environment variable:
- `GROQ_API_KEY`: Your actual Groq API key.

### 3. Deploy
Vercel will automatically detect the `vercel.json` and `main.py` configuration and deploy the FastAPI app as a serverless function.

> [!NOTE]
> Since this prototype uses local FAISS/BM25 indices, they are included in the repository (`data/processed/`). This allows the app to function immediately upon deployment without re-ingesting documents.

## 🚀 Usage

### Via Web UI

1. Open browser to `http://127.0.0.1:8000`
2. Select template (C01.00 or C07.00)
3. Enter as-of date (defaults to today)
4. Describe scenario (e.g., "Bank has CET1 capital of 500M, AT1 of 100M...")
5. Ask question (e.g., "Which rows should be populated?")
6. Click **Submit Question**
7. View results in tabs:
   - **Evidence**: Retrieved regulatory text chunks
   - **Structured JSON**: Full LLM output
   - **Template Extract**: Rendered table
   - **Validation**: Pass/warn/fail findings
   - **Audit Log**: Field → evidence mapping

### Via API

**Health Check:**
```bash
curl http://127.0.0.1:8000/api/health
```

**Ask Question:**
```bash
curl -X POST http://127.0.0.1:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "C01.00",
    "as_of_date": "2024-12-31",
    "scenario": "Bank has CET1 capital instruments of 500M...",
    "question": "Which rows should be populated?",
    "top_k": 6,
    "use_bm25": true,
    "use_faiss": true,
    "citation_strict": true,
    "confidence_threshold": 0.65
  }'
```

**Get Audit:**
```bash
curl http://127.0.0.1:8000/api/audit/{request_id}
```

## 📚 Demo Scenarios

### C01.00 - Own Funds

**Scenario 1: Basic Capital Composition**
```
Template: C01.00
Scenario: A bank has common equity tier 1 capital of 800 million GBP, 
additional tier 1 capital of 150 million GBP, and tier 2 capital of 
200 million GBP. Goodwill deductions amount to 50 million GBP.
Question: Which rows should be populated and what validation checks apply?
```

**Scenario 2: Retained Earnings**
```
Template: C01.00
Scenario: The institution has retained earnings of 300 million GBP 
verified by external auditors. Own CET1 instruments held by the 
institution amount to 20 million GBP.
Question: How should these items be reported in the own funds template?
```

**Scenario 3: Prudent Valuation**
```
Template: C01.00
Scenario: Prudent valuation adjustments (AVAs) for the trading book 
amount to 15 million GBP in accordance with Article 105 CRR.
Question: Which row captures this and what is the regulatory treatment?
```

### C07.00 - Credit Risk SA

**Scenario 1: Off-Balance Sheet**
```
Template: C07.00
Scenario: A bank has off-balance sheet exposures to corporate clients 
totaling 500 million GBP (pre-CCF) in the form of undrawn committed 
credit facilities. These are not derivative or repo transactions.
Question: Which rows should be used and what conversion factors apply?
```

**Scenario 2: Exposures in Default**
```
Template: C07.00
Scenario: Corporate exposures of 100 million GBP are classified as 
in default under Article 178 CRR. Provisions cover 25% of the exposure 
value.
Question: How should these be reported and what risk weight applies?
```

**Scenario 3: Mortgage-Secured**
```
Template: C07.00
Scenario: Retail exposures secured by residential property mortgages 
amount to 2 billion GBP with an average loan-to-value of 65%. The 
properties are located in the UK.
Question: Which rows capture these exposures and what risk weight category?
```

## 🔧 Extending the System

### Adding New Templates

1. Create schema file: `corep_assistant/schemas/cXX_XX.py`
2. Define allowed rows, columns, and validation rules
3. Register in `template_registry.py`
4. Add template-specific validators in `validation/`
5. Update UI template dropdown

### Adding Custom Documents

1. Place PDFs or .txt files in `data/raw/`
2. Run: `python app.py ingest`
3. System will extract, chunk, and index automatically

### Modifying Retrieval

- **Adjust weights**: Edit `hybrid.py` → `merge_results()` function
- **Change top-k**: Modify `.env` → `TOP_K_FAISS`, `TOP_K_BM25`, `FINAL_TOP_K`
- **Add reranker**: Implement `retrieval/rerank.py` and set `ENABLE_RERANKER=true`

### Customizing Validation

- **Structural**: Edit `validation/structural.py`
- **C01 math**: Edit `validation/c01_math.py`
- **C07 rules**: Edit `validation/c07_rules.py`
- **Add new validators**: Create new file, import in `validation/report.py`

## 🧪 Running Tests

```bash
pytest
```

Tests cover:
- Schema validation
- Citation enforcement
- Arithmetic validation
- Hybrid retrieval deduplication

## 📁 Repository Structure

```
AKION/
├── app.py                          # Main entry point
├── requirements.txt
├── .env.example
├── README.md
├── corep_assistant/
│   ├── config.py                   # Configuration
│   ├── ingest/                     # Document ingestion
│   │   ├── extract_pdf.py
│   │   ├── normalize.py
│   │   ├── chunking.py
│   │   ├── taxonomy_stub.py
│   │   └── build_corpus.py
│   ├── retrieval/                  # Hybrid retrieval
│   │   ├── embeddings.py
│   │   ├── faiss_index.py
│   │   ├── bm25_index.py
│   │   ├── hybrid.py
│   │   └── rerank.py
│   ├── schemas/                    # Template registries
│   │   ├── c01_00.py
│   │   ├── c07_00.py
│   │   └── template_registry.py
│   ├── llm/                        # LLM integration
│   │   ├── groq_client.py
│   │   ├── prompts.py
│   │   └── generate.py
│   ├── validation/                 # Validation layer
│   │   ├── structural.py
│   │   ├── c01_math.py
│   │   ├── c07_rules.py
│   │   └── report.py
│   ├── storage/                    # Audit database
│   │   └── sqlite.py
│   ├── rendering/                  # HTML rendering
│   │   └── template_render.py
│   └── server/                     # FastAPI server
│       ├── api.py
│       ├── ui.py
│       ├── templates/
│       │   └── index.html
│       └── static/
│           ├── app.js
│           └── styles.css
├── data/
│   ├── raw/                        # Place PDFs/docs here
│   │   ├── sample_c01.txt
│   │   └── sample_c07.txt
│   └── processed/                  # Generated indexes
│       ├── corpus.jsonl
│       ├── faiss.index
│       ├── bm25.pkl
│       └── meta.sqlite
└── tests/
    ├── test_schema_validation.py
    ├── test_citation_strict.py
    ├── test_c01_math.py
    └── test_hybrid_retrieval.py
```

## ⚠️ Known Limitations

1. **Sample Documents**: Included sample docs are placeholders. Replace with real COREP reporting instructions and EBA Q&As for production use.

2. **Template Coverage**: Only C01.00 and C07.00 are implemented. Full COREP framework has 30+ templates.

3. **Taxonomy Integration**: DPM/XBRL parsing is stubbed. Future versions should parse official taxonomy files for complete row/column definitions.

4. **Validation Rules**: Implemented rules are a subset. Production systems need complete rulebook from EBA validation formulas.

5. **Reranker**: Cross-encoder reranking is stubbed but not implemented. Can significantly improve retrieval precision.

6. **Multi-lingual**: System assumes English text. Real COREP docs may be multilingual.

## 🚦 Next Steps

### Immediate Enhancements
- [ ] Add real COREP reporting instructions PDFs
- [ ] Implement cross-encoder reranking
- [ ] Add more C01/C07 validation rules
- [ ] Expand template registry with more rows

### Medium-term
- [ ] Parse DPM/XBRL taxonomy files
- [ ] Add more templates (C02, C08, C09, etc.)
- [ ] Implement formula-based validation from XBRL
- [ ] Add user authentication and session management

### Long-term
- [ ] Multi-template reasoning (cross-template consistency)
- [ ] Historical data comparison
- [ ] Regulatory change impact analysis
- [ ] Export to official XBRL format

## 📄 License

Prototype for demonstration purposes.

## 🤝 Contributing

This is a prototype. For production deployment:
1. Replace sample docs with official regulatory texts
2. Integrate official DPM/XBRL taxonomies
3. Implement complete validation rulesets
4. Add comprehensive test coverage
5. Implement proper security (API keys, rate limiting, etc.)

## 📞 Support

For questions about COREP templates, consult:
- [EBA Single Rulebook](https://www.eba.europa.eu/regulation-and-policy/single-rulebook)
- [Bank of England COREP Instructions](https://www.bankofengland.co.uk/prudential-regulation/regulatory-reporting)
- [CRR Text](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32013R0575)

---

**Built with**: Python 3.10+ | FastAPI | FAISS | sentence-transformers | Groq Llama | SQLite
