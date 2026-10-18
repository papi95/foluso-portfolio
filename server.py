"""Small, security-conscious gig-board pilot API for Crews & Gigs.

The first release intentionally ships only member accounts, gigs and applications.
Run locally with: uvicorn server:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("CREWS_GIGS_DB", ROOT / "instance" / "crews-gigs.sqlite3"))
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "0") == "1"
SESSION_COOKIE = "cg_session"
SESSION_DAYS = 7
PBKDF2_ROUNDS = 310_000
DUMMY_SALT = b"crews-gigs-dummy-salt"
DUMMY_HASH = hashlib.pbkdf2_hmac("sha256", b"not-a-real-password", DUMMY_SALT, PBKDF2_ROUNDS, dklen=32)
MAX_BODY_BYTES = 1_000_000
EMAIL_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$")
DISCIPLINES = {
    "music", "live production", "audio / av", "photography", "videography",
    "graphic design", "video editing", "production", "other media"
}

@asynccontextmanager
async def lifespan(_app):
    init_db()
    with db() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now_iso(),))
    yield


app = FastAPI(title="Crews & Gigs pilot API", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
_rate_lock = Lock()
_rate_buckets: dict[str, list[float]] = {}


@contextmanager
def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == "posix":
        os.chmod(DB_PATH.parent, 0o700)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    if os.name == "posix" and DB_PATH.exists():
        os.chmod(DB_PATH, 0o600)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db() as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            name TEXT NOT NULL, discipline TEXT NOT NULL, city TEXT NOT NULL,
            password_salt BLOB NOT NULL, password_hash BLOB NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            csrf_token TEXT NOT NULL, expires_at TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS sessions_user_idx ON sessions(user_id);
        CREATE TABLE IF NOT EXISTS gigs (
            id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL, description TEXT NOT NULL, discipline TEXT NOT NULL,
            location TEXT NOT NULL, engagement TEXT NOT NULL, pay_info TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','closed')),
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS gigs_open_created_idx ON gigs(status, created_at DESC);
        CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY, gig_id TEXT NOT NULL REFERENCES gigs(id) ON DELETE CASCADE,
            applicant_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            message TEXT NOT NULL, share_email INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','accepted','declined')),
            created_at TEXT NOT NULL, UNIQUE(gig_id, applicant_id)
        );
        CREATE INDEX IF NOT EXISTS applications_gig_idx ON applications(gig_id, created_at);
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY, gig_id TEXT NOT NULL REFERENCES gigs(id) ON DELETE CASCADE,
            reporter_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            reason TEXT NOT NULL, details TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','reviewed','dismissed')),
            moderator_note TEXT NOT NULL DEFAULT '', reviewed_by TEXT REFERENCES users(id), reviewed_at TEXT,
            UNIQUE(gig_id, reporter_id)
        );
        """)
        # Small forward-only migration for a pilot DB created before moderation status fields.
        report_columns = {row["name"] for row in conn.execute("PRAGMA table_info(reports)")}
        for name, declaration in (("status", "TEXT NOT NULL DEFAULT 'pending'"),
                                  ("moderator_note", "TEXT NOT NULL DEFAULT ''"),
                                  ("reviewed_by", "TEXT REFERENCES users(id)"),
                                  ("reviewed_at", "TEXT")):
            if name not in report_columns:
                conn.execute(f"ALTER TABLE reports ADD COLUMN {name} {declaration}")
        application_columns = {row["name"] for row in conn.execute("PRAGMA table_info(applications)")}
        if "share_email" not in application_columns:
            conn.execute("ALTER TABLE applications ADD COLUMN share_email INTEGER NOT NULL DEFAULT 0")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _limited(key: str, limit: int, window_seconds: int) -> None:
    now = time.monotonic()
    with _rate_lock:
        hits = [stamp for stamp in _rate_buckets.get(key, []) if now - stamp < window_seconds]
        if len(hits) >= limit:
            raise HTTPException(429, "Too many attempts. Please wait and try again.", headers={"Retry-After": str(window_seconds)})
        hits.append(now)
        _rate_buckets[key] = hits
        if len(_rate_buckets) > 2_000:
            for old_key in list(_rate_buckets)[:500]:
                _rate_buckets.pop(old_key, None)


