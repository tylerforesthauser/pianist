"""
Musical reference database for storing and retrieving composition examples.

This module provides a database of musical examples that can be used to guide
AI expansion, including motif development, phrase expansion, transitions, and
form examples.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schema import Composition


@dataclass
class MusicalReference:
    """A musical reference example."""
    id: str
    title: str
    description: str
    composition: Composition
    style: str | None = None  # Baroque, Classical, Romantic, Modern, etc.
    form: str | None = None  # binary, ternary, sonata, etc.
    techniques: list[str] | None = None  # sequence, inversion, augmentation, etc.
    metadata: dict[str, Any] | None = None  # Additional metadata


class ReferenceDatabase:
    """Database for storing and retrieving musical references."""
    
    def __init__(self, db_path: Path | str | None = None) -> None:
        """
        Initialize the reference database.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            # Default: ~/.pianist/references.db
            default_dir = Path.home() / ".pianist"
            default_dir.mkdir(parents=True, exist_ok=True)
            db_path = default_dir / "references.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS musical_references (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                style TEXT,
                form TEXT,
                techniques TEXT,  -- JSON array of technique names
                composition_json TEXT NOT NULL,  -- Full composition JSON
                metadata TEXT,  -- JSON object for additional metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for faster searching
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_style ON musical_references(style)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_form ON musical_references(form)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_title ON musical_references(title)
        """)
        
        conn.commit()
        conn.close()
    
    def add_reference(self, reference: MusicalReference) -> None:
        """
        Add a musical reference to the database.
        
        Args:
            reference: The musical reference to add
        """
        from .iterate import composition_to_canonical_json
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        composition_json = composition_to_canonical_json(reference.composition)
        techniques_json = json.dumps(reference.techniques) if reference.techniques else None
        metadata_json = json.dumps(reference.metadata) if reference.metadata else None
        
        cursor.execute("""
            INSERT OR REPLACE INTO musical_references 
            (id, title, description, style, form, techniques, composition_json, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            reference.id,
            reference.title,
            reference.description,
            reference.style,
            reference.form,
            techniques_json,
            composition_json,
            metadata_json,
        ))
        
        conn.commit()
        conn.close()
    
    def get_reference(self, reference_id: str) -> MusicalReference | None:
        """
        Retrieve a musical reference by ID.
        
        Args:
            reference_id: The ID of the reference to retrieve
        
        Returns:
            The musical reference, or None if not found
        """
        from .parser import parse_composition_from_text
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, description, style, form, techniques, composition_json, metadata
            FROM musical_references
            WHERE id = ?
        """, (reference_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        id_val, title, description, style, form, techniques_json, composition_json, metadata_json = row
        
        techniques = json.loads(techniques_json) if techniques_json else None
        metadata = json.loads(metadata_json) if metadata_json else None
        
        composition = parse_composition_from_text(composition_json)
        
        return MusicalReference(
            id=id_val,
            title=title,
            description=description,
            style=style,
            form=form,
            techniques=techniques,
            composition=composition,
            metadata=metadata,
        )
    
    def search_references(
        self,
        style: str | None = None,
        form: str | None = None,
        technique: str | None = None,
        title_contains: str | None = None,
        description_contains: str | None = None,
        limit: int = 10
    ) -> list[MusicalReference]:
        """
        Search for musical references matching criteria.
        
        Args:
            style: Filter by musical style
            form: Filter by musical form
            technique: Filter by technique (must be in techniques list)
            title_contains: Filter by title substring
            description_contains: Filter by description substring
            limit: Maximum number of results to return
        
        Returns:
            List of matching musical references
        """
        from .parser import parse_composition_from_text
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT id, title, description, style, form, techniques, composition_json, metadata FROM musical_references WHERE 1=1"
        params: list[Any] = []
        
        if style:
            query += " AND style = ?"
            params.append(style)
        
        if form:
            query += " AND form = ?"
            params.append(form)
        
        if technique:
            # Search for technique in JSON array
            query += " AND techniques LIKE ?"
            params.append(f'%"{technique}"%')
        
        if title_contains:
            query += " AND title LIKE ?"
            params.append(f"%{title_contains}%")
        
        if description_contains:
            query += " AND description LIKE ?"
            params.append(f"%{description_contains}%")
        
        query += " LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        references: list[MusicalReference] = []
        for row in rows:
            id_val, title, description, style_val, form_val, techniques_json, composition_json, metadata_json = row
            
            techniques = json.loads(techniques_json) if techniques_json else None
            metadata = json.loads(metadata_json) if metadata_json else None
            
            composition = parse_composition_from_text(composition_json)
            
            references.append(MusicalReference(
                id=id_val,
                title=title,
                description=description,
                style=style_val,
                form=form_val,
                techniques=techniques,
                composition=composition,
                metadata=metadata,
            ))
        
        return references
    
    def find_relevant_references(
        self,
        composition: Composition,
        analysis: Any | None = None,  # MusicalAnalysis type
        limit: int = 5
    ) -> list[MusicalReference]:
        """
        Find relevant references for a given composition based on analysis.
        
        This is a simple implementation that matches by form and style.
        More sophisticated matching can be added later.
        
        Args:
            composition: The composition to find references for
            analysis: Optional musical analysis results
            limit: Maximum number of references to return
        
        Returns:
            List of relevant musical references
        """
        # Try to match by form if detected
        form = None
        if analysis and hasattr(analysis, 'form') and analysis.form:
            form = analysis.form.lower()
        
        # Try to match by key signature (style inference)
        style = None
        if composition.key_signature:
            # Simple heuristic: major keys might suggest Classical/Romantic
            # This is very basic and should be enhanced
            if "major" in composition.key_signature.lower():
                style = "Classical"  # Default assumption
        
        # Search for references
        references = self.search_references(
            style=style,
            form=form,
            limit=limit
        )
        
        # If no matches, return any references
        if not references:
            references = self.search_references(limit=limit)
        
        return references
    
    def list_all_references(self) -> list[MusicalReference]:
        """
        List all references in the database.
        
        Returns:
            List of all musical references
        """
        return self.search_references(limit=1000)
    
    def delete_reference(self, reference_id: str) -> bool:
        """
        Delete a reference from the database.
        
        Args:
            reference_id: The ID of the reference to delete
        
        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM musical_references WHERE id = ?", (reference_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def count_references(self) -> int:
        """
        Get the total number of references in the database.
        
        Returns:
            Number of references
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM musical_references")
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return count


def get_default_database() -> ReferenceDatabase:
    """Get the default reference database instance."""
    return ReferenceDatabase()

