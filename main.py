import os
import asyncio
import json
from fastmcp import FastMCP
import aiosqlite

DB_PATH = os.path.join(os.path.dirname(__file__), 'expenses.db')
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), 'categories.json')

mcp = FastMCP("Expense Tracker", "Track your expenses easily")

async def init_db():
    """Initialize the database with the expenses table."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT NOT NULL,
                note TEXT DEFAULT ''
            )
        """)
        await db.commit()

@mcp.tool()
async def add_expense(date: str, amount: float, category: str, subcategory: str, note: str = ""):
    """Add a new expense to the tracker."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO expenses (date, amount, category, subcategory, note)
            VALUES (?, ?, ?, ?, ?)
        """, (date, amount, category, subcategory, note))
        await db.commit()
        last_id = db.lastrowid
    return {"status": "success", "id": last_id}

@mcp.tool()
async def list_expenses():
    """List all expenses."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT id, date, amount, category, subcategory, note FROM expenses")
        rows = await cursor.fetchall()
        return {"expenses": [dict(row) for row in rows]}

@mcp.tool()
async def summarize_expenses(start_date: str = None, end_date: str = None):
    """Summarize expenses by category within an optional date range."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE (? IS NULL OR date >= ?)
              AND (? IS NULL OR date <= ?)
            GROUP BY category
        """, (start_date, start_date, end_date, end_date))
        rows = await cursor.fetchall()
        return {"summary": {row[0]: row[1] for row in rows}}

@mcp.resource("expenses://categories", mime_type="application/json")
async def categories():
    """Get available expense categories."""
    loop = asyncio.get_event_loop()
    def read_categories():
        with open(CATEGORIES_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    return await loop.run_in_executor(None, read_categories)

async def main():
    """Initialize database and run the MCP server."""
    await init_db()
    mcp.run(transport="http", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    asyncio.run(main())