"""
Database module for KisanMitra AI.
Manages SQLite database connection and queries table initialization & operations.
"""

import sqlite3
import os
from typing import List, Dict, Optional, Any

DB_PATH = os.getenv("DATABASE_PATH") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "kisanmitra.db")


def get_db_connection() -> sqlite3.Connection:
    """Creates a connection to the SQLite database with Row factory."""
    db_path = os.getenv("DATABASE_PATH") or DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initializes the database and creates the queries table if it doesn't exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                question TEXT NOT NULL,
                response TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'hi',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def save_query(query_type: str, question: str, response: str, language: str = "hi") -> int:
    """
    Saves an interaction query to SQLite.
    Returns the newly inserted row ID.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO queries (type, question, response, language)
            VALUES (?, ?, ?, ?)
            """,
            (query_type, question, response, language),
        )
        conn.commit()
        return cursor.lastrowid


def get_queries(query_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieves queries ordered by newest first.
    Optionally filters by query_type ('chat', 'crop', 'weather', 'plant').
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if query_type and query_type.strip() and query_type.lower() != "all":
            cursor.execute(
                """
                SELECT id, type, question, response, language, created_at
                FROM queries
                WHERE type = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (query_type.lower(), limit),
            )
        else:
            cursor.execute(
                """
                SELECT id, type, question, response, language, created_at
                FROM queries
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def delete_query(query_id: int) -> bool:
    """
    Deletes a query by ID.
    Returns True if a record was deleted, False otherwise.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM queries WHERE id = ?", (query_id,))
        conn.commit()
        return cursor.rowcount > 0
