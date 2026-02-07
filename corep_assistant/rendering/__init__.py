"""Template rendering to HTML"""
from typing import List
from corep_assistant.schemas import TemplateOutput, AnswerItem


def render_template_table(output: TemplateOutput) -> str:
    """
    Render template output as HTML table.
    
    Args:
        output: Template output
        
    Returns:
        HTML string
    """
    if not output.answers:
        return "<p>No answers populated.</p>"
    
    # Get unique columns
    columns = sorted(set(answer.col_code for answer in output.answers))
    
    # Build table header
    html = f"""<div class="template-table">
<h3>Template {output.template_id} - Extract</h3>
<p><strong>As of:</strong> {output.as_of_date}</p>
<table class="corep-table">
<thead>
<tr>
<th>Row Code</th>
<th>Concept</th>"""
    
    for col in columns:
        html += f"<th>Column {col}</th>"
    
    html += "</tr>\n</thead>\n<tbody>\n"
    
    # Group answers by row
    rows_dict = {}
    for answer in output.answers:
        row_code = answer.row_code
        if row_code not in rows_dict:
            rows_dict[row_code] = {
                "concept": answer.concept,
                "columns": {}
            }
        rows_dict[row_code]["columns"][answer.col_code] = answer
    
    # Render rows
    for row_code in sorted(rows_dict.keys()):
        row_data = rows_dict[row_code]
        html += f"<tr>\n<td class='row-code'>{row_code}</td>\n"
        html += f"<td class='concept'>{row_data['concept']}</td>\n"
        
        for col in columns:
            answer = row_data["columns"].get(col)
            if answer and answer.value is not None:
                # Format value
                value_str = f"{answer.value:,.2f}" if isinstance(answer.value, (int, float)) else str(answer.value)
                confidence_class = "high" if answer.confidence > 0.8 else "medium" if answer.confidence > 0.5 else "low"
                html += f"<td class='value {confidence_class}' title='Confidence: {answer.confidence:.2f}'>{value_str}</td>\n"
            else:
                html += "<td class='value-empty'>—</td>\n"
        
        html += "</tr>\n"
    
    html += "</tbody>\n</table>\n</div>"
    
    return html


def render_evidence_list(evidence: List) -> str:
    """
    Render evidence list as HTML.
    
    Args:
        evidence: List of evidence chunks
        
    Returns:
        HTML string
    """
    if not evidence:
        return "<p>No evidence retrieved.</p>"
    
    html = "<div class='evidence-list'>\n"
    
    for i, ev in enumerate(evidence, 1):
        metadata = ev.get('metadata', {}) if isinstance(ev, dict) else ev.metadata
        chunk_id = ev.get('chunk_id', '') if isinstance(ev, dict) else ev.chunk_id
        text = ev.get('text', '') if isinstance(ev, dict) else ev.text
        score = ev.get('score', 0.0) if isinstance(ev, dict) else ev.score
        
        template_id = metadata.get('template_id', 'UNKNOWN')
        chunk_type = metadata.get('chunk_type', 'unknown')
        row_code = metadata.get('row_code') or 'N/A'
        source_doc = metadata.get('source_doc', 'unknown')
        page_start = metadata.get('page_start', '?')
        
        html += f"""<div class='evidence-item'>
<div class='evidence-header'>
<span class='evidence-num'>[{i}]</span>
<span class='chunk-id'>{chunk_id}</span>
<span class='score'>Score: {score:.3f}</span>
</div>
<div class='evidence-meta'>
<span>Template: {template_id}</span> |
<span>Type: {chunk_type}</span> |
<span>Row: {row_code}</span> |
<span>Source: {source_doc} (p{page_start})</span>
</div>
<div class='evidence-text'>{text[:400]}...</div>
</div>\n"""
    
    html += "</div>"
    
    return html


def render_validation_findings(validation_report: dict) -> str:
    """
    Render validation findings as HTML.
    
    Args:
        validation_report: Validation report dict
        
    Returns:
        HTML string
    """
    overall_status = validation_report.get('overall_status', 'UNKNOWN')
    severity_counts = validation_report.get('severity_counts', {})
    findings = validation_report.get('findings', [])
    
    status_class = overall_status.lower()
    
    html = f"""<div class='validation-report status-{status_class}'>
<h3>Validation Report</h3>
<div class='status-summary'>
<span class='overall-status {status_class}'>{overall_status}</span>
<span class='counts'>
PASS: {severity_counts.get('PASS', 0)} |
WARN: {severity_counts.get('WARN', 0)} |
FAIL: {severity_counts.get('FAIL', 0)}
</span>
</div>
<div class='findings-list'>
"""
    
    for finding in findings:
        severity = finding.get('severity', 'UNKNOWN')
        rule_id = finding.get('rule_id', '')
        message = finding.get('message', '')
        impacted_cells = finding.get('impacted_cells', [])
        
        severity_class = severity.lower()
        cells_str = ', '.join(impacted_cells) if impacted_cells else 'N/A'
        
        html += f"""<div class='finding {severity_class}'>
<span class='severity-badge {severity_class}'>{severity}</span>
<span class='rule-id'>{rule_id}</span>
<span class='message'>{message}</span>
{f"<span class='impacted-cells'>Cells: {cells_str}</span>" if impacted_cells else ""}
</div>\n"""
    
    html += "</div>\n</div>"
    
    return html