def _client_key(request: Request, action: str) -> str:
    # Never trust arbitrary forwarded IP headers here; configure a trusted proxy/rate limiter in production.
    return f"{action}:{request.client.host if request.client else 'unknown'}"


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS, dklen=32)


def _enforce_daily_quota(conn: sqlite3.Connection, table: str, owner_column: str, user_id: str, limit: int) -> None:
    # Identifiers come only from these fixed call-site constants, never from request input.
    allowed = {("gigs", "owner_id"), ("applications", "applicant_id"), ("reports", "reporter_id")}
    if (table, owner_column) not in allowed:
        raise RuntimeError("Invalid quota target")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(timespec="seconds")
    count = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {owner_column}=? AND created_at>=?", (user_id, cutoff)).fetchone()[0]
    if count >= limit:
        raise HTTPException(429, "Daily action limit reached. Please try again later.")


def _moderator_emails() -> set[str]:
    return {item.strip().lower() for item in os.environ.get("MODERATOR_EMAILS", "").split(",") if item.strip()}


def _is_moderator(email: str) -> bool:
    return email.lower() in _moderator_emails()


def _moderator_ready() -> bool:
    emails = _moderator_emails()
    if not emails:
        return False
    placeholders = ",".join("?" for _ in emails)
    with db() as conn:
        return conn.execute(f"SELECT 1 FROM users WHERE lower(email) IN ({placeholders}) LIMIT 1", tuple(emails)).fetchone() is not None


def _session(request: Request) -> tuple[sqlite3.Row, str] | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token or len(token) > 128:
        return None
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with db() as conn:
        row = conn.execute("""SELECT u.*, s.csrf_token, s.expires_at FROM sessions s
            JOIN users u ON u.id=s.user_id WHERE s.token_hash=?""", (token_hash,)).fetchone()
        if not row:
            return None
        if row["expires_at"] <= now_iso():
            conn.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash,))
            return None
        return row, row["csrf_token"]


def current_user(request: Request) -> sqlite3.Row:
    data = _session(request)
    if data is None:
        raise HTTPException(401, "Please sign in to continue.")
    return data[0]


def require_csrf(request: Request, x_csrf_token: Annotated[str | None, Header()] = None) -> None:
    data = _session(request)
    if data is None:
        raise HTTPException(401, "Please sign in to continue.")
    expected = data[1]
    if not x_csrf_token or not hmac.compare_digest(x_csrf_token, expected):
        raise HTTPException(403, "Session check failed. Refresh and try again.")
    origin = request.headers.get("origin")
    if origin:
        from urllib.parse import urlsplit
        origin_parts = urlsplit(origin)
        host = request.headers.get("host", "").lower()
        if origin_parts.netloc.lower() != host or origin_parts.scheme not in {"http", "https"}:
            raise HTTPException(403, "Cross-origin request rejected.")


def _create_session(response: Response, user_id: str) -> tuple[str, str]:
    raw_token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    created = datetime.now(timezone.utc)
    expiry = created + timedelta(days=SESSION_DAYS)
    with db() as conn:
        conn.execute("INSERT INTO sessions(token_hash,user_id,csrf_token,expires_at,created_at) VALUES(?,?,?,?,?)",
                     (token_hash, user_id, csrf, expiry.isoformat(timespec="seconds"), created.isoformat(timespec="seconds")))
    response.set_cookie(SESSION_COOKIE, raw_token, max_age=SESSION_DAYS*24*3600,
        httponly=True, secure=COOKIE_SECURE, samesite="strict", path="/")
    return csrf, expiry.isoformat(timespec="seconds")


class RegisterInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=6, max_length=254)
    password: str = Field(min_length=12, max_length=128)
    discipline: str = Field(min_length=2, max_length=40)
    city: str = Field(min_length=2, max_length=80)
    invite_code: str = Field(default="", max_length=80)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        value = value.strip()
        if not EMAIL_RE.fullmatch(value):
            raise ValueError("Enter a valid email address.")
        local = value.rsplit("@", 1)[0]
        if local.startswith(".") or local.endswith(".") or ".." in local:
            raise ValueError("Enter a valid email address.")
        return value.lower()

    @field_validator("name", "city")
    @classmethod
    def plain_text(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2 or any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
            raise ValueError("Enter at least two visible characters.")
        return value

    @field_validator("discipline")
    @classmethod
    def known_discipline(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in DISCIPLINES:
            raise ValueError("Choose a listed media discipline.")
        return value

    @field_validator("invite_code")
    @classmethod
    def normalized_invite_code(cls, value: str) -> str:
        return value.strip()


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=6, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalized_email(cls, value: str) -> str:
        return value.strip().lower()


class GigInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str = Field(min_length=6, max_length=120)
    description: str = Field(min_length=20, max_length=4000)
    discipline: str = Field(min_length=2, max_length=40)
    location: str = Field(min_length=2, max_length=80)
    engagement: str = Field(min_length=2, max_length=30)
    pay_info: str = Field(default="", max_length=160)

    @field_validator("discipline")
    @classmethod
    def known_discipline(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in DISCIPLINES:
            raise ValueError("Choose a listed media discipline.")
        return value

    @field_validator("title", "location", "pay_info")
    @classmethod
    def no_control_chars(cls, value: str) -> str:
        if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
            raise ValueError("Control characters are not allowed.")
        return value

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str) -> str:
        if any((ord(ch) < 32 and ch not in "\n\r\t") or ord(ch) == 127 for ch in value):
            raise ValueError("Unsupported control characters are not allowed.")
        return value

    @field_validator("engagement")
    @classmethod
    def known_engagement(cls, value: str) -> str:
        allowed = {"Paid gig", "Contract", "Volunteer", "Other"}
        if value not in allowed:
            raise ValueError("Choose a valid engagement type.")
        return value


class ApplicationInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    message: str = Field(min_length=20, max_length=1500)
    share_email: bool = False

    @field_validator("message")
    @classmethod
    def clean_message(cls, value: str) -> str:
        if any((ord(ch) < 32 and ch not in "\n\r\t") or ord(ch) == 127 for ch in value):
            raise ValueError("Unsupported control characters are not allowed.")
        return value


class ReportInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    reason: str = Field(min_length=4, max_length=40)
    details: str = Field(default="", max_length=1000)


class ModerationInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    status: str
    note: str = Field(default="", max_length=1000)
    close_gig: bool = False


@app.middleware("http")
async def security_headers(request: Request, call_next):
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > MAX_BODY_BYTES:
        return Response("Request too large", status_code=413, headers={"X-Content-Type-Options":"nosniff", "X-Frame-Options":"DENY", "Cache-Control":"no-store"})
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'")
    if COOKIE_SECURE:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(ROOT / "index.html")


@app.get("/app", include_in_schema=False)
def pilot_app():
    return FileResponse(ROOT / "pilot.html")


@app.get("/styles.css", include_in_schema=False)
def stylesheet():
    return FileResponse(ROOT / "styles.css", media_type="text/css")


@app.get("/script.js", include_in_schema=False)
def javascript():
    return FileResponse(ROOT / "script.js", media_type="application/javascript")


@app.get("/pilot.css", include_in_schema=False)
def pilot_stylesheet():
    return FileResponse(ROOT / "pilot.css", media_type="text/css")


@app.get("/pilot.js", include_in_schema=False)
def pilot_javascript():
    return FileResponse(ROOT / "pilot.js", media_type="application/javascript")


@app.get("/docs/{document}", include_in_schema=False)
def public_document(document: str):
    allowed = {"PRODUCT-PLAN.md", "COMMUNITY-GUIDELINES.md", "PRIVACY.md", "TERMS.md", "PILOT-RESEARCH.md"}
    if document not in allowed:
        raise HTTPException(404, "Document not found.")
    path = ROOT / "docs" / document
    if not path.is_file():
        raise HTTPException(404, "Document not found.")
    return FileResponse(path, media_type="text/markdown")


@app.get("/health")
def health():
    return {"status": "ok", "service": "crews-gigs-pilot"}


@app.post("/api/auth/register", status_code=201)
def register(payload: RegisterInput, request: Request, response: Response):
    _limited(_client_key(request, "register"), 5, 3600)
    invite_code = os.environ.get("PILOT_INVITE_CODE", "")
    if invite_code and not hmac.compare_digest(payload.invite_code, invite_code):
        raise HTTPException(403, "A valid pilot invite code is required.")
    salt = secrets.token_bytes(16)
    password_hash = _hash_password(payload.password, salt)
    user_id = str(uuid.uuid4())
    created = now_iso()
    try:
        with db() as conn:
            conn.execute("INSERT INTO users(id,email,name,discipline,city,password_salt,password_hash,created_at) VALUES(?,?,?,?,?,?,?,?)",
                         (user_id, payload.email, payload.name, payload.discipline, payload.city, salt, password_hash, created))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "An account with that email already exists.")
    csrf, expiry = _create_session(response, user_id)
    return {"user": {"id": user_id, "name": payload.name, "email": payload.email, "discipline": payload.discipline, "city": payload.city, "is_moderator": _is_moderator(payload.email)}, "csrf_token": csrf, "expires_at": expiry}


@app.post("/api/auth/login")
def login(payload: LoginInput, request: Request, response: Response):
    _limited(_client_key(request, "login"), 10, 900)
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE email=? COLLATE NOCASE", (payload.email.lower(),)).fetchone()
    # Do comparable PBKDF2 work for unknown emails to reduce account-enumeration timing signals.
    salt = user["password_salt"] if user else DUMMY_SALT
    expected_hash = user["password_hash"] if user else DUMMY_HASH
    candidate_hash = _hash_password(payload.password, salt)
    if not user or not hmac.compare_digest(candidate_hash, expected_hash):
        raise HTTPException(401, "Email or password is incorrect.")
    csrf, expiry = _create_session(response, user["id"])
    return {"user": {"id": user["id"], "name": user["name"], "email": user["email"], "discipline": user["discipline"], "city": user["city"], "is_moderator": _is_moderator(user["email"])}, "csrf_token": csrf, "expires_at": expiry}


@app.get("/api/auth/session")
def session_info(request: Request):
    data = _session(request)
    if not data:
        return {"user": None, "csrf_token": None}
    user, csrf = data
    return {"user": {"id": user["id"], "name": user["name"], "email": user["email"], "discipline": user["discipline"], "city": user["city"], "is_moderator": _is_moderator(user["email"])}, "csrf_token": csrf}


@app.post("/api/auth/logout", status_code=204)
def logout(request: Request, response: Response, _: Annotated[None, Depends(require_csrf)]):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        with db() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),))
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, secure=COOKIE_SECURE, samesite="strict")
    response.status_code = 204
    return response


