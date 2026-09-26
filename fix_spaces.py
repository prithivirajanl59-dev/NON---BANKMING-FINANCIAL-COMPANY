import sqlite3  # <- this line must be at the top

DB_FILE = "customer.db"

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Add loan_number column if it doesn't exist
try:
    c.execute("ALTER TABLE loan_applications ADD COLUMN loan_number TEXT")
    print("loan_number column added successfully")
except sqlite3.OperationalError:
    print("loan_number column already exists")

conn.commit()
conn.close()
