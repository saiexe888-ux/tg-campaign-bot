import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from . import config


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    is_blocked INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_seen TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS instagram_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, username)
);

CREATE TABLE IF NOT EXISTS campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    payout_per_view REAL DEFAULT 0,
    target_views INTEGER DEFAULT 0,
    description TEXT DEFAULT '',
    rules TEXT DEFAULT '',
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS submissions (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    campaign_id INTEGER NOT NULL,
    link TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    views INTEGER DEFAULT 0,
    payout REAL DEFAULT 0,
    admin_note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    decided_at TEXT,
    UNIQUE(user_id, campaign_id, link)
);

CREATE INDEX IF NOT EXISTS idx_submissions_user
ON submissions(user_id);

CREATE INDEX IF NOT EXISTS idx_submissions_status
ON submissions(status);
"""


def _connect():
    """
    Create a new SQLite connection (one per operation = thread safe).
    """
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        config.DB_PATH,
        timeout=30,
    )
    conn.row_factory = sqlite3.Row

    # WAL mode helps with concurrent reads/writes.
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")

    return conn


@contextmanager
def _db():
    """
    Database context manager: commit on success, rollback on error.
    """
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Create database tables if they do not exist.
    """
    with _db() as conn:
        conn.executescript(SCHEMA)


# ------------------------------------------------------------------
# Users
# ------------------------------------------------------------------

def upsert_user(user_id, username, first_name, last_name) -> None:
    """
    Insert or update a Telegram user.
    """
    with _db() as conn:
        conn.execute(
            """
            INSERT INTO users(user_id, username, first_name, last_name, last_seen)
            VALUES(?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                last_name=excluded.last_name,
                last_seen=CURRENT_TIMESTAMP
            """,
            (user_id, username, first_name, last_name),
        )


def all_user_ids() -> list:
    """
    Return all non-blocked user IDs (for broadcast).
    """
    with _db() as conn:
        rows = conn.execute(
            """
            SELECT user_id
            FROM users
            WHERE is_blocked = 0
            ORDER BY last_seen DESC
            """
        ).fetchall()
        return [row["user_id"] for row in rows]


# ------------------------------------------------------------------
# Instagram accounts
# ------------------------------------------------------------------

def add_instagram(user_id: int, username: str) -> bool:
    """
    Add Instagram username. True if inserted, False if duplicate.
    """
    username = username.lower()

    with _db() as conn:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO instagram_accounts(user_id, username)
            VALUES(?, ?)
            """,
            (user_id, username),
        )
        return cur.rowcount > 0


def list_instagram(user_id: int) -> list:
    """
    List saved Instagram accounts for a user.
    """
    with _db() as conn:
        rows = conn.execute(
            """
            SELECT id, username
            FROM instagram_accounts
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def delete_instagram(account_id: int, user_id: int) -> bool:
    """
    Delete an Instagram account if it belongs to the user.
    """
    with _db() as conn:
        cur = conn.execute(
            """
            DELETE FROM instagram_accounts
            WHERE id = ? AND user_id = ?
            """,
            (account_id, user_id),
        )
        return cur.rowcount > 0


def has_instagram_account(user_id: int) -> bool:
    """
    Check whether user has at least one saved Instagram account.
    """
    with _db() as conn:
        row = conn.execute(
            """
            SELECT 1
            FROM instagram_accounts
            WHERE user_id = ?
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        return row is not None


# ------------------------------------------------------------------
# Campaigns
# ------------------------------------------------------------------

def get_active_campaigns() -> list:
    """
    Get active campaigns visible to users.
    """
    with _db() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM campaigns
            WHERE active = 1
            ORDER BY id DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]


def get_campaigns_admin() -> list:
    """
    Get all campaigns for admin panel.
    """
    with _db() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM campaigns
            ORDER BY id DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]


def get_campaign(campaign_id: int):
    """
    Get one campaign by ID.
    """
    with _db() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM campaigns
            WHERE id = ?
            """,
            (campaign_id,),
        ).fetchone()
        return dict(row) if row else None


def create_campaign(name, payout_per_view, target_views, description, rules) -> int:
    """
    Create a new campaign. Returns campaign ID.
    """
    with _db() as conn:
        cur = conn.execute(
            """
            INSERT INTO campaigns(name, payout_per_view, target_views, description, rules, active)
            VALUES(?, ?, ?, ?, ?, 1)
            """,
            (name, payout_per_view, target_views, description, rules),
        )
        return int(cur.lastrowid)


def set_campaign_description(campaign_id: int, description: str) -> bool:
    """
    Update campaign description.
    """
    with _db() as conn:
        cur = conn.execute(
            """
            UPDATE campaigns
            SET description = ?
            WHERE id = ?
            """,
            (description, campaign_id),
        )
        return cur.rowcount > 0


def set_campaign_rules(campaign_id: int, rules: str) -> bool:
    """
    Update campaign rules.
    """
    with _db() as conn:
        cur = conn.execute(
            """
            UPDATE campaigns
            SET rules = ?
            WHERE id = ?
            """,
            (rules, campaign_id),
        )
        return cur.rowcount > 0


def toggle_campaign(campaign_id: int):
    """
    Toggle campaign active state. Returns new state or None.
    """
    with _db() as conn:
        cur = conn.execute(
            """
            UPDATE campaigns
            SET active = 1 - active
            WHERE id = ?
            """,
            (campaign_id,),
        )
        if cur.rowcount == 0:
            return None

        row = conn.execute(
            """
            SELECT active
            FROM campaigns
            WHERE id = ?
            """,
            (campaign_id,),
        ).fetchone()
        return bool(row["active"])