@app.get("/api/gigs")
def list_gigs(q: str = "", city: str = "", discipline: str = "", limit: int = 50, offset: int = 0):
    if len(q) > 100 or len(city) > 80 or len(discipline) > 40:
        raise HTTPException(422, "Search filter is too long.")
    limit = max(1, min(limit, 100)); offset = max(0, offset)
    clauses = ["g.status='open'"]; args: list = []
    if q.strip():
        clauses.append("(g.title LIKE ? OR g.description LIKE ? OR g.discipline LIKE ?)")
        term = f"%{q.strip()}%"; args.extend([term, term, term])
    if city.strip():
        clauses.append("g.location LIKE ?"); args.append(f"%{city.strip()}%")
    if discipline.strip():
        clauses.append("g.discipline=?"); args.append(discipline.strip().lower())
    where = " AND ".join(clauses)
    with db() as conn:
        rows = conn.execute(f"""SELECT g.*,u.name AS poster_name,u.discipline AS poster_discipline,
            (SELECT COUNT(*) FROM applications a WHERE a.gig_id=g.id) AS application_count
            FROM gigs g JOIN users u ON u.id=g.owner_id WHERE {where}
            ORDER BY g.created_at DESC LIMIT ? OFFSET ?""", (*args, limit, offset)).fetchall()
    return {"items": [dict(row) for row in rows], "limit": limit, "offset": offset}


