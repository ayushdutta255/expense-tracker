"""Database functions for PennyWise (SQLite).

All the SQL lives in this file, so app.py only has to call simple functions.
Every query uses ? placeholders. This keeps the database safe from SQL injection.
"""
import os
import sqlite3

# The database file is stored next to this file
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pennywise.db")


def connect():
    """Open a connection to the database."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row  # lets us write row["amount"]
    return connection


def query(sql, params=()):
    """Run a SELECT and return all the rows."""
    connection = connect()
    try:
        return connection.execute(sql, params).fetchall()
    finally:
        connection.close()


def execute(sql, params=()):
    """Run an INSERT / UPDATE / DELETE and save the change."""
    connection = connect()
    try:
        cursor = connection.execute(sql, params)
        connection.commit()
        return cursor.rowcount
    finally:
        connection.close()


def create_tables():
    """Create the tables if they do not exist yet (runs every time the app starts)."""
    execute(
        """CREATE TABLE IF NOT EXISTS transactions (
               id       INTEGER PRIMARY KEY AUTOINCREMENT,
               kind     TEXT NOT NULL,     -- 'income' or 'expense'
               amount   REAL NOT NULL,
               category TEXT NOT NULL,
               note     TEXT,              -- the short description
               spent_on TEXT NOT NULL      -- the date, written as YYYY-MM-DD
           )"""
    )
    execute(
        """CREATE TABLE IF NOT EXISTS monthly_budget (
               month  TEXT PRIMARY KEY,    -- for example '2026-11'
               amount REAL NOT NULL
           )"""
    )


# ---------- Transactions ----------
def add_transaction(kind, amount, category, description, date_text):
    execute(
        "INSERT INTO transactions (kind, amount, category, note, spent_on) VALUES (?, ?, ?, ?, ?)",
        (kind, amount, category, description, date_text),
    )


def update_transaction(transaction_id, kind, amount, category, description, date_text):
    return execute(
        "UPDATE transactions SET kind = ?, amount = ?, category = ?, note = ?, spent_on = ? WHERE id = ?",
        (kind, amount, category, description, date_text, transaction_id),
    )


def delete_transaction(transaction_id):
    return execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))


def search_transactions(text, category, date_from, date_to):
    """Return transactions, newest first. Empty filters are ignored."""
    sql = "SELECT * FROM transactions WHERE 1 = 1"
    params = []
    if text:
        sql += " AND note LIKE ?"
        params.append("%" + text + "%")
    if category:
        sql += " AND category = ?"
        params.append(category)
    if date_from:
        sql += " AND spent_on >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND spent_on <= ?"
        params.append(date_to)
    sql += " ORDER BY spent_on DESC, id DESC"
    return query(sql, params)


# ---------- Totals ----------
def get_totals(month=None):
    """Return (total_income, total_expenses).
    Give a month like '2026-11' for that month only, or nothing for all time."""
    sql = "SELECT kind, SUM(amount) AS total FROM transactions"
    params = ()
    if month:
        sql += " WHERE spent_on LIKE ?"
        params = (month + "-%",)
    sql += " GROUP BY kind"

    income = 0
    expenses = 0
    for row in query(sql, params):
        if row["kind"] == "income":
            income = row["total"]
        else:
            expenses = row["total"]
    return round(income or 0, 2), round(expenses or 0, 2)


def get_category_spending(month):
    """Expenses of one month added up per category, biggest first."""
    return query(
        """SELECT category, ROUND(SUM(amount), 2) AS total FROM transactions
           WHERE kind = 'expense' AND spent_on LIKE ?
           GROUP BY category ORDER BY total DESC""",
        (month + "-%",),
    )


# ---------- Budget ----------
def get_budget(month):
    """Budget for a month. If none was set for it, use the most recent earlier
    budget (so you do not have to set it again every month). None if never set."""
    rows = query(
        "SELECT amount FROM monthly_budget WHERE month <= ? ORDER BY month DESC LIMIT 1",
        (month,),
    )
    if rows:
        return round(rows[0]["amount"], 2)
    return None


def save_budget(month, amount):
    execute("INSERT OR REPLACE INTO monthly_budget (month, amount) VALUES (?, ?)", (month, amount))
