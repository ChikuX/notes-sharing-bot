"""
Database Service Layer — Neon PostgreSQL via asyncpg.
NO Supabase DB usage. All data is stored in Neon PostgreSQL.
"""
import asyncpg
import uuid
from src.core.config import config

pool: asyncpg.Pool = None


# ─── Connection lifecycle ─────────────────────────────────────

async def connect_db():
    """Create asyncpg connection pool and ensure tables exist."""
    global pool
    pool = await asyncpg.create_pool(dsn=config.DATABASE_URL, min_size=2, max_size=10)
    await _ensure_tables()


async def close_db():
    """Close connection pool."""
    global pool
    if pool:
        await pool.close()


async def _ensure_tables():
    """Create tables if they don't exist, and migrate existing tables (Neon PostgreSQL)."""
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id BIGINT PRIMARY KEY,
                name TEXT,
                roll_no TEXT,
                course TEXT,
                department TEXT,
                semester TEXT,
                session TEXT,
                language TEXT DEFAULT 'en',
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                uploaded_by BIGINT,
                file_id TEXT,
                file_url TEXT,
                subject TEXT,
                display_name TEXT,
                display_course TEXT,
                display_department TEXT,
                display_semester TEXT,
                display_session TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pyqs (
                id SERIAL PRIMARY KEY,
                display_name TEXT,
                display_course TEXT,
                display_department TEXT NULL,
                display_semester INT,
                year INT,
                file_url TEXT,
                status TEXT,
                subject TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS upload_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id BIGINT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        # ── Migrations: add missing columns to existing tables ──
        migrations = [
            "ALTER TABLE notes ADD COLUMN IF NOT EXISTS file_id TEXT",
            "ALTER TABLE notes ADD COLUMN IF NOT EXISTS file_url TEXT",
            "ALTER TABLE notes ADD COLUMN IF NOT EXISTS display_session TEXT",
            "ALTER TABLE notes ADD COLUMN IF NOT EXISTS display_semester TEXT",
        ]
        for sql in migrations:
            try:
                await conn.execute(sql)
            except Exception:
                pass  # column already exists


# ─── User operations (Neon PostgreSQL) ────────────────────────

async def get_user(telegram_id: int) -> dict | None:
    """Fetch user from Neon DB by telegram_id."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE telegram_id = $1", telegram_id
        )
        return dict(row) if row else None


async def create_user(
    telegram_id: int,
    name: str,
    roll_no: str,
    course: str,
    department: str | None,
    semester: str,
    session: str,
    language: str = "en",
):
    """Insert or update user profile in Neon DB."""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (telegram_id, name, roll_no, course, department, semester, session, language)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (telegram_id)
            DO UPDATE SET name=$2, roll_no=$3, course=$4, department=$5, semester=$6, session=$7
            """,
            telegram_id, name, roll_no, course, department, semester, session, language,
        )


async def update_user_language(telegram_id: int, language: str):
    """Update user language in Neon DB. Creates minimal record if user doesn't exist."""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (telegram_id, language)
            VALUES ($1, $2)
            ON CONFLICT (telegram_id) DO UPDATE SET language=$2
            """,
            telegram_id, language,
        )


async def get_user_language(telegram_id: int) -> str:
    """Get user language from Neon DB, default 'en'."""
    async with pool.acquire() as conn:
        row = await conn.fetchval(
            "SELECT language FROM users WHERE telegram_id = $1", telegram_id
        )
        return row or "en"


# ─── Upload Logs (Daily Limits) operations ────────────────────

async def get_daily_upload_count(telegram_id: int) -> int:
    """Get number of uploads by user in the last 24 hours."""
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM upload_logs WHERE user_id = $1 AND created_at >= NOW() - INTERVAL '24 hours'",
            telegram_id
        )
        return count or 0


async def add_upload_log(telegram_id: int):
    """Log an upload attempt for rate limiting."""
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO upload_logs (user_id) VALUES ($1)",
            telegram_id
        )


# ─── Notes operations (Neon PostgreSQL) ───────────────────────
# Notes are ONLY inserted AFTER admin approval.
# Rejected notes are NOT stored.

async def insert_note(
    uploaded_by: int,
    file_id: str,
    file_url: str,
    subject: str,
    display_name: str,
    display_course: str,
    display_department: str | None,
    display_semester: str,
    display_session: str,
    status: str = "approved",
) -> str:
    """
    Insert an APPROVED note into Neon DB.
    Called ONLY from admin approve handler.
    """
    note_id = str(uuid.uuid4())
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO notes (id, uploaded_by, file_id, file_url, subject, display_name,
                               display_course, display_department, display_semester, display_session, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
            note_id, uploaded_by, file_id, file_url, subject, display_name,
            display_course, display_department, display_semester, display_session, status,
        )
    return note_id


async def insert_pyq(
    file_url: str,
    subject: str,
    display_name: str,
    display_course: str,
    display_department: str | None,
    display_semester: str,
    year: str,
    status: str = "approved",
):
    """
    Insert an APPROVED PYQ into Neon DB.
    Called ONLY from admin approve handler.
    """
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO pyqs (file_url, subject, display_name, display_course,
                              display_department, display_semester, year, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            file_url, subject, display_name, display_course,
            display_department, int(display_semester), int(year), status,
        )


async def update_note_status(note_id: str, status: str):
    """Generic status update in Neon DB."""
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE notes SET status=$1 WHERE id=$2", status, note_id
        )


async def get_note(note_id: str) -> dict | None:
    """Fetch note from Neon DB by ID."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM notes WHERE id = $1", note_id)
        return dict(row) if row else None