@app.post("/api/gigs", status_code=201)
def create_gig(payload: GigInput, user: Annotated[sqlite3.Row, Depends(current_user)], _: Annotated[None, Depends(require_csrf)]):
    gig_id = str(uuid.uuid4()); created = now_iso()
    with db() as conn:
        _enforce_daily_quota(conn, "gigs", "owner_id", user["id"], 10)
        conn.execute("INSERT INTO gigs(id,owner_id,title,description,discipline,location,engagement,pay_info,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                     (gig_id, user["id"], payload.title, payload.description, payload.discipline,
                      payload.location, payload.engagement, payload.pay_info, created))
    return {"id": gig_id, "owner_id": user["id"], **payload.model_dump(), "status": "open", "created_at": created, "poster_name": user["name"], "application_count": 0}


@app.post("/api/gigs/{gig_id}/applications", status_code=201)
def apply_to_gig(gig_id: str, payload: ApplicationInput, user: Annotated[sqlite3.Row, Depends(current_user)], _: Annotated[None, Depends(require_csrf)]):
    with db() as conn:
        gig = conn.execute("SELECT id,owner_id,status FROM gigs WHERE id=?", (gig_id,)).fetchone()
        if not gig or gig["status"] != "open":
            raise HTTPException(404, "This gig is no longer available.")
        if gig["owner_id"] == user["id"]:
            raise HTTPException(409, "You cannot apply to your own gig.")
        _enforce_daily_quota(conn, "applications", "applicant_id", user["id"], 30)
        application_id = str(uuid.uuid4())
        try:
            conn.execute("INSERT INTO applications(id,gig_id,applicant_id,message,share_email,created_at) VALUES(?,?,?,?,?,?)",
                         (application_id, gig_id, user["id"], payload.message, int(payload.share_email), now_iso()))
        except sqlite3.IntegrityError:
            raise HTTPException(409, "You have already applied to this gig.")
    return {"id": application_id, "gig_id": gig_id, "status": "pending"}


@app.get("/api/gigs/{gig_id}/applications")
def gig_applications(gig_id: str, user: Annotated[sqlite3.Row, Depends(current_user)]):
    with db() as conn:
        gig = conn.execute("SELECT owner_id FROM gigs WHERE id=?", (gig_id,)).fetchone()
        if not gig:
            raise HTTPException(404, "Gig not found.")
        if gig["owner_id"] != user["id"]:
            raise HTTPException(403, "Only the gig poster can view applications.")
        rows = conn.execute("""SELECT a.id,a.message,a.status,a.created_at,u.name AS applicant_name,
            u.discipline AS applicant_discipline,u.city AS applicant_city,
            CASE WHEN a.share_email=1 THEN u.email ELSE NULL END AS applicant_email
            FROM applications a JOIN users u ON u.id=a.applicant_id
            WHERE a.gig_id=? ORDER BY a.created_at""", (gig_id,)).fetchall()
    return {"items": [dict(row) for row in rows]}


@app.get("/api/my/gigs")
def my_gigs(user: Annotated[sqlite3.Row, Depends(current_user)]):
    with db() as conn:
        rows = conn.execute("""SELECT g.*,(SELECT COUNT(*) FROM applications a WHERE a.gig_id=g.id) AS application_count
            FROM gigs g WHERE g.owner_id=? ORDER BY g.created_at DESC""", (user["id"],)).fetchall()
    return {"items": [dict(row) for row in rows]}


@app.get("/api/my/applications")
def my_applications(user: Annotated[sqlite3.Row, Depends(current_user)]):
    with db() as conn:
        rows = conn.execute("""SELECT a.id,a.message,a.status,a.created_at,g.id AS gig_id,g.title,g.location,g.status AS gig_status
            FROM applications a JOIN gigs g ON g.id=a.gig_id
            WHERE a.applicant_id=? ORDER BY a.created_at DESC""", (user["id"],)).fetchall()
    return {"items": [dict(row) for row in rows]}


