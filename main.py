import os
from fastmcp import FastMCP
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), 'expenses.db')
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), 'categories.json')

mcp = FastMCP("Expense Tracker", "Track your expenses easily")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT NOT NULL,
                note TEXT DEFAULT ''
            )
        """)

init_db()

@mcp.tool()
def add_expense(date: str, amount: float, category: str, subcategory: str, note: str = ""):
    """Add a new expense to the tracker."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO expenses (date, amount, category, subcategory, note)
            VALUES (?, ?, ?, ?, ?)
        """, (date, amount, category, subcategory, note))
        last_id = cursor.lastrowid
    return {"status": "success", "id": last_id}

@mcp.tool()
def list_expenses():
    """List all expenses."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT id, date, amount, category, subcategory, note FROM expenses")
        cols = [description[0] for description in cursor.description]
        return {"expenses": [dict(zip(cols, row)) for row in cursor.fetchall()]}

@mcp.tool()
def summarize_expenses(start_date: str = None, end_date: str = None):
    """Summarize expenses by category within an optional date range."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE (? IS NULL OR date >= ?)
              AND (? IS NULL OR date <= ?)
            GROUP BY category
        """, (start_date, start_date, end_date, end_date))
        return {"summary": {row[0]: row[1] for row in cursor.fetchall()}}
    
@mcp.resource("expenses://categories",mime_type="application/json")
def categories():
    with open(CATEGORIES_PATH, 'r',encoding='utf-8') as f:
        return f.read()
    
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)