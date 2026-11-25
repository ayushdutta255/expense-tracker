import os
import sqlite3

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pennywise.db")

def connect():

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def query(sql, params=()):

    connection = connect()
    try:
        return connection.execute(sql, params).fetchall()
    finally:
        connection.close()

def execute(sql, params=()):

    connection = connect()
    try:
        cursor = connection.execute(sql, params)
        connection.commit()
        return cursor.rowcount
    finally:
        connection.close()

def create_tables():

    execute(
        """CREATE TABLE IF NOT EXISTS transactions (
               id       INTEGER PRIMARY KEY AUTOINCREMENT,
               kind     TEXT NOT NULL,
               amount   REAL NOT NULL,
               category TEXT NOT NULL,
               note     TEXT,
               spent_on TEXT NOT NULL
           )"""
    )
    execute(
        """CREATE TABLE IF NOT EXISTS monthly_budget (
               month  TEXT PRIMARY KEY,
               amount REAL NOT NULL
           )"""
    )

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

def get_totals(month=None):

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

    return query(
        """SELECT category, ROUND(SUM(amount), 2) AS total FROM transactions
           WHERE kind = 'expense' AND spent_on LIKE ?
           GROUP BY category ORDER BY total DESC""",
        (month + "-%",),
    )

def get_budget(month):

    rows = query(
        "SELECT amount FROM monthly_budget WHERE month <= ? ORDER BY month DESC LIMIT 1",
        (month,),
    )
    if rows:
        return round(rows[0]["amount"], 2)
    return None

def save_budget(month, amount):
    execute("INSERT OR REPLACE INTO monthly_budget (month, amount) VALUES (?, ?)", (month, amount))
