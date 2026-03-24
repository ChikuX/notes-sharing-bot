"""
Storage Service Layer — Supabase Storage ONLY (for PDF file uploads).
NO database operations here. All DB work is in db_service.py (Neon PostgreSQL).
"""
import uuid
import aiohttp
from src.core.config import config


async def upload_pdf(file_bytes: bytes, file_name: str) -> str:
    """
    Upload a PDF to Supabase Storage bucket.
    Returns the public URL of the uploaded file.

    Uses: SUPABASE_URL, SUPABASE_KEY, SUPABASE_BUCKET from config.
    """
    bucket = config.SUPABASE_BUCKET  # e.g. "notes"
    storage_path = f"{bucket}/{file_name}"

    url = f"{config.SUPABASE_URL}/storage/v1/object/{storage_path}"

    headers = {
        "apikey": config.SUPABASE_KEY,
        "Authorization": f"Bearer {config.SUPABASE_KEY}",
        "Content-Type": "application/pdf",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=file_bytes) as resp:
            if resp.status not in (200, 201):
                error_text = await resp.text()
                raise Exception(f"Supabase storage upload failed ({resp.status}): {error_text}")

    return get_public_url(storage_path)


def get_public_url(storage_path: str) -> str:
    """Return public URL for a file in Supabase Storage."""
    return f"{config.SUPABASE_URL}/storage/v1/object/public/{storage_path}"


def build_file_name(course: str, subject: str) -> str:
    """
    Build a sanitized file path for storage.
    Format: {course}/{subject}/{uuid}.pdf
    """
    course_clean = course.strip().replace(" ", "_").lower()
    subject_clean = subject.strip().replace(" ", "_").lower()
    return f"{course_clean}/{subject_clean}/{uuid.uuid4()}.pdf"
