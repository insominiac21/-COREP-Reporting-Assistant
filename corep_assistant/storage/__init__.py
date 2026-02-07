"""SQLite database for audit logs and metadata"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from corep_assistant.config import METADATA_DB_PATH


class AuditDB:
    """SQLite database for audit logs"""
    
    def __init__(self, db_path: Path = METADATA_DB_PATH):
        """Initialize database connection"""
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(str(self.db_path))
    
    def init_schema(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                template_id TEXT NOT NULL,
                question TEXT NOT NULL,
                scenario TEXT,
                as_of_date TEXT NOT NULL,
                settings_json TEXT
            )
        """)
        
        # Evidence table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                chunk_id TEXT NOT NULL,
                rank INTEGER NOT NULL,
                score REAL NOT NULL,
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )
        """)
        
        # Outputs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                structured_json TEXT NOT NULL,
                validation_json TEXT NOT NULL,
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )
        """)
        
        # Field audit table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS field_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                cell_id TEXT NOT NULL,
                value REAL,
                evidence_chunk_ids_json TEXT NOT NULL,
                reasoning TEXT,
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def log_request(
        self,
        request_id: str,
        template_id: str,
        question: str,
        scenario: str,
        as_of_date: str,
        settings: Dict[str, Any]
    ):
        """Log request"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO requests (id, timestamp, template_id, question, scenario, as_of_date, settings_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            request_id,
            datetime.now().isoformat(),
            template_id,
            question,
            scenario,
            as_of_date,
            json.dumps(settings)
        ))
        
        conn.commit()
        conn.close()
    
    def log_evidence(self, request_id: str, evidence_list: List[Dict[str, Any]]):
        """Log evidence chunks"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for rank, ev in enumerate(evidence_list, 1):
            cursor.execute("""
                INSERT INTO evidence (request_id, chunk_id, rank, score)
                VALUES (?, ?, ?, ?)
            """, (
                request_id,
                ev.get('chunk_id', 'unknown'),
                rank,
                ev.get('score', 0.0)
            ))
        
        conn.commit()
        conn.close()
    
    def log_output(
        self,
        request_id: str,
        structured_output: Dict[str, Any],
        validation_report: Dict[str, Any]
    ):
        """Log structured output and validation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO outputs (request_id, structured_json, validation_json)
            VALUES (?, ?, ?)
        """, (
            request_id,
            json.dumps(structured_output),
            json.dumps(validation_report)
        ))
        
        conn.commit()
        conn.close()
    
    def log_field_audit(self, request_id: str, field_audits: List[Dict[str, Any]]):
        """Log field-level audit trail"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for audit_entry in field_audits:
            cursor.execute("""
                INSERT INTO field_audit (request_id, cell_id, value, evidence_chunk_ids_json, reasoning)
                VALUES (?, ?, ?, ?, ?)
            """, (
                request_id,
                audit_entry.get('cell_id', ''),
                audit_entry.get('value'),
                json.dumps(audit_entry.get('evidence_chunk_ids', [])),
                audit_entry.get('reasoning', '')
            ))
        
        conn.commit()
        conn.close()
    
    def get_audit(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve audit information for request"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get request
        cursor.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
        request_row = cursor.fetchone()
        
        if not request_row:
            conn.close()
            return None
        
        # Get evidence
        cursor.execute("SELECT chunk_id, rank, score FROM evidence WHERE request_id = ? ORDER BY rank", (request_id,))
        evidence_rows = cursor.fetchall()
        
        # Get output
        cursor.execute("SELECT structured_json, validation_json FROM outputs WHERE request_id = ?", (request_id,))
        output_row = cursor.fetchone()
        
        # Get field audit
        cursor.execute("SELECT cell_id, value, evidence_chunk_ids_json, reasoning FROM field_audit WHERE request_id = ?", (request_id,))
        field_audit_rows = cursor.fetchall()
        
        conn.close()
        
        audit = {
            "request_id": request_row[0],
            "timestamp": request_row[1],
            "template_id": request_row[2],
            "question": request_row[3],
            "scenario": request_row[4],
            "as_of_date": request_row[5],
            "settings": json.loads(request_row[6]) if request_row[6] else {},
            "evidence": [
                {"chunk_id": row[0], "rank": row[1], "score": row[2]}
                for row in evidence_rows
            ],
            "output": json.loads(output_row[0]) if output_row else {},
            "validation": json.loads(output_row[1]) if output_row else {},
            "field_audit": [
                {
                    "cell_id": row[0],
                    "value": row[1],
                    "evidence_chunk_ids": json.loads(row[2]),
                    "reasoning": row[3]
                }
                for row in field_audit_rows
            ]
        }
        
        return audit


def get_audit_db() -> AuditDB:
    """Get global audit DB instance"""
    return AuditDB()
