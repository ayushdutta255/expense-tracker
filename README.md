# PennyWise

**Personal Expense Tracker and Budget Management System**

PennyWise is a web application for recording income and expenses, tracking a monthly budget and
understanding where your money goes. It is built with **Python (Flask)** and **SQLite**.

## Objectives
- Record income and expense transactions with an amount, category, date and description.
- Keep a complete history of transactions that can be edited, deleted, searched and filtered.
- Calculate total income, total expenses and the available balance automatically.
- Let the user set a monthly budget and see how much is spent and how much remains.
- Show spending by category in a chart, with a short monthly summary.

## Features
- **Dashboard:** total income, total expenses and available balance (all saved transactions).
- **Add, edit and delete** income and expenses. Data is saved in SQLite and is still there after restarting.
- **Categories:** Food, Transportation, Shopping, Bills, Entertainment, Education, Healthcare, Other
  (income categories: Salary, Allowance, Gift, Other income).
- **Monthly budget** with the amount spent, the amount remaining and a progress bar
  (the bar turns coral when you go over budget). A budget stays in use for later months until you change it.
- **Transaction history** showing date, description, category, type (income or expense) and amount.
- **Search and filter** by description, category and date range.
- **Spending by category** doughnut chart for the selected month.
- **Spending Snapshot:** highest spending category, total monthly expenses, remaining budget.
- **Monthly report:** income, expenses and remaining balance, with the arrows to switch months.
- Input checks: invalid amounts, missing fields, invalid or future dates are rejected with a message.
- Responsive white design, made to work on Android phone screens.

## Technologies used
- Python 3 and Flask (web framework)
- SQLite (built into Python, no installation needed)
- HTML (Jinja2 templates), CSS, and a little JavaScript for the pop-up forms and delete confirmation

## Project structure
```
PennyWise/
├── app.py              # Flask routes and input checking
├── database.py         # All SQLite code (tables and SQL queries)
├── requirements.txt    # Python packages (Flask)
├── README.md
├── .gitignore
├── templates/
│   └── index.html      # The page
└── static/
    ├── style.css       # Styling
    └── script.js       # Pop-up forms and delete confirmation
```

## Installation requirements
- Python 3.8 or newer
- Flask (installed in step 3 below)

## How to run
1. Open a terminal (or command prompt) inside the `PennyWise` folder.
2. (Optional) create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate          # Windows
   source venv/bin/activate       # macOS / Linux
   ```
3. Install Flask:
   ```
   pip install -r requirements.txt
   ```
4. Start the application:
   ```
   python app.py
   ```
5. Open http://127.0.0.1:5000 in your browser.

To open it on an Android phone, connect the phone to the same Wi-Fi as the computer and open
`http://COMPUTER-IP-ADDRESS:5000` in Chrome (find the address with `ipconfig` on Windows or `ifconfig` on macOS/Linux).

## How the SQLite database is created
Nothing needs to be set up by hand. When the app starts, `database.create_tables()` runs and creates
the file `pennywise.db` next to `app.py` if it does not exist, with two tables:

| Table | Columns |
|---|---|
| `transactions` | id, kind (`income` or `expense`), amount, category, note (the description), spent_on (date as YYYY-MM-DD) |
| `monthly_budget` | month (for example `2026-11`), amount |

The database file is not included in the repository (see `.gitignore`). To start again with empty data, stop the app and delete `pennywise.db`.

## How to use the application
1. Tap **+ Add**, choose **Income** or **Expense**, enter the amount, category, description and date, then save.
2. Use **Set budget** to enter the monthly budget. The progress bar shows how much of it is used.
3. Use the arrows next to the month name to look at other months. The budget, chart, snapshot and monthly report follow the month.
4. Use **Search & filter** in the history to find transactions by description, category or dates.
5. Use the pencil to edit a transaction and the × to delete it.

## Expected workflow
Add income → add expenses → expenses are categorized → the balance is calculated → check the chart and monthly report → monitor the budget.

Example: income ₹40,000 and expenses Food ₹6,000, Transportation ₹3,000, Shopping ₹5,000, Bills ₹7,000 and
Entertainment ₹2,000 give total expenses of ₹23,000 and a remaining balance of ₹17,000.

## Notes and limitations
- There is no user login. The app is meant for one person on one computer.
- The page font loads from Google Fonts. Without internet a standard system font is used instead and everything else still works.
- The date of a transaction cannot be in the future.
