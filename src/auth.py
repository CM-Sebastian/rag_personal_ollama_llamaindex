import sqlite3
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timedelta

try:
    from argon2 import PasswordHasher
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "argon2-cffi is required for authentication. Install it with 'pip install argon2-cffi'"
    ) from exc

DEFAULT_LOCKOUT_THRESHOLD = 5
DEFAULT_LOCKOUT_MINUTES = 5


class AuthDB:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        return sqlite3.connect(str(self.db_path))

    def init_db(self):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.executescript(
                """
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                label TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role_id INTEGER NOT NULL,
                failed_attempts INTEGER DEFAULT 0,
                locked_until TEXT DEFAULT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(role_id) REFERENCES roles(id)
            );

            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY,
                role_id INTEGER NOT NULL,
                permission TEXT NOT NULL,
                FOREIGN KEY(role_id) REFERENCES roles(id)
            );

            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                event_type TEXT NOT NULL,
                detail TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
            )
            # ensure default roles
            roles = [
                ("administrador", "Administrador"),
                ("reclutador", "Reclutador"),
                ("cliente", "Cliente"),
                ("estudiante", "Estudiante"),
                ("colega", "Colega"),
                ("general", "Público general"),
            ]
            for key, label in roles:
                try:
                    cur.execute("INSERT INTO roles(key,label) VALUES (?,?)", (key, label))
                except sqlite3.IntegrityError:
                    pass
            conn.commit()

    def create_user(self, username: str, password: str, role_key: str = "general") -> None:
        ph = PasswordHasher() if PasswordHasher else None
        if ph is None:
            raise RuntimeError("argon2-cffi is required for secure password hashing")
        password_hash = ph.hash(password)
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM roles WHERE key = ?", (role_key,))
            row = cur.fetchone()
            if not row:
                raise ValueError("Role not found")
            role_id = row[0]
            cur.execute(
                "INSERT INTO users(username,password_hash,role_id,created_at) VALUES (?,?,?,?)",
                (username, password_hash, role_id, datetime.utcnow().isoformat()),
            )
            conn.commit()

    def verify_user(self, username: str, password: str) -> Optional[Dict]:
        ph = PasswordHasher() if PasswordHasher else None
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id,password_hash,role_id,failed_attempts,locked_until FROM users WHERE username = ?", (username,))
            row = cur.fetchone()
            if not row:
                return None
            user_id, password_hash, role_id, failed_attempts, locked_until = row
            # check lock
            if locked_until:
                locked_until_dt = datetime.fromisoformat(locked_until)
                if datetime.utcnow() < locked_until_dt:
                    return None
            try:
                if ph is None:
                    raise RuntimeError("argon2-cffi required")
                ph.verify(password_hash, password)
                # success: reset counters
                cur.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?", (user_id,))
                conn.commit()
                cur.execute("SELECT key,label FROM roles WHERE id = ?", (role_id,))
                role_row = cur.fetchone()
                role = {"key": role_row[0], "label": role_row[1]} if role_row else {"key": "unknown", "label": "Unknown"}
                return {"id": user_id, "username": username, "role": role}
            except Exception:
                # failure: increment failed_attempts and maybe lock
                failed_attempts = (failed_attempts or 0) + 1
                locked_until_val = None
                if failed_attempts >= DEFAULT_LOCKOUT_THRESHOLD:
                    locked_until_val = (datetime.utcnow() + timedelta(minutes=DEFAULT_LOCKOUT_MINUTES)).isoformat()
                cur.execute("UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?", (failed_attempts, locked_until_val, user_id))
                conn.commit()
                return None

    def list_users(self):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT u.id,u.username,r.key FROM users u JOIN roles r ON u.role_id=r.id")
            return cur.fetchall()

    def record_audit(self, user_id: Optional[int], event_type: str, detail: Optional[str] = None):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO audit_events(user_id,event_type,detail,created_at) VALUES (?,?,?,?)",
                (user_id, event_type, detail, datetime.utcnow().isoformat()),
            )
            conn.commit()
