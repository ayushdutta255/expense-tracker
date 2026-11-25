"""PennyWise - Personal Expense Tracker and Budget Management System.

Flask handles the web pages, database.py handles SQLite.

Run it:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000 in your browser.
"""
import math
import os
from datetime import date, datetime, timedelta

from flask import Flask, flash, redirect, render_template, request, url_for

import database

app = Flask(__name__)
# Flask needs a secret key to show messages like "Transaction added".
# It is not a password, so it is fine to keep it in the code for this project.
app.secret_key = "pennywise-college-project"

CURRENCY = "₹"  # change to "$", "£" ... if you like
MAX_AMOUNT = 10000000

# Each category has an emoji and a colour (used in the list and the chart)
EXPENSE_CATEGORIES = {
    "Food":           {"emoji": "🍜", "color": "#FF7A66"},
    "Transportation": {"emoji": "🚌", "color": "#2F4FD8"},
    "Shopping":       {"emoji": "🛍️", "color": "#7C4DFF"},
    "Bills":          {"emoji": "💡", "color": "#4C9AFF"},
    "Entertainment":  {"emoji": "🎬", "color": "#B983FF"},
    "Education":      {"emoji": "📚", "color": "#5B6CFF"},
    "Healthcare":     {"emoji": "💊", "color": "#1DB9A0"},
    "Other":          {"emoji": "✨", "color": "#F6B93B"},
}
INCOME_CATEGORIES = {
    "Salary":       {"emoji": "💼", "color": "#2F4FD8"},
    "Allowance":    {"emoji": "🎒", "color": "#7C4DFF"},
    "Gift":         {"emoji": "🎁", "color": "#FF7A66"},
    "Other income": {"emoji": "💰", "color": "#4C9AFF"},
}
ALL_CATEGORIES = {**INCOME_CATEGORIES, **EXPENSE_CATEGORIES}


# ---------- Small helper functions ----------
@app.template_filter("money")
def money(value):
    """12345.5 -> '12,345.50'"""
    return "{:,.2f}".format(value or 0)


@app.template_filter("pretty_date")
def pretty_date(value):
    """'2026-11-24' -> '24 Nov 2026'"""
    try:
        d = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return value
    return f"{d.day} {d.strftime('%b')} {d.year}"


def read_amount(text):
    """Turn the typed amount into a number. Returns None if it is not valid."""
    try:
        amount = float(text)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(amount) or amount > MAX_AMOUNT:
        return None
    amount = round(amount, 2)
    if amount <= 0 or amount > MAX_AMOUNT:
        return None
    return amount


def valid_date(text):
    """Return the text if it is a real date like 2026-11-24, otherwise ''."""
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d").date()
        if parsed.year < 2000:
            return ""
        return parsed.isoformat()
    except (TypeError, ValueError):
        return ""


def parse_month(text):
    """Turn '2026-11' into the first day of that month.
    Wrong or future months fall back to the current month."""
    this_month = date.today().replace(day=1)
    try:
        month = datetime.strptime(text, "%Y-%m").date()
    except ValueError:
        return this_month
    if month > this_month or month.year < 2000:
        return this_month
    return month


def read_transaction_form():
    """Check the add / edit form. Returns (data, error_message).
    If something is wrong, data is None and error_message explains what."""
    kind = request.form.get("kind", "")
    category = request.form.get("category", "")
    description = request.form.get("description", "").strip()
    date_text = valid_date(request.form.get("date", "").strip())
    amount = read_amount(request.form.get("amount", ""))

    if kind not in ("income", "expense"):
        return None, "Choose Income or Expense."
    allowed = INCOME_CATEGORIES if kind == "income" else EXPENSE_CATEGORIES
    if amount is None:
        return None, "Enter an amount between 0.01 and 10,000,000."
    if category not in allowed:
        return None, "Choose a category."
    if description == "":
        return None, "Enter a short description."
    if not date_text:
        return None, "Enter a valid date from 1 Jan 2000 onward."
    chosen_date = datetime.strptime(date_text, "%Y-%m-%d").date()
    if chosen_date > date.today():
        return None, "The date cannot be in the future."

    return (kind, amount, category, description[:60], date_text), None