# ------------------------------------------------------------------
# Submissions
# ------------------------------------------------------------------

def create_submission(user_id: int, campaign_id: int, link: str) -> dict:
    """
    Create a submission. Returns dict with duplicate flag and id.
    """
    with _db() as conn:
        existing = conn.execute(
            """
            SELECT id, status
            FROM submissions
            WHERE user_id = ? AND campaign_id = ? AND link = ?
            """,
            (user_id, campaign_id, link),
        ).fetchone()

        if existing:
            return {
                "duplicate": True,
                "id": existing["id"],
                "status": existing["status"],
            }

        # Try a few times in case of rare ID collision.
        for _ in range(10):
            submission_id = uuid.uuid4().hex[:8]

            try:
                conn.execute(
                    """
                    INSERT INTO submissions(id, user_id, campaign_id, link, status)
                    VALUES(?, ?, ?, ?, 'pending')
                    """,
                    (submission_id, user_id, campaign_id, link),
                )
                return {
                    "duplicate": False,
                    "id": submission_id,
                    "status": "pending",
                }
            except sqlite3.IntegrityError:
                continue

        raise RuntimeError("Could not create a unique submission ID")


def get_submission(submission_id: str):
    """
    Get one submission by short ID.
    """
    with _db() as conn:
        row = conn.execute(
            """
            SELECT
                s.id,
                s.user_id,
                s.campaign_id,
                s.link,
                s.status,
                s.views,
                s.payout,
                s.admin_note,
                s.created_at,
                s.decided_at,
                c.name AS campaign_name,
                c.payout_per_view,
                c.target_views,
                u.username AS user_username
            FROM submissions s
            JOIN campaigns c ON c.id = s.campaign_id
            LEFT JOIN users u ON u.user_id = s.user_id
            WHERE s.id = ?
            """,
            (submission_id,),
        ).fetchone()
        return dict(row) if row else None


def list_user_submissions(user_id: int, limit: int = 10) -> list:
    """
    Get recent submissions for a user.
    """
    with _db() as conn:
        rows = conn.execute(
            """
            SELECT
                s.id,
                s.link,
                s.status,
                s.views,
                s.payout,
                s.created_at,
                c.name AS campaign_name
            FROM submissions s
            JOIN campaigns c ON c.id = s.campaign_id
            WHERE s.user_id = ?
            ORDER BY s.created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]


def list_pending_submissions(limit: int = 20) -> list:
    """
    Get pending submissions for admin panel.
    """
    with _db() as conn:
        rows = conn.execute(
            """
            SELECT
                s.id,
                s.user_id,
                s.link,
                s.created_at,
                c.name AS campaign_name,
                u.username AS user_username
            FROM submissions s
            JOIN campaigns c ON c.id = s.campaign_id
            LEFT JOIN users u ON u.user_id = s.user_id
            WHERE s.status = 'pending'
            ORDER BY s.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def set_submission_status(submission_id: str, status: str, admin_note=None):
    """
    Approve or reject a submission.
    """
    with _db() as conn:
        cur = conn.execute(
            """
            UPDATE submissions
            SET status = ?, decided_at = CURRENT_TIMESTAMP, admin_note = ?
            WHERE id = ?
            """,
            (status, admin_note, submission_id),
        )
        if cur.rowcount == 0:
            return None

    return get_submission(submission_id)


def update_submission_views(submission_id: str, views: int):
    """
    Update view count and calculate payout (approved only, capped at target).
    """
    views = max(0, int(views))

    with _db() as conn:
        row = conn.execute(
            """
            SELECT
                s.status,
                c.payout_per_view,
                c.target_views
            FROM submissions s
            JOIN campaigns c ON c.id = s.campaign_id
            WHERE s.id = ?
            """,
            (submission_id,),
        ).fetchone()

        if not row:
            return None

        paid_views = views

        if row["target_views"] and row["target_views"] > 0:
            paid_views = min(views, row["target_views"])

        payout = 0.0

        if row["status"] == "approved":
            payout = round(paid_views * float(row["payout_per_view"] or 0), 6)

        conn.execute(
            """
            UPDATE submissions
            SET views = ?, payout = ?
            WHERE id = ?
            """,
            (views, payout, submission_id),
        )

    return get_submission(submission_id)


# ------------------------------------------------------------------
# Stats
# ------------------------------------------------------------------

def user_earnings(user_id: int) -> dict:
    """
    Get submission/payout summary for a user.
    """
    with _db() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END), 0) AS pending,
                COALESCE(SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END), 0) AS approved,
                COALESCE(SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END), 0) AS rejected,
                COALESCE(SUM(CASE WHEN status = 'approved' THEN views ELSE 0 END), 0) AS views,
                COALESCE(SUM(CASE WHEN status = 'approved' THEN payout ELSE 0 END), 0) AS payout
            FROM submissions
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
        return dict(row)


def admin_stats() -> dict:
    """
    Get admin dashboard stats.
    """
    with _db() as conn:
        row = conn.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM users) AS users,
                (SELECT COUNT(*) FROM campaigns WHERE active = 1) AS active_campaigns,
                (SELECT COUNT(*) FROM submissions WHERE status = 'pending') AS pending,
                (SELECT COUNT(*) FROM submissions WHERE status = 'approved') AS approved,
                (SELECT COUNT(*) FROM submissions WHERE status = 'rejected') AS rejected,
                (
                    SELECT COALESCE(SUM(payout), 0)
                    FROM submissions
                    WHERE status = 'approved'
                ) AS total_payout
            """
        ).fetchone()
        return dict(row)
