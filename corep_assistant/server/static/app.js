// COREP Assistant - Frontend JavaScript

// State
let currentRequestId = null;

// Elements
const statusText = document.getElementById('status-text');
const ingestBtn = document.getElementById('ingest-btn');
const submitBtn = document.getElementById('submit-btn');
const resultsSection = document.getElementById('results-section');

// Form inputs
const templateSelect = document.getElementById('template-select');
const asOfDateInput = document.getElementById('as-of-date');
const scenarioInput = document.getElementById('scenario');
const questionInput = document.getElementById('question');
const topKInput = document.getElementById('top-k');
const useBM25Input = document.getElementById('use-bm25');
const useFAISSInput = document.getElementById('use-faiss');
const citationStrictInput = document.getElementById('citation-strict');
const confidenceThresholdInput = document.getElementById('confidence-threshold');

// Output areas
const evidenceOutput = document.getElementById('evidence-output');
const jsonOutput = document.getElementById('json-output');
const templateOutput = document.getElementById('template-output');
const validationOutput = document.getElementById('validation-output');


// Tab handling
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;

        // Update active states
        tabButtons.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));

        btn.classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
    });
});

// Initialize with today's date
function initializeDate() {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    asOfDateInput.value = `${year}-${month}-${day}`;
}

// Set status
function setStatus(message, isError = false) {
    statusText.textContent = message;
    statusText.style.color = isError ? '#d32f2f' : '#333';
}

// Show loading
function setLoading(isLoading) {
    if (isLoading) {
        submitBtn.disabled = true;
        submitBtn.textContent = '⏳ Processing...';
    } else {
        submitBtn.disabled = false;
        submitBtn.textContent = '🚀 Submit Question';
    }
}

