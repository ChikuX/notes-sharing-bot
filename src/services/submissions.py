"""
In-memory pending submissions store.
Holds submission metadata between user confirm and admin decision.
NO database, NO storage — just a dict keyed by submission UUID.

On bot restart, pending submissions are lost (admins ask users to resubmit).
"""

_store: dict[str, dict] = {}


def save(submission_id: str, data: dict):
    """Store a pending submission."""
    _store[submission_id] = data


def get(submission_id: str) -> dict | None:
    """Retrieve a pending submission."""
    return _store.get(submission_id)


def remove(submission_id: str):
    """Remove a submission after it's been processed."""
    _store.pop(submission_id, None)


def exists(submission_id: str) -> bool:
    """Check if a submission is still pending."""
    return submission_id in _store