@app.patch("/api/gigs/{gig_id}/close")
def close_gig(gig_id: str, user: Annotated[sqlite3.Row, Depends(current_user)], _: Annotated[None, Depends(require_csrf)]):
    with db() as conn:
        result = conn.execute("UPDATE gigs SET status='closed' WHERE id=? AND owner_id=? AND status='open'", (gig_id, user["id"]))
        if result.rowcount != 1:
            exists = conn.execute("SELECT 1 FROM gigs WHERE id=?", (gig_id,)).fetchone()
            if not exists: raise HTTPException(404, "Gig not found.")
            raise HTTPException(409, "Gig is already closed or belongs to another member.")
    return {"id": gig_id, "status": "closed"}


@app.post("/api/gigs/{gig_id}/reports", status_code=201)
def report_gig(gig_id: str, payload: ReportInput, user: Annotated[sqlite3.Row, Depends(current_user)], _: Annotated[None, Depends(require_csrf)]):
    allowed = {"spam", "fraud", "unsafe", "discrimination", "other"}
    if payload.reason not in allowed:
        raise HTTPException(422, "Choose a valid report reason.")
    with db() as conn:
        if not conn.execute("SELECT 1 FROM gigs WHERE id=?", (gig_id,)).fetchone():
            raise HTTPException(404, "Gig not found.")
        _enforce_daily_quota(conn, "reports", "reporter_id", user["id"], 10)
        try:
            conn.execute("INSERT INTO reports(id,gig_id,reporter_id,reason,details,created_at) VALUES(?,?,?,?,?,?)",
                         (str(uuid.uuid4()), gig_id, user["id"], payload.reason, payload.details, now_iso()))
        except sqlite3.IntegrityError:
            raise HTTPException(409, "You have already reported this gig.")
    moderator_ready = _moderator_ready()
    message = ("Report recorded for moderator review. If anyone is in immediate danger, contact local emergency services."
               if moderator_ready else "Report saved, but no active moderator is configured. Please contact the pilot operator directly for follow-up.")
    return {"received": True, "message": message}


@app.get("/api/moderation/reports")
def moderation_reports(user: Annotated[sqlite3.Row, Depends(current_user)], status: str = "pending"):
    # Moderator access is a server-configured email allowlist, never a client-provided role.
    if not _is_moderator(user["email"]):
        raise HTTPException(403, "Moderator access required.")
    if status not in {"pending", "reviewed", "dismissed", "all"}:
        raise HTTPException(422, "Unknown moderation status.")
    with db() as conn:
        query = """SELECT r.id,r.gig_id,r.reason,r.details,r.status,r.moderator_note,r.created_at,
            g.title AS gig_title,g.location,g.owner_id,u.name AS reporter_name
            FROM reports r JOIN gigs g ON g.id=r.gig_id JOIN users u ON u.id=r.reporter_id"""
        rows = conn.execute(query + (" ORDER BY r.created_at DESC" if status == "all" else " WHERE r.status=? ORDER BY r.created_at DESC"), (() if status == "all" else (status,))).fetchall()
    return {"items": [dict(row) for row in rows]}


@app.patch("/api/moderation/reports/{report_id}")
def update_report(report_id: str, payload: ModerationInput,
                  user: Annotated[sqlite3.Row, Depends(current_user)],
                  _: Annotated[None, Depends(require_csrf)]):
    if not _is_moderator(user["email"]):
        raise HTTPException(403, "Moderator access required.")
    if payload.status not in {"reviewed", "dismissed"}:
        raise HTTPException(422, "Choose reviewed or dismissed.")
    with db() as conn:
        report = conn.execute("SELECT gig_id FROM reports WHERE id=? AND status='pending'", (report_id,)).fetchone()
        if not report:
            exists = conn.execute("SELECT 1 FROM reports WHERE id=?", (report_id,)).fetchone()
            if not exists: raise HTTPException(404, "Report not found.")
            raise HTTPException(409, "Report has already been reviewed.")
        if payload.close_gig:
            conn.execute("UPDATE gigs SET status='closed' WHERE id=?", (report["gig_id"],))
        conn.execute("""UPDATE reports SET status=?,moderator_note=?,reviewed_by=?,reviewed_at=?
            WHERE id=? AND status='pending'""", (payload.status,payload.note,user["id"],now_iso(),report_id))
    return {"id": report_id, "status": payload.status, "gig_closed": payload.close_gig}
