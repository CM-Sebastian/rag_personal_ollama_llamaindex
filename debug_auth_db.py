from pathlib import Path
import sqlite3
from src.config import AppConfig

cfg = AppConfig()
db = Path(cfg.auth_db_path)
print('AUTH_DB_PATH=', db)
print('exists=', db.exists())
if db.exists():
    with sqlite3.connect(str(db)) as con:
        cur = con.cursor()
        for t in ['roles', 'users']:
            cur.execute('SELECT name FROM sqlite_master WHERE type="table" AND name=?', (t,))
            print(t, 'exists', cur.fetchone() is not None)
        print('USERS:')
        try:
            cur.execute('SELECT username, role_id, failed_attempts, locked_until, created_at FROM users')
            users = cur.fetchall()
            print(len(users), 'rows')
            for row in users:
                print(row)
        except Exception as e:
            print('USERS_ERROR', e)
        print('ROLES:')
        try:
            cur.execute('SELECT id, key, label FROM roles')
            roles = cur.fetchall()
            print(len(roles), 'rows')
            for row in roles:
                print(row)
        except Exception as e:
            print('ROLES_ERROR', e)