// Ingest documents
ingestBtn.addEventListener('click', async () => {
    ingestBtn.disabled = true;
    ingestBtn.textContent = '⏳ Ingesting...';
    setStatus('Running document ingestion and building indexes...');

    try {
        const response = await fetch('/api/ingest', {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            setStatus(`✅ Ingestion complete! ${data.chunks_created} chunks created.`);
            ingestBtn.textContent = '✔️ Indexes Built';
        } else {
            setStatus(`❌ Ingestion failed: ${data.detail}`, true);
            ingestBtn.disabled = false;
            ingestBtn.textContent = '🔄 Retry Ingestion';
        }
    } catch (error) {
        setStatus(`❌ Error: ${error.message}`, true);
        ingestBtn.disabled = false;
        ingestBtn.textContent = '🔄 Retry Ingestion';
    }
});

// Submit question
submitBtn.addEventListener('click', async () => {
    // Validate inputs
    if (!questionInput.value.trim()) {
        alert('Please enter a question');
        return;
    }

    setLoading(true);
    setStatus('Processing your question...');
    resultsSection.classList.add('hidden');

    const requestData = {
        template_id: templateSelect.value,
        as_of_date: asOfDateInput.value,
        scenario: scenarioInput.value,
        question: questionInput.value,
        top_k: parseInt(topKInput.value),
        use_bm25: useBM25Input.checked,
        use_faiss: useFAISSInput.checked,
        citation_strict: citationStrictInput.checked,
        confidence_threshold: parseFloat(confidenceThresholdInput.value)
    };

    try {
        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        const data = await response.json();

        if (response.ok) {
            currentRequestId = data.request_id;
            displayResults(data);
            setStatus('✅ Results ready!');
            resultsSection.classList.remove('hidden');
        } else {
            setStatus(`❌ Error: ${data.detail}`, true);
            alert(`Error: ${data.detail}`);
        }
    } catch (error) {
        setStatus(`❌ Error: ${error.message}`, true);
        alert(`Error: ${error.message}`);
    } finally {
        setLoading(false);
    }
});

// Display results
function displayResults(data) {
    // Evidence
    if (data.evidence && data.evidence.length > 0) {
        evidenceOutput.innerHTML = renderEvidence(data.evidence);
    } else {
        evidenceOutput.innerHTML = '<p>No evidence retrieved.</p>';
    }

    // Answer Panel
    renderAnswer(data.structured_output);

    // Structured JSON
    jsonOutput.textContent = JSON.stringify(data.structured_output, null, 2);

    // Template extract
    templateOutput.innerHTML = data.rendered_template_html;

    // Validation
    validationOutput.innerHTML = renderValidation(data.validation);


}

// Render Answer Panel
function renderAnswer(output) {
    const answerText = document.getElementById('final-answer-text');
    const citationsList = document.getElementById('answer-citations');

    // Clear previous
    answerText.innerHTML = '';
    citationsList.innerHTML = '';

    if (output.final_answer) {
        // Simple markdown-like formatting for bold/newlines
        let html = output.final_answer
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
        answerText.innerHTML = html;
    } else {
        answerText.textContent = 'No natural language answer generated.';
    }

    if (output.answer_citations && output.answer_citations.length > 0) {
        output.answer_citations.forEach(cit => {
            const div = document.createElement('div');
            div.className = 'citation-item';
            div.innerHTML = `
                <span class="cite-purpose">${cit.purpose || 'ref'}</span>
                <span class="cite-id">${cit.chunk_id}</span>
                <span class="cite-quote">"${cit.quote_span}"</span>
            `;
            citationsList.appendChild(div);
        });
    }
}

// Render evidence
function renderEvidence(evidence) {
    let html = '<div class="evidence-list">';

    evidence.forEach((ev, i) => {
        const metadata = ev.metadata || {};
        html += `
            <div class="evidence-item">
                <div class="evidence-header">
                    <span class="evidence-num">[${i + 1}]</span>
                    <span class="chunk-id">${ev.chunk_id}</span>
                    <span class="score">Score: ${ev.score.toFixed(3)}</span>
                </div>
                <div class="evidence-meta">
                    <span>Template: ${metadata.template_id || 'UNKNOWN'}</span> |
                    <span>Type: ${metadata.chunk_type || 'unknown'}</span> |
                    <span>Row: ${metadata.row_code || 'N/A'}</span> |
                    <span>Source: ${metadata.source_doc || 'unknown'} (p${metadata.page_start || '?'})</span>
                </div>
                <div class="evidence-text">${ev.text.substring(0, 400)}...</div>
            </div>
        `;
    });

    html += '</div>';
    return html;
}

// Render validation
function renderValidation(validation) {
    const status = validation.overall_status || 'UNKNOWN';
    const counts = validation.severity_counts || {};
    const findings = validation.findings || [];

    let html = `
        <div class="validation-report status-${status.toLowerCase()}">
            <div class="status-summary">
                <span class="overall-status ${status.toLowerCase()}">${status}</span>
                <span class="counts">
                    PASS: ${counts.PASS || 0} |
                    WARN: ${counts.WARN || 0} |
                    FAIL: ${counts.FAIL || 0}
                </span>
            </div>
            <div class="findings-list">
    `;

    findings.forEach(finding => {
        const severity = finding.severity || 'UNKNOWN';
        const cells = finding.impacted_cells || [];

        html += `
            <div class="finding ${severity.toLowerCase()}">
                <span class="severity-badge ${severity.toLowerCase()}">${severity}</span>
                <span class="rule-id">${finding.rule_id}</span>
                <span class="message">${finding.message}</span>
                ${cells.length > 0 ? `<span class="impacted-cells">Cells: ${cells.join(', ')}</span>` : ''}
            </div>
        `;
    });

    html += '</div></div>';
    return html;
}



// Initialize on load
window.addEventListener('DOMContentLoaded', () => {
    initializeDate();

    // Check health
    fetch('/api/health')
        .then(res => res.json())
        .then(data => {
            if (data.indexes_loaded) {
                setStatus(`✅ Ready (${data.chunks_count} chunks loaded)`);
                ingestBtn.textContent = '✔️ Indexes Loaded';
                ingestBtn.disabled = true;
            } else {
                setStatus('⚠️ No indexes found. Please ingest documents first.');
            }
        })
        .catch(err => {
            setStatus('❌ Failed to connect to server', true);
        });
});
