import sqlite3, os

DB_FILE = os.path.join(os.path.dirname(__file__), "bank.db")

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

try:
    # Try adding the column
    c.execute("ALTER TABLE loan_applications ADD COLUMN loan_number TEXT")
    conn.commit()
    print("✅ loan_number column added successfully.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("ℹ️ Column 'loan_number' already exists.")
    else:
        print("⚠️ Error:", e)
finally:
    conn.close()
