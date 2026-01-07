"""
Musical reference database for storing and retrieving composition examples.

This module provides a database of musical examples that can be used to guide
AI expansion, including motif development, phrase expansion, transitions, and
form examples.

The database stores enhanced metadata from the review and normalization scripts,
including quality scores, musical analysis (key, tempo, motif/phrase counts),
and harmonic progressions for improved search and relevance matching.
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
    """A musical reference example with comprehensive metadata."""
    id: str
    title: str
    description: str
    composition: Composition
    style: str | None = None  # Baroque, Classical, Romantic, Modern, etc.
    form: str | None = None  # binary, ternary, sonata, etc.
    techniques: list[str] | None = None  # sequence, inversion, augmentation, etc.
    metadata: dict[str, Any] | None = None  # Additional custom metadata
    
    # Musical analysis metadata (from review script)
    detected_key: str | None = None
    tempo_bpm: float | None = None
    duration_beats: float | None = None
    quality_score: float | None = None
    technical_score: float | None = None
    musical_score: float | None = None
    structure_score: float | None = None
    motif_count: int | None = None
    phrase_count: int | None = None
    chord_count: int | None = None
    harmonic_progression: str | None = None  # First 10 chords as space-separated string
    time_signature: str | None = None
    bars: float | None = None


class ReferenceDatabase:
    """
    Database for storing and retrieving musical references.
    
    Provides enhanced search capabilities using musical metadata including
    key signatures, tempo, quality scores, and harmonic progressions.
    """
    
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
                techniques TEXT,
                composition_json TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                detected_key TEXT,
                tempo_bpm REAL,
                duration_beats REAL,
                quality_score REAL,
                technical_score REAL,
                musical_score REAL,
                structure_score REAL,
                motif_count INTEGER,
                phrase_count INTEGER,
                chord_count INTEGER,
                harmonic_progression TEXT,
                time_signature TEXT,
                bars REAL
            )
        """)
        
        # Create indexes for faster searching
        indexes = [
            ("idx_style", "style"),
            ("idx_form", "form"),
            ("idx_title", "title"),
            ("idx_key", "detected_key"),
            ("idx_quality", "quality_score"),
            ("idx_tempo", "tempo_bpm"),
        ]
        
        for idx_name, column in indexes:
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS {idx_name} ON musical_references({column})
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
        
        # Limit harmonic progression to first 10 chords
        harmonic_prog = reference.harmonic_progression
        if harmonic_prog:
            harmonic_prog = " ".join(harmonic_prog.split()[:10])
        
        cursor.execute("""
            INSERT OR REPLACE INTO musical_references 
            (id, title, description, style, form, techniques, composition_json, metadata,
             detected_key, tempo_bpm, duration_beats, quality_score, technical_score,
             musical_score, structure_score, motif_count, phrase_count, chord_count,
             harmonic_progression, time_signature, bars)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            reference.id,
            reference.title,
            reference.description,
            reference.style,
            reference.form,
            techniques_json,
            composition_json,
            metadata_json,
            reference.detected_key,
            reference.tempo_bpm,
            reference.duration_beats,
            reference.quality_score,
            reference.technical_score,
            reference.musical_score,
            reference.structure_score,
            reference.motif_count,
            reference.phrase_count,
            reference.chord_count,
            harmonic_prog,
            reference.time_signature,
            reference.bars,
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
            SELECT id, title, description, style, form, techniques, composition_json, metadata,
                   detected_key, tempo_bpm, duration_beats, quality_score, technical_score,
                   musical_score, structure_score, motif_count, phrase_count, chord_count,
                   harmonic_progression, time_signature, bars
            FROM musical_references
            WHERE id = ?
        """, (reference_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        (id_val, title, description, style, form, techniques_json, composition_json, metadata_json,
         detected_key, tempo_bpm, duration_beats, quality_score, technical_score,
         musical_score, structure_score, motif_count, phrase_count, chord_count,
         harmonic_progression, time_signature, bars) = row
        
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
            detected_key=detected_key,
            tempo_bpm=tempo_bpm,
            duration_beats=duration_beats,
            quality_score=quality_score,
            technical_score=technical_score,
            musical_score=musical_score,
            structure_score=structure_score,
            motif_count=motif_count,
            phrase_count=phrase_count,
            chord_count=chord_count,
            harmonic_progression=harmonic_progression,
            time_signature=time_signature,
            bars=bars,
        )
    
    def search_references(
        self,
        style: str | None = None,
        form: str | None = None,
        technique: str | None = None,
        title_contains: str | None = None,
        description_contains: str | None = None,
        key: str | None = None,
        key_base_only: bool = False,  # Match base key (C) ignoring mode (major/minor)
        tempo_min: float | None = None,
        tempo_max: float | None = None,
        min_quality: float | None = None,
        min_motif_count: int | None = None,
        min_phrase_count: int | None = None,
        limit: int = 10,
        order_by_quality: bool = False,  # Rank by quality score
    ) -> list[MusicalReference]:
        """
        Enhanced search for musical references matching criteria.
        
        Args:
            style: Filter by musical style
            form: Filter by musical form
            technique: Filter by technique (must be in techniques list)
            title_contains: Filter by title substring
            description_contains: Filter by description substring
            key: Filter by detected key (exact match)
            key_base_only: If True, match base key only (C matches C major and C minor)
            tempo_min: Minimum tempo (BPM)
            tempo_max: Maximum tempo (BPM)
            min_quality: Minimum quality score
            min_motif_count: Minimum motif count
            min_phrase_count: Minimum phrase count
            limit: Maximum number of results
            order_by_quality: Rank results by quality score (descending)
        
        Returns:
            List of matching musical references
        """
        from .parser import parse_composition_from_text
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT id, title, description, style, form, techniques, composition_json, metadata,
                   detected_key, tempo_bpm, duration_beats, quality_score, technical_score,
                   musical_score, structure_score, motif_count, phrase_count, chord_count,
                   harmonic_progression, time_signature, bars
            FROM musical_references WHERE 1=1
        """
        params: list[Any] = []
        
        if style:
            query += " AND style = ?"
            params.append(style)
        
        if form:
            query += " AND form = ?"
            params.append(form)
        
        if technique:
            query += " AND techniques LIKE ?"
            params.append(f'%"{technique}"%')
        
        if title_contains:
            query += " AND title LIKE ?"
            params.append(f"%{title_contains}%")
        
        if description_contains:
            query += " AND description LIKE ?"
            params.append(f"%{description_contains}%")
        
        if key:
            if key_base_only:
                # Match base key (e.g., "C" matches "C major" and "C minor")
                query += " AND (detected_key = ? OR detected_key LIKE ?)"
                params.extend([key, f"{key} %"])
            else:
                query += " AND detected_key = ?"
                params.append(key)
        
        if tempo_min is not None:
            query += " AND tempo_bpm >= ?"
            params.append(tempo_min)
        
        if tempo_max is not None:
            query += " AND tempo_bpm <= ?"
            params.append(tempo_max)
        
        if min_quality is not None:
            query += " AND quality_score >= ?"
            params.append(min_quality)
        
        if min_motif_count is not None:
            query += " AND motif_count >= ?"
            params.append(min_motif_count)
        
        if min_phrase_count is not None:
            query += " AND phrase_count >= ?"
            params.append(min_phrase_count)
        
        if order_by_quality:
            query += " ORDER BY quality_score DESC"
        
        query += " LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        references: list[MusicalReference] = []
        for row in rows:
            (id_val, title, description, style_val, form_val, techniques_json, composition_json, metadata_json,
             detected_key, tempo_bpm, duration_beats, quality_score, technical_score,
             musical_score, structure_score, motif_count, phrase_count, chord_count,
             harmonic_progression, time_signature, bars) = row
            
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
                detected_key=detected_key,
                tempo_bpm=tempo_bpm,
                duration_beats=duration_beats,
                quality_score=quality_score,
                technical_score=technical_score,
                musical_score=musical_score,
                structure_score=structure_score,
                motif_count=motif_count,
                phrase_count=phrase_count,
                chord_count=chord_count,
                harmonic_progression=harmonic_progression,
                time_signature=time_signature,
                bars=bars,
            ))
        
        return references
    
    def find_relevant_references(
        self,
        composition: Composition,
        analysis: Any | None = None,  # MusicalAnalysis type
        limit: int = 5,
        min_quality: float = 0.7,
    ) -> list[MusicalReference]:
        """
        Find relevant references using enhanced musical similarity matching.
        
        Enhanced matching considers:
        - Key (exact match preferred, then base key)
        - Form (from analysis)
        - Style (from analysis if available)
        - Harmonic progression similarity
        - Quality scores
        
        Args:
            composition: The composition to find references for
            analysis: Optional musical analysis results
            limit: Maximum number of references to return
            min_quality: Minimum quality score for references
        
        Returns:
            List of relevant musical references, ranked by relevance
        """
        # Extract matching criteria from analysis
        form = None
        detected_key = None
        style = None
        harmonic_progression = None
        
        if analysis:
            if hasattr(analysis, 'form') and analysis.form:
                form = analysis.form.lower()
            if hasattr(analysis, 'harmonic_progression') and analysis.harmonic_progression:
                if hasattr(analysis.harmonic_progression, 'key'):
                    detected_key = analysis.harmonic_progression.key
                if hasattr(analysis.harmonic_progression, 'progression'):
                    prog = analysis.harmonic_progression.progression
                    if prog:
                        harmonic_progression = " ".join(str(c) for c in prog[:10])
        
        # Try to get key from composition if not in analysis
        if not detected_key and composition.key_signature:
            detected_key = composition.key_signature
        
        # Search with multiple strategies, ranked by relevance
        candidates: list[tuple[MusicalReference, float]] = []
        seen_ids: set[str] = set()
        
        # Strategy 1: Exact key + form + style match (highest priority)
        if detected_key and form:
            exact_matches = self.search_references(
                key=detected_key,
                form=form,
                style=style,
                min_quality=min_quality,
                limit=limit * 2,
                order_by_quality=True,
            )
            for ref in exact_matches:
                if ref.id not in seen_ids:
                    score = 1.0
                    if ref.quality_score:
                        score += ref.quality_score * 0.1  # Boost by quality
                    candidates.append((ref, score))
                    seen_ids.add(ref.id)
        
        # Strategy 2: Base key match + form (high priority)
        if detected_key and form and len(candidates) < limit:
            base_key = detected_key.split()[0] if ' ' in detected_key else detected_key
            base_matches = self.search_references(
                key=base_key,
                key_base_only=True,
                form=form,
                min_quality=min_quality,
                limit=limit * 2,
                order_by_quality=True,
            )
            for ref in base_matches:
                if ref.id not in seen_ids:
                    score = 0.8
                    if ref.quality_score:
                        score += ref.quality_score * 0.1
                    candidates.append((ref, score))
                    seen_ids.add(ref.id)
        
        # Strategy 3: Key match only
        if detected_key and len(candidates) < limit:
            key_matches = self.search_references(
                key=detected_key,
                min_quality=min_quality,
                limit=limit * 2,
                order_by_quality=True,
            )
            for ref in key_matches:
                if ref.id not in seen_ids:
                    score = 0.6
                    if ref.quality_score:
                        score += ref.quality_score * 0.1
                    candidates.append((ref, score))
                    seen_ids.add(ref.id)
        
        # Strategy 4: Form match only
        if form and len(candidates) < limit:
            form_matches = self.search_references(
                form=form,
                min_quality=min_quality,
                limit=limit * 2,
                order_by_quality=True,
            )
            for ref in form_matches:
                if ref.id not in seen_ids:
                    score = 0.5
                    if ref.quality_score:
                        score += ref.quality_score * 0.1
                    candidates.append((ref, score))
                    seen_ids.add(ref.id)
        
        # Strategy 5: Harmonic progression similarity (if available)
        if harmonic_progression and len(candidates) < limit:
            # Get all high-quality references for comparison
            all_refs = self.search_references(
                min_quality=min_quality,
                limit=50,
                order_by_quality=True,
            )
            
            query_prog = set(harmonic_progression.split()[:10])
            for ref in all_refs:
                if ref.id in seen_ids or not ref.harmonic_progression:
                    continue
                
                ref_prog = set(ref.harmonic_progression.split()[:10])
                if not ref_prog:
                    continue
                
                # Calculate overlap
                overlap = len(query_prog & ref_prog) / max(len(query_prog), len(ref_prog), 1)
                if overlap > 0.3:  # At least 30% overlap
                    score = 0.4 + overlap * 0.3
                    if ref.quality_score:
                        score += ref.quality_score * 0.1
                    candidates.append((ref, score))
                    seen_ids.add(ref.id)
        
        # Strategy 6: Any high-quality references (fallback)
        if len(candidates) < limit:
            fallback = self.search_references(
                min_quality=min_quality,
                limit=limit,
                order_by_quality=True,
            )
            for ref in fallback:
                if ref.id not in seen_ids:
                    score = 0.3
                    if ref.quality_score:
                        score += ref.quality_score * 0.1
                    candidates.append((ref, score))
                    seen_ids.add(ref.id)
        
        # Sort by relevance score and return top results
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [ref for ref, _ in candidates[:limit]]
    
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
    
    def get_coverage(self) -> dict[str, Any]:
        """
        Get coverage statistics by style, form, and technique.
        
        Returns:
            Dictionary with coverage statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        coverage: dict[str, Any] = {
            'by_style': {},
            'by_form': {},
            'by_technique': {},
            'quality_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'total': 0,
        }
        
        # Count by style
        cursor.execute("SELECT style, COUNT(*) FROM musical_references WHERE style IS NOT NULL GROUP BY style")
        for style, count in cursor.fetchall():
            coverage['by_style'][style] = count
        
        # Count by form
        cursor.execute("SELECT form, COUNT(*) FROM musical_references WHERE form IS NOT NULL GROUP BY form")
        for form, count in cursor.fetchall():
            coverage['by_form'][form] = count
        
        # Count by technique (from JSON array)
        cursor.execute("SELECT techniques FROM musical_references WHERE techniques IS NOT NULL")
        technique_counts: dict[str, int] = {}
        for (techniques_json,) in cursor.fetchall():
            try:
                techniques = json.loads(techniques_json)
                if isinstance(techniques, list):
                    for tech in techniques:
                        technique_counts[tech] = technique_counts.get(tech, 0) + 1
            except (json.JSONDecodeError, TypeError):
                continue
        coverage['by_technique'] = technique_counts
        
        # Quality distribution
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN quality_score >= 0.8 THEN 1 ELSE 0 END) as high,
                SUM(CASE WHEN quality_score >= 0.6 AND quality_score < 0.8 THEN 1 ELSE 0 END) as medium,
                SUM(CASE WHEN quality_score < 0.6 THEN 1 ELSE 0 END) as low
            FROM musical_references
            WHERE quality_score IS NOT NULL
        """)
        row = cursor.fetchone()
        if row:
            coverage['quality_distribution'] = {
                'high': row[0] or 0,
                'medium': row[1] or 0,
                'low': row[2] or 0,
            }
        
        # Total count
        cursor.execute("SELECT COUNT(*) FROM musical_references")
        coverage['total'] = cursor.fetchone()[0]
        
        conn.close()
        return coverage


def get_default_database() -> ReferenceDatabase:
    """Get the default reference database instance."""
    return ReferenceDatabase()

