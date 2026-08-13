import sqlite3
from config import DB_PATH

def get_connection():
    return sqlite3.connect(DB_PATH)

def authenticate_user(username: str, password: str):
    """
    Verifies user credentials against SQLite database.
    Returns (True, role) if authenticated, otherwise (False, None).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT password, role
        FROM users
        WHERE username = ?
    """, (username,))

    user = cursor.fetchone()
    conn.close()

    if user:
        stored_password, role = user
        if stored_password == password:
            return True, role

    return False, None