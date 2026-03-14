"""Firestore-based session tracking for YHTBT Phone Booth callers."""

from google.cloud import firestore
import uuid
from datetime import datetime


db = firestore.Client()
COLLECTION = "yhtbt_callers"


def get_or_create_caller(anonymous_id: str) -> dict:
    """Fetch caller history from Firestore, or create new record."""
    doc_ref = db.collection(COLLECTION).document(anonymous_id)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict()

    # New caller
    caller_data = {
        "anonymous_id": anonymous_id,
        "cycles_completed": [],
        "branch_cycle_2": None,
        "branch_cycle_6": None,
        "numbers_dialed": [],
        "door_offered": False,
        "door_accepted": False,
        "returning_caller": False,
        "created_at": datetime.utcnow().isoformat(),
        "last_call_at": datetime.utcnow().isoformat(),
    }
    doc_ref.set(caller_data)
    return caller_data


def update_caller(anonymous_id: str, updates: dict):
    """Update caller record in Firestore."""
    doc_ref = db.collection(COLLECTION).document(anonymous_id)
    updates["last_call_at"] = datetime.utcnow().isoformat()
    doc_ref.update(updates)


def log_event(anonymous_id: str, event_name: str, details: dict = None):
    """Log a caller event to Firestore."""
    db.collection(COLLECTION).document(anonymous_id).collection("events").add({
        "event_name": event_name,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat(),
    })


def mark_returning(anonymous_id: str):
    """Mark caller as returning."""
    update_caller(anonymous_id, {"returning_caller": True})


def complete_cycle(anonymous_id: str, cycle: int):
    """Record a completed cycle."""
    doc_ref = db.collection(COLLECTION).document(anonymous_id)
    doc_ref.update({
        "cycles_completed": firestore.ArrayUnion([cycle]),
    })
    log_event(anonymous_id, "cycle_completed", {"cycle": cycle})


def record_branch(anonymous_id: str, branch: str):
    """Record which branch the caller took (2A, 2B, 6A, 6B)."""
    if branch in ("2A", "2B"):
        update_caller(anonymous_id, {"branch_cycle_2": branch})
    elif branch in ("6A", "6B"):
        update_caller(anonymous_id, {"branch_cycle_6": branch})
    log_event(anonymous_id, "branch_taken", {"branch": branch})


def record_number_dialed(anonymous_id: str, number: str):
    """Record a directory number the caller dialed."""
    doc_ref = db.collection(COLLECTION).document(anonymous_id)
    doc_ref.update({
        "numbers_dialed": firestore.ArrayUnion([number]),
    })
    log_event(anonymous_id, "number_dialed", {"number": number})


def format_session_context(caller_data: dict) -> str:
    """Format caller data into a context string for the agent."""
    cycles = caller_data.get("cycles_completed", [])
    if not cycles:
        return "This is a new caller. They have not spoken to you before. Begin with the opening sequence."

    context = "CALLER SESSION DATA - READ BEFORE SPEAKING:\n"
    context += f"This is a RETURNING caller. They have talked to you before.\n"
    context += f"Cycles completed: {cycles}\n"

    branch_2 = caller_data.get("branch_cycle_2")
    if branch_2:
        context += f"At Cycle 2, they took branch: {branch_2}\n"

    branch_6 = caller_data.get("branch_cycle_6")
    if branch_6:
        context += f"At Cycle 6, they took branch: {branch_6}\n"

    numbers = caller_data.get("numbers_dialed", [])
    if numbers:
        context += f"Numbers they have dialed: {numbers}\n"

    door_offered = caller_data.get("door_offered", False)
    door_accepted = caller_data.get("door_accepted", False)
    if door_offered:
        context += f"The door (757) has been offered. Accepted: {door_accepted}\n"

    # Figure out what cycle they should be on next
    max_cycle = max(cycles) if cycles else 0
    context += f"\nPick up where they left off. Their next cycle is {max_cycle + 1}. "
    context += "Do NOT redo the opening sequence. Do NOT re-recruit them. "
    context += "Acknowledge they are back and ask what they heard on the last set of numbers you gave them."

    return context