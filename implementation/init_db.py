from __future__ import annotations

import sqlite3
from pathlib import Path

try:
    from .db import DEFAULT_DB_PATH
except ImportError:  # Allows running this file directly.
    from db import DEFAULT_DB_PATH


SCHEMA_SQL = """
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS students;

CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    cohort TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    score REAL NOT NULL CHECK (score >= 0 AND score <= 100),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    credits INTEGER NOT NULL CHECK (credits > 0)
);

CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    grade REAL NOT NULL CHECK (grade >= 0 AND grade <= 100),
    status TEXT NOT NULL CHECK (status IN ('enrolled', 'completed', 'dropped')),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE(student_id, course_id)
);
"""

SEED_SQL = """
INSERT INTO students (name, cohort, email, score, active) VALUES
    ('Nguyen An', 'A1', 'an.nguyen@example.com', 88.5, 1),
    ('Tran Binh', 'A1', 'binh.tran@example.com', 91.0, 1),
    ('Le Chi', 'A2', 'chi.le@example.com', 76.25, 1),
    ('Pham Dung', 'A2', 'dung.pham@example.com', 82.0, 0),
    ('Vu Huy', 'A1', 'huy.vu@example.com', 95.5, 1);

INSERT INTO courses (code, title, credits) VALUES
    ('MCP101', 'Model Context Protocol Basics', 3),
    ('SQL201', 'Safe SQL for Applications', 4),
    ('PY150', 'Python Service Patterns', 3);

INSERT INTO enrollments (student_id, course_id, grade, status) VALUES
    (1, 1, 87.0, 'completed'),
    (1, 2, 90.0, 'enrolled'),
    (2, 1, 92.0, 'completed'),
    (2, 3, 89.0, 'enrolled'),
    (3, 2, 78.5, 'completed'),
    (4, 1, 80.0, 'dropped'),
    (5, 1, 96.0, 'completed'),
    (5, 2, 94.0, 'completed'),
    (5, 3, 97.5, 'enrolled');
"""


def create_database(db_path: str | Path = DEFAULT_DB_PATH) -> Path:
    """Create a fresh SQLite database with deterministic schema and seed data."""

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_SQL)
        conn.executescript(SEED_SQL)
        conn.commit()

    return db_path


if __name__ == "__main__":
    path = create_database()
    print(f"Created database at {path}")
