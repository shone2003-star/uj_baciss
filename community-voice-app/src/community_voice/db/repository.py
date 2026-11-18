"""Reports and reviews in SQLite (plain sqlite3, no ORM)."""

import sqlite3
from contextlib import closing
from datetime import UTC, datetime

from community_voice.core.config import DB_PATH
from community_voice.schemas.chat import Message, Sender, Thread, ThreadSummary
from community_voice.schemas.review import ReportRecord, ReviewDecision
from community_voice.schemas.user import StoredUser, User

MAX_MESSAGES = 50  # per thread; protects the free AI tier and the screen


class ThreadNotFound(Exception):
    """The report has no conversation (it is not resolved yet)."""


class ThreadClosed(Exception):
    """The admin closed this conversation: nobody can write in it."""


class ThreadFull(Exception):
    """The conversation reached MAX_MESSAGES."""


# Statuses that still wait for a reviewer ("approved" waits for the draft decision).
PENDING = ("ready_for_review", "fast_track", "duplicate", "needs_human", "approved")

SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    status TEXT NOT NULL,
    category TEXT NOT NULL,
    urgency TEXT NOT NULL,
    municipality TEXT NOT NULL,
    department TEXT NOT NULL,
    duplicate_of TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT NOT NULL,
    action TEXT NOT NULL,
    category TEXT,
    urgency TEXT,
    department TEXT,
    note TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS report_owners (
    report_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS threads (
    report_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    marked_fixed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT NOT NULL,
    sender TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS drafts (
    report_id TEXT PRIMARY KEY,
    body TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return connection


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def save_report(
    report_id: str,
    text: str,
    status: str,
    category: str,
    urgency: str,
    municipality: str,
    department: str,
    duplicate_of: str | None = None,
) -> None:
    """Insert a report, or update it if the id exists."""
    now = _now()
    with closing(_connect()) as connection, connection:
        connection.execute(
            """
            INSERT INTO reports (id, text, status, category, urgency, municipality,
                                 department, duplicate_of, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status = excluded.status, category = excluded.category,
                urgency = excluded.urgency, municipality = excluded.municipality,
                department = excluded.department, duplicate_of = excluded.duplicate_of,
                updated_at = excluded.updated_at
            """,
            (
                report_id,
                text,
                status,
                category,
                urgency,
                municipality,
                department,
                duplicate_of,
                now,
                now,
            ),
        )


def get_report(report_id: str) -> ReportRecord | None:
    with closing(_connect()) as connection:
        row = connection.execute(
            "SELECT * FROM reports WHERE id = ?", (report_id,)
        ).fetchone()
    return ReportRecord(**dict(row)) if row else None


def list_pending() -> list[ReportRecord]:
    """Reports waiting for review, most urgent first."""
    marks = ", ".join("?" * len(PENDING))
    query = f"""
        SELECT * FROM reports WHERE status IN ({marks})
        ORDER BY CASE urgency WHEN 'critical' THEN 0 WHEN 'high' THEN 1
                              WHEN 'medium' THEN 2 ELSE 3 END, created_at
    """
    with closing(_connect()) as connection:
        rows = connection.execute(query, PENDING).fetchall()
    return [ReportRecord(**dict(row)) for row in rows]


def list_reports() -> list[ReportRecord]:
    """Every report, newest first."""
    with closing(_connect()) as connection:
        rows = connection.execute(
            "SELECT * FROM reports ORDER BY created_at DESC"
        ).fetchall()
    return [ReportRecord(**dict(row)) for row in rows]


def save_review(report_id: str, decision: ReviewDecision, status: str) -> None:
    """Record a review and apply its corrections to the report."""
    now = _now()
    category = decision.category.value if decision.category else None
    urgency = decision.urgency.value if decision.urgency else None
    with closing(_connect()) as connection, connection:
        connection.execute(
            """
            INSERT INTO reviews (report_id, action, category, urgency, department,
                                 note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                decision.action,
                category,
                urgency,
                decision.department,
                decision.note,
                now,
            ),
        )
        connection.execute(
            """
            UPDATE reports SET status = ?, updated_at = ?,
                category = COALESCE(?, category), urgency = COALESCE(?, urgency),
                department = COALESCE(?, department)
            WHERE id = ?
            """,
            (status, now, category, urgency, decision.department, report_id),
        )


def list_reviews(report_id: str) -> list[dict]:
    with closing(_connect()) as connection:
        rows = connection.execute(
            "SELECT * FROM reviews WHERE report_id = ? ORDER BY id", (report_id,)
        ).fetchall()
    return [dict(row) for row in rows]


def save_draft(report_id: str, body: str) -> None:
    """Save a drafted reply as pending."""
    now = _now()
    with closing(_connect()) as connection, connection:
        connection.execute(
            """
            INSERT INTO drafts (report_id, body, status, created_at, updated_at)
            VALUES (?, ?, 'pending', ?, ?)
            ON CONFLICT(report_id) DO UPDATE SET
                body = excluded.body, status = 'pending',
                updated_at = excluded.updated_at
            """,
            (report_id, body, now, now),
        )


def get_draft(report_id: str) -> dict | None:
    with closing(_connect()) as connection:
        row = connection.execute(
            "SELECT * FROM drafts WHERE report_id = ?", (report_id,)
        ).fetchone()
    return dict(row) if row else None


def finish_draft(report_id: str, body: str, status: str) -> None:
    """Record the final draft and set the report's final status."""
    now = _now()
    with closing(_connect()) as connection, connection:
        connection.execute(
            "UPDATE drafts SET body = ?, status = ?, updated_at = ? "
            "WHERE report_id = ?",
            (body, status, now, report_id),
        )
        connection.execute(
            "UPDATE reports SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, report_id),
        )
        if status == "ready_to_send":
            _create_thread(connection, report_id, body)


def create_user(email: str, name: str, password_hash: str, role: str) -> None:
    with closing(_connect()) as connection, connection:
        connection.execute(
            "INSERT INTO users (email, name, password_hash, role, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (email.lower(), name, password_hash, role, _now()),
        )


def find_user(email: str) -> StoredUser | None:
    with closing(_connect()) as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE email = ?", (email.lower(),)
        ).fetchone()
    return StoredUser(**dict(row)) if row else None


def get_user(user_id: int) -> User | None:
    with closing(_connect()) as connection:
        row = connection.execute(
            "SELECT id, email, name, role FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return User(**dict(row)) if row else None


def set_owner(report_id: str, user_id: int) -> None:
    with closing(_connect()) as connection, connection:
        connection.execute(
            "INSERT OR REPLACE INTO report_owners (report_id, user_id) VALUES (?, ?)",
            (report_id, user_id),
        )


def delete_owner(report_id: str) -> None:
    """Forget the owner of a report that was never saved."""
    with closing(_connect()) as connection, connection:
        connection.execute(
            "DELETE FROM report_owners WHERE report_id = ?", (report_id,)
        )


def get_owner(report_id: str) -> int | None:
    with closing(_connect()) as connection:
        row = connection.execute(
            "SELECT user_id FROM report_owners WHERE report_id = ?", (report_id,)
        ).fetchone()
    return row["user_id"] if row else None


def list_reports_of(user_id: int) -> list[ReportRecord]:
    """A citizen's own reports (those already saved), newest first."""
    with closing(_connect()) as connection:
        rows = connection.execute(
            """
            SELECT reports.* FROM reports
            JOIN report_owners ON report_owners.report_id = reports.id
            WHERE report_owners.user_id = ? ORDER BY reports.created_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [ReportRecord(**dict(row)) for row in rows]


def reset_database() -> None:
    """Delete all reports, reviews and drafts."""
    with closing(_connect()) as connection, connection:
        connection.execute("DELETE FROM drafts")
        connection.execute("DELETE FROM reviews")
        connection.execute("DELETE FROM reports")
        connection.execute("DELETE FROM report_owners")
        connection.execute("DELETE FROM threads")
        connection.execute("DELETE FROM messages")


# ---- Conversations: one thread per resolved report ----

SUMMARY_SQL = """
    SELECT t.*, r.text, r.category, r.urgency, r.department,
        (SELECT COUNT(*) FROM messages m WHERE m.report_id = t.report_id)
            AS message_count,
        (SELECT sender FROM messages m WHERE m.report_id = t.report_id
            ORDER BY id DESC LIMIT 1) AS last_sender,
        (SELECT created_at FROM messages m WHERE m.report_id = t.report_id
            ORDER BY id DESC LIMIT 1) AS last_message_at
    FROM threads t JOIN reports r ON r.id = t.report_id
"""


def _insert_message(
    connection: sqlite3.Connection, report_id: str, sender: Sender, body: str
) -> None:
    connection.execute(
        "INSERT INTO messages (report_id, sender, body, created_at) "
        "VALUES (?, ?, ?, ?)",
        (report_id, sender, body, _now()),
    )


def _create_thread(connection: sqlite3.Connection, report_id: str, reply: str) -> None:
    """Open the conversation. The approved reply is its first message."""
    now = _now()
    created = connection.execute(
        "INSERT OR IGNORE INTO threads (report_id, status, marked_fixed, "
        "created_at, updated_at) VALUES (?, 'open', 0, ?, ?)",
        (report_id, now, now),
    )
    if created.rowcount:
        _insert_message(connection, report_id, "admin", reply)


def _backfill(connection: sqlite3.Connection) -> None:
    """Give reports resolved before conversations existed their thread."""
    rows = connection.execute(
        """
        SELECT r.id, d.body FROM reports r JOIN drafts d ON d.report_id = r.id
        WHERE r.status = 'ready_to_send'
          AND r.id NOT IN (SELECT report_id FROM threads)
        """
    ).fetchall()
    for row in rows:
        _create_thread(connection, row["id"], row["body"])


def _summary(row: sqlite3.Row) -> ThreadSummary:
    data = dict(row)
    data["marked_fixed"] = bool(data["marked_fixed"])
    data["needs_attention"] = data["status"] == "open" and (
        data["marked_fixed"] or data["last_sender"] == "citizen"
    )
    return ThreadSummary(**data)


def get_thread(report_id: str) -> Thread | None:
    with closing(_connect()) as connection, connection:
        _backfill(connection)
        row = connection.execute(
            "SELECT * FROM threads WHERE report_id = ?", (report_id,)
        ).fetchone()
    if row is None:
        return None
    return Thread(**{**dict(row), "marked_fixed": bool(row["marked_fixed"])})


def list_messages(report_id: str) -> list[Message]:
    with closing(_connect()) as connection:
        rows = connection.execute(
            "SELECT * FROM messages WHERE report_id = ? ORDER BY id", (report_id,)
        ).fetchall()
    return [Message(**dict(row)) for row in rows]


def _list_threads(where: str = "", args: tuple = ()) -> list[ThreadSummary]:
    with closing(_connect()) as connection, connection:
        _backfill(connection)
        rows = connection.execute(
            f"{SUMMARY_SQL} {where} ORDER BY t.updated_at DESC, t.report_id", args
        ).fetchall()
    return [_summary(row) for row in rows]


def list_threads(
    status: str | None = None, attention: bool = False
) -> list[ThreadSummary]:
    """Every conversation, most recently active first (for the admin)."""
    threads = _list_threads()
    if status:
        threads = [t for t in threads if t.status == status]
    if attention:
        threads = [t for t in threads if t.needs_attention]
    return threads


def list_threads_of(user_id: int) -> list[ThreadSummary]:
    """A citizen's own conversations."""
    where = (
        "WHERE t.report_id IN (SELECT report_id FROM report_owners WHERE user_id = ?)"
    )
    return _list_threads(where, (user_id,))


def _open_thread(connection: sqlite3.Connection, report_id: str) -> None:
    """Raise unless the report has an open conversation."""
    _backfill(connection)
    thread = connection.execute(
        "SELECT status FROM threads WHERE report_id = ?", (report_id,)
    ).fetchone()
    if thread is None:
        raise ThreadNotFound(report_id)
    if thread["status"] == "closed":
        raise ThreadClosed(report_id)


def add_message(report_id: str, sender: Sender, body: str) -> Message:
    """Add a message to an open conversation.

    A citizen's message withdraws their "fixed" mark: their last word counts.
    """
    with closing(_connect()) as connection, connection:
        _open_thread(connection, report_id)
        count = connection.execute(
            "SELECT COUNT(*) FROM messages WHERE report_id = ?", (report_id,)
        ).fetchone()[0]
        if count >= MAX_MESSAGES:
            raise ThreadFull(report_id)
        _insert_message(connection, report_id, sender, body)
        connection.execute(
            "UPDATE threads SET updated_at = ?, "
            "marked_fixed = CASE WHEN ? = 'citizen' THEN 0 ELSE marked_fixed END "
            "WHERE report_id = ?",
            (_now(), sender, report_id),
        )
        row = connection.execute(
            "SELECT * FROM messages WHERE report_id = ? ORDER BY id DESC LIMIT 1",
            (report_id,),
        ).fetchone()
    return Message(**dict(row))


def mark_fixed(report_id: str) -> None:
    """The citizen says the problem is fixed. Only the admin closes the thread."""
    with closing(_connect()) as connection, connection:
        _open_thread(connection, report_id)
        connection.execute(
            "UPDATE threads SET marked_fixed = 1, updated_at = ? WHERE report_id = ?",
            (_now(), report_id),
        )


def close_thread(report_id: str) -> None:
    with closing(_connect()) as connection, connection:
        _open_thread(connection, report_id)
        connection.execute(
            "UPDATE threads SET status = 'closed', updated_at = ? WHERE report_id = ?",
            (_now(), report_id),
        )
