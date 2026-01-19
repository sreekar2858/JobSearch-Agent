"""
Document Database Manager - Handles storage of generated CVs and Cover Letters

This module provides functionality to store generated documents (CVs and cover letters)
in the database instead of text files, with proper relationships to job postings.
"""

import sqlite3
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


class DocumentDatabase:
    """Database manager for storing generated documents (CVs and Cover Letters)"""

    def __init__(self, db_path: str = "jobs/jobsearch.db"):
        """Initialize database connection and create tables if needed"""
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        # Enable WAL mode for better concurrent access
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.commit()
        self._create_tables()

    def _create_tables(self):
        """Create document storage tables"""
        # Create documents table for storing generated CVs and cover letters
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                document_type TEXT NOT NULL CHECK(document_type IN ('CV', 'COVER_LETTER')),
                content TEXT NOT NULL,
                state_json TEXT,
                metadata TEXT,
                process_id TEXT,
                company_name TEXT,
                job_title TEXT,
                template_used TEXT,
                generation_method TEXT DEFAULT 'AI_AGENT',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
            )
        """)

        # Create index for faster queries
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_job_id 
            ON documents(job_id)
        """)

        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_type 
            ON documents(document_type)
        """)

        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_process_id 
            ON documents(process_id)
        """)

        # Create document versions table for tracking revisions
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS document_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                version_number INTEGER NOT NULL,
                content TEXT NOT NULL,
                changes_summary TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
                UNIQUE(document_id, version_number)
            )
        """)

        self.conn.commit()

    def store_document(
        self,
        document_type: str,
        content: str,
        job_posting: Dict[str, Any] = None,
        job_id: int = None,
        state_json: str = None,
        process_id: str = None,
        template_used: str = None,
        metadata: Dict[str, Any] = None,
    ) -> int:
        """
        Store a generated document in the database

        Args:
            document_type: 'CV' or 'COVER_LETTER'
            content: The generated document content
            job_posting: Job posting data (if job_id not provided)
            job_id: Existing job ID in database
            state_json: Agent state information
            process_id: Process ID for tracking
            template_used: Template file used for generation
            metadata: Additional metadata

        Returns:
            Document ID of the stored document
        """
        if document_type not in ["CV", "COVER_LETTER"]:
            raise ValueError("document_type must be 'CV' or 'COVER_LETTER'")

        # Extract company and job title info
        company_name = None
        job_title = None

        if job_posting:
            company_name = (
                job_posting.get("company_name")
                or job_posting.get("company")
                or job_posting.get("company_title")
            )
            job_title = (
                job_posting.get("job_title")
                or job_posting.get("title")
                or job_posting.get("position_title")
            )

        # Convert metadata to JSON string
        metadata_json = json.dumps(metadata) if metadata else None

        try:
            with self.conn:
                cursor = self.conn.execute(
                    """
                    INSERT INTO documents (
                        job_id, document_type, content, state_json, metadata,
                        process_id, company_name, job_title, template_used
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        job_id,
                        document_type,
                        content,
                        state_json,
                        metadata_json,
                        process_id,
                        company_name,
                        job_title,
                        template_used,
                    ),
                )

                document_id = cursor.lastrowid

                # Create initial version
                self.conn.execute(
                    """
                    INSERT INTO document_versions (
                        document_id, version_number, content, changes_summary
                    ) VALUES (?, ?, ?, ?)
                """,
                    (document_id, 1, content, "Initial generation"),
                )

                print(
                    f"✅ Successfully stored {document_type} in database (ID: {document_id})"
                )
                return document_id

        except Exception as e:
            print(f"❌ Error storing document: {e}")
            raise

    def get_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Get a document by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_documents_by_job(self, job_id: int) -> List[Dict[str, Any]]:
        """Get all documents for a specific job"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM documents 
            WHERE job_id = ? 
            ORDER BY created_at DESC
        """,
            (job_id,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_documents_by_process(self, process_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a specific process"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM documents 
            WHERE process_id = ? 
            ORDER BY created_at DESC
        """,
            (process_id,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_recent_documents(
        self, document_type: str = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent documents with optional filtering by type"""
        cursor = self.conn.cursor()

        if document_type:
            cursor.execute(
                """
                SELECT * FROM documents 
                WHERE document_type = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """,
                (document_type, limit),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM documents 
                ORDER BY created_at DESC 
                LIMIT ?
            """,
                (limit,),
            )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def update_document_content(
        self, document_id: int, new_content: str, changes_summary: str = None
    ) -> bool:
        """Update document content and create a new version"""
        try:
            with self.conn:
                # Get current version number
                cursor = self.conn.cursor()
                cursor.execute(
                    """
                    SELECT MAX(version_number) FROM document_versions 
                    WHERE document_id = ?
                """,
                    (document_id,),
                )
                result = cursor.fetchone()
                current_version = result[0] if result[0] else 0
                new_version = current_version + 1

                # Update main document
                self.conn.execute(
                    """
                    UPDATE documents 
                    SET content = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """,
                    (new_content, document_id),
                )

                # Create new version
                self.conn.execute(
                    """
                    INSERT INTO document_versions (
                        document_id, version_number, content, changes_summary
                    ) VALUES (?, ?, ?, ?)
                """,
                    (
                        document_id,
                        new_version,
                        new_content,
                        changes_summary or f"Updated to version {new_version}",
                    ),
                )

                print(f"✅ Document {document_id} updated to version {new_version}")
                return True

        except Exception as e:
            print(f"❌ Error updating document: {e}")
            return False

    def get_document_versions(self, document_id: int) -> List[Dict[str, Any]]:
        """Get all versions of a document"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM document_versions 
            WHERE document_id = ? 
            ORDER BY version_number DESC
        """,
            (document_id,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def delete_document(self, document_id: int) -> bool:
        """Delete a document and all its versions"""
        try:
            with self.conn:
                self.conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
                print(f"✅ Document {document_id} deleted successfully")
                return True
        except Exception as e:
            print(f"❌ Error deleting document: {e}")
            return False

    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about stored documents"""
        cursor = self.conn.cursor()

        # Total documents by type
        cursor.execute("""
            SELECT document_type, COUNT(*) as count 
            FROM documents 
            GROUP BY document_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}

        # Documents by company (top 10)
        cursor.execute("""
            SELECT company_name, COUNT(*) as count 
            FROM documents 
            WHERE company_name IS NOT NULL 
            GROUP BY company_name 
            ORDER BY count DESC 
            LIMIT 10
        """)
        by_company = [{"company": row[0], "count": row[1]} for row in cursor.fetchall()]

        # Recent activity (last 7 days)
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count 
            FROM documents 
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY DATE(created_at) 
            ORDER BY date DESC
        """)
        recent_activity = [
            {"date": row[0], "count": row[1]} for row in cursor.fetchall()
        ]

        # Total counts
        cursor.execute("SELECT COUNT(*) FROM documents")
        total_documents = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(DISTINCT process_id) FROM documents WHERE process_id IS NOT NULL"
        )
        total_processes = cursor.fetchone()[0]

        return {
            "total_documents": total_documents,
            "total_processes": total_processes,
            "by_type": by_type,
            "by_company": by_company,
            "recent_activity": recent_activity,
        }

    def search_documents(
        self, keyword: str = None, company: str = None, document_type: str = None
    ) -> List[Dict[str, Any]]:
        """Search documents by keyword, company, or type"""
        cursor = self.conn.cursor()
        query = "SELECT * FROM documents WHERE 1=1"
        params = []

        if keyword:
            query += " AND (job_title LIKE ? OR company_name LIKE ? OR content LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])

        if company:
            query += " AND company_name LIKE ?"
            params.append(f"%{company}%")

        if document_type:
            query += " AND document_type = ?"
            params.append(document_type)

        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def export_document_to_file(
        self, document_id: int, output_dir: str = "output"
    ) -> str:
        """Export a document to a text file for backward compatibility"""
        document = self.get_document(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        os.makedirs(output_dir, exist_ok=True)

        # Generate filename
        doc_type = document["document_type"].lower()
        company = document.get("company_name", "unknown").replace(" ", "_")
        job_title = document.get("job_title", "job").replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"{company}_{job_title}_{doc_type}_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(document["content"])

        print(f"✅ Document exported to: {filepath}")
        return filepath

    def close(self):
        """Close the database connection"""
        self.conn.close()


class DocumentStorage:
    """
    Main class for handling document storage operations
    Provides a simple interface for the main API to use
    """

    @staticmethod
    def store_cv(
        content: str,
        job_posting: Dict[str, Any] = None,
        process_id: str = None,
        state_json: str = None,
        template_used: str = None,
    ) -> int:
        """Store a CV in the database"""
        db = DocumentDatabase()
        try:
            return db.store_document(
                document_type="CV",
                content=content,
                job_posting=job_posting,
                process_id=process_id,
                state_json=state_json,
                template_used=template_used,
            )
        finally:
            db.close()

    @staticmethod
    def store_cover_letter(
        content: str,
        job_posting: Dict[str, Any] = None,
        process_id: str = None,
        state_json: str = None,
        template_used: str = None,
    ) -> int:
        """Store a cover letter in the database"""
        db = DocumentDatabase()
        try:
            return db.store_document(
                document_type="COVER_LETTER",
                content=content,
                job_posting=job_posting,
                process_id=process_id,
                state_json=state_json,
                template_used=template_used,
            )
        finally:
            db.close()

    @staticmethod
    def get_documents_for_process(process_id: str) -> Dict[str, Any]:
        """Get all documents for a process, organized by type"""
        db = DocumentDatabase()
        try:
            documents = db.get_documents_by_process(process_id)
            result = {"cv": None, "cover_letter": None, "all_documents": documents}

            for doc in documents:
                if doc["document_type"] == "CV" and not result["cv"]:
                    result["cv"] = doc
                elif (
                    doc["document_type"] == "COVER_LETTER"
                    and not result["cover_letter"]
                ):
                    result["cover_letter"] = doc

            return result
        finally:
            db.close()

    @staticmethod
    def export_process_documents_to_files(
        process_id: str, output_dir: str = "output"
    ) -> Dict[str, str]:
        """Export all documents for a process to files (for backward compatibility)"""
        db = DocumentDatabase()
        try:
            documents = db.get_documents_by_process(process_id)
            exported_files = {}

            for doc in documents:
                filepath = db.export_document_to_file(doc["id"], output_dir)
                doc_type = doc["document_type"].lower()
                exported_files[doc_type] = filepath

            return exported_files
        finally:
            db.close()


# Example usage and testing functions
if __name__ == "__main__":
    # Example usage
    db = DocumentDatabase()

    # Example job posting data
    job_posting = {
        "company_name": "TechCorp",
        "job_title": "Senior Python Developer",
        "job_location": "Remote",
    }

    # Store a CV
    cv_id = db.store_document(
        document_type="CV",
        content="This is a sample CV content...",
        job_posting=job_posting,
        process_id="test_process_123",
        template_used="professional_cv.txt",
    )

    # Store a cover letter
    cl_id = db.store_document(
        document_type="COVER_LETTER",
        content="This is a sample cover letter content...",
        job_posting=job_posting,
        process_id="test_process_123",
        template_used="professional_cover_letter.txt",
    )

    # Get documents by process
    process_docs = db.get_documents_by_process("test_process_123")
    print(f"Found {len(process_docs)} documents for process")

    # Get statistics
    stats = db.get_document_stats()
    print("Document Statistics:", stats)

    db.close()
