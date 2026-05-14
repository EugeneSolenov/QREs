import secrets
import sqlite3

from config import DATABASE_PATH


def get_db_connection():
    con = sqlite3.connect(DATABASE_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    con = get_db_connection()
    try:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER PRIMARY KEY,
                role TEXT NOT NULL DEFAULT 'user',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        con.commit()
    finally:
        con.close()


def find_user_by_username(username):
    con = get_db_connection()
    try:
        arr = con.execute(
            """
            SELECT users.id, users.username, users.password, user_roles.role
            FROM users
            LEFT JOIN user_roles ON user_roles.user_id = users.id
            """
        ).fetchall()
    finally:
        con.close()

    for r in arr:
        if secrets.compare_digest(r["username"], username):
            return {
                "id": r["id"],
                "username": r["username"],
                "password": r["password"],
                "role": r["role"] or "user",
            }
    return None


def create_user(username, password_hash, role="user"):
    con = get_db_connection()
    try:
        cur = con.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password_hash),
        )
        uid = cur.lastrowid
        con.execute(
            "INSERT INTO user_roles (user_id, role) VALUES (?, ?)",
            (uid, role),
        )
        con.commit()
    finally:
        con.close()

    u = find_user_by_username(username)
    if u is None:
        raise RuntimeError("Created user was not found")
    return u


def create_todo(title, description):
    con = get_db_connection()
    try:
        cur = con.execute(
            "INSERT INTO todos (title, description, completed) VALUES (?, ?, 0)",
            (title, description),
        )
        tid = cur.lastrowid
        con.commit()
        r = con.execute(
            "SELECT id, title, description, completed FROM todos WHERE id = ?",
            (tid,),
        ).fetchone()
    finally:
        con.close()

    if r is None:
        raise RuntimeError("Created todo was not found")
    return {
        "id": r["id"],
        "title": r["title"],
        "description": r["description"],
        "completed": bool(r["completed"]),
    }


def list_todos():
    con = get_db_connection()
    try:
        arr = con.execute(
            "SELECT id, title, description, completed FROM todos ORDER BY id"
        ).fetchall()
    finally:
        con.close()

    res = []
    for r in arr:
        res.append(
            {
                "id": r["id"],
                "title": r["title"],
                "description": r["description"],
                "completed": bool(r["completed"]),
            }
        )
    return res


def get_todo(todo_id):
    con = get_db_connection()
    try:
        r = con.execute(
            "SELECT id, title, description, completed FROM todos WHERE id = ?",
            (todo_id,),
        ).fetchone()
    finally:
        con.close()

    if not r:
        return None
    return {
        "id": r["id"],
        "title": r["title"],
        "description": r["description"],
        "completed": bool(r["completed"]),
    }


def update_todo(todo_id, title, description, completed):
    con = get_db_connection()
    try:
        cur = con.execute(
            """
            UPDATE todos
            SET title = ?, description = ?, completed = ?
            WHERE id = ?
            """,
            (title, description, int(completed), todo_id),
        )
        con.commit()
        if cur.rowcount == 0:
            return None
        r = con.execute(
            "SELECT id, title, description, completed FROM todos WHERE id = ?",
            (todo_id,),
        ).fetchone()
    finally:
        con.close()

    if not r:
        return None
    return {
        "id": r["id"],
        "title": r["title"],
        "description": r["description"],
        "completed": bool(r["completed"]),
    }


def delete_todo(todo_id):
    con = get_db_connection()
    try:
        cur = con.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        con.commit()
        return cur.rowcount > 0
    finally:
        con.close()
