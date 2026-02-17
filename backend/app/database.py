"""Database management for persistent analysis storage."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from app.models.schemas import AnalysisDetail, StructuralModel, AnalysisResults, Load
from app.config import settings


class Database:
    """SQLite database for analysis storage."""
    
    def __init__(self, db_path: str = "analyses.db"):
        """Initialize database connection."""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Create tables if they don't exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    analysis_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    material TEXT NOT NULL,
                    scale_factor REAL NOT NULL,
                    detection_method TEXT NOT NULL,
                    model_json TEXT,
                    results_json TEXT,
                    loads_json TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON analyses(created_at DESC)
            """)
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def save_analysis(self, analysis: AnalysisDetail) -> None:
        """Save or update an analysis."""
        from datetime import UTC
        now = datetime.now(UTC).isoformat()
        
        # Serialize complex fields to JSON
        model_json = analysis.model.model_dump_json() if analysis.model else None
        results_json = analysis.results.model_dump_json() if analysis.results else None
        loads_json = json.dumps([load.model_dump() for load in analysis.loads])
        
        with self._get_connection() as conn:
            # Check if analysis exists
            cursor = conn.execute(
                "SELECT created_at FROM analyses WHERE analysis_id = ?",
                (analysis.analysis_id,)
            )
            row = cursor.fetchone()
            created_at = row[0] if row else now
            
            conn.execute("""
                INSERT OR REPLACE INTO analyses (
                    analysis_id, status, material, scale_factor, detection_method,
                    model_json, results_json, loads_json, error, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis.analysis_id,
                analysis.status,
                analysis.material,
                analysis.scale_factor,
                analysis.detection_method,
                model_json,
                results_json,
                loads_json,
                analysis.error,
                created_at,
                now
            ))
            conn.commit()
    
    def get_analysis(self, analysis_id: str) -> Optional[AnalysisDetail]:
        """Get analysis by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM analyses WHERE analysis_id = ?",
                (analysis_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_analysis(row)
    
    def list_analyses(self, skip: int = 0, limit: int = 10) -> tuple[list[AnalysisDetail], int]:
        """List analyses with pagination."""
        with self._get_connection() as conn:
            # Get total count
            cursor = conn.execute("SELECT COUNT(*) FROM analyses")
            total = cursor.fetchone()[0]
            
            # Get paginated results
            cursor = conn.execute("""
                SELECT * FROM analyses 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """, (limit, skip))
            
            analyses = [self._row_to_analysis(row) for row in cursor.fetchall()]
            
            return analyses, total
    
    def _row_to_analysis(self, row: sqlite3.Row) -> AnalysisDetail:
        """Convert database row to AnalysisDetail."""
        # Deserialize JSON fields
        model = None
        if row["model_json"]:
            model = StructuralModel.model_validate_json(row["model_json"])
        
        results = None
        if row["results_json"]:
            results = AnalysisResults.model_validate_json(row["results_json"])
        
        loads = []
        if row["loads_json"]:
            loads_data = json.loads(row["loads_json"])
            loads = [Load.model_validate(load) for load in loads_data]
        
        return AnalysisDetail(
            analysis_id=row["analysis_id"],
            status=row["status"],
            material=row["material"],
            scale_factor=row["scale_factor"],
            detection_method=row["detection_method"],
            model=model,
            results=results,
            loads=loads,
            error=row["error"]
        )
    
    def delete_analysis(self, analysis_id: str) -> bool:
        """Delete an analysis by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM analyses WHERE analysis_id = ?",
                (analysis_id,)
            )
            conn.commit()
            return cursor.rowcount > 0


# Global database instance
_db: Optional[Database] = None


def get_database() -> Database:
    """Get or create global database instance."""
    global _db
    if _db is None:
        # Extract path from database URL
        db_url = settings.database_url
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
        else:
            db_path = "analyses.db"
        
        _db = Database(db_path)
    
    return _db