# ---------- Pages ----------
@app.route("/")
def index():
    # 1. Which month are we looking at?  (?month=2026-11)
    first_day = parse_month(request.args.get("month", ""))
    month_key = first_day.strftime("%Y-%m")
    this_month = date.today().replace(day=1)

    # 2. Overall totals (all saved transactions)
    total_income, total_expenses = database.get_totals()
    balance = round(total_income - total_expenses, 2)

    # 3. Totals for the chosen month
    month_income, month_expenses = database.get_totals(month_key)
    month_balance = round(month_income - month_expenses, 2)

    # 4. Spending per category, and the pieces of the doughnut chart
    categories_spent = []
    gradient_parts = []
    start = 0
    for row in database.get_category_spending(month_key):
        share = row["total"] / month_expenses * 100 if month_expenses > 0 else 0
        look = ALL_CATEGORIES.get(row["category"], EXPENSE_CATEGORIES["Other"])
        gradient_parts.append(f"{look['color']} {start:.2f}% {start + share:.2f}%")
        start += share
        categories_spent.append({
            "name": row["category"], "total": row["total"],
            "percent": round(share), "emoji": look["emoji"], "color": look["color"],
        })
    chart_gradient = "conic-gradient(" + ", ".join(gradient_parts) + ")" if gradient_parts else ""
    top_category = categories_spent[0] if categories_spent else None

    # 5. Budget
    budget = database.get_budget(month_key)
    budget_remaining = None
    budget_percent = 0
    if budget is not None:
        budget_remaining = round(budget - month_expenses, 2)
        budget_percent = round(month_expenses / budget * 100) if budget > 0 else 0

    # 6. Bars for the monthly report (the bigger of income / expenses is 100%)
    biggest = max(month_income, month_expenses)
    income_bar = month_income / biggest * 100 if biggest else 0
    expense_bar = month_expenses / biggest * 100 if biggest else 0

    # 7. Transaction history with search and filters
    text = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    if category not in ALL_CATEGORIES:
        category = ""
    date_from = valid_date(request.args.get("from", ""))
    date_to = valid_date(request.args.get("to", ""))
    transactions = database.search_transactions(text, category, date_from, date_to)

    return render_template(
        "index.html",
        currency=CURRENCY,
        expense_categories=EXPENSE_CATEGORIES,
        income_categories=INCOME_CATEGORIES,
        all_categories=ALL_CATEGORIES,
        today=date.today().isoformat(),
        # month navigation
        month_key=month_key,
        month_name=first_day.strftime("%B %Y"),
        prev_month=(first_day - timedelta(days=1)).strftime("%Y-%m"),
        next_month=(first_day + timedelta(days=32)).replace(day=1).strftime("%Y-%m"),
        has_prev=first_day.year > 2000 or first_day.month > 1,
        has_next=first_day < this_month,
        # dashboard
        total_income=total_income, total_expenses=total_expenses, balance=balance,
        # month
        month_income=month_income, month_expenses=month_expenses, month_balance=month_balance,
        categories_spent=categories_spent, chart_gradient=chart_gradient, top_category=top_category,
        income_bar=income_bar, expense_bar=expense_bar,
        # budget
        budget=budget, budget_remaining=budget_remaining,
        budget_percent=budget_percent, budget_bar=min(100, budget_percent),
        # history
        transactions=transactions,
        search_text=text, search_category=category, date_from=date_from, date_to=date_to,
        filters_used=bool(text or category or date_from or date_to),
    )


@app.route("/add", methods=["POST"])
def add_transaction():
    data, error = read_transaction_form()
    if error:
        flash(error, "error")
        return redirect(url_for("index"))
    database.add_transaction(*data)
    flash("Transaction added.", "success")
    return redirect(url_for("index", month=data[4][:7]))   # data[4] is the date


@app.route("/edit/<int:transaction_id>", methods=["POST"])
def edit_transaction(transaction_id):
    data, error = read_transaction_form()
    if error:
        flash(error, "error")
        return redirect(url_for("index"))
    if database.update_transaction(transaction_id, *data) == 0:
        flash("Transaction not found.", "error")
        return redirect(url_for("index", month=data[4][:7]))
    flash("Transaction updated.", "success")
    return redirect(url_for("index", month=data[4][:7]))


@app.route("/delete/<int:transaction_id>", methods=["POST"])
def delete_transaction(transaction_id):
    if database.delete_transaction(transaction_id) == 0:
        flash("Transaction not found.", "error")
    else:
        flash("Transaction deleted.", "success")
    return redirect(url_for("index"))


@app.route("/budget", methods=["POST"])
def set_budget():
    month_key = parse_month(request.form.get("month", "")).strftime("%Y-%m")
    amount = read_amount(request.form.get("amount", ""))
    if amount is None:
        flash("Enter a budget between 0.01 and 10,000,000.", "error")
    else:
        database.save_budget(month_key, amount)
        flash("Budget saved.", "success")
    return redirect(url_for("index", month=month_key))


# Create the database tables when the app starts
database.create_tables()

if __name__ == "__main__":
    # Read the hosting platform's port when available; use 5000 locally.
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
