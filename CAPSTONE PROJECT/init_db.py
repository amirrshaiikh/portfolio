import sqlite3

conn = sqlite3.connect("vehicles.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS Vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number TEXT UNIQUE NOT NULL,
    is_allowed INTEGER NOT NULL
)
""")

# Sample Data
cursor.execute(
    "INSERT OR IGNORE INTO Vehicles (plate_number, is_allowed) VALUES (?, ?)",
    ("MH12AB1234", 1)
)

cursor.execute(
    "INSERT OR IGNORE INTO Vehicles (plate_number, is_allowed) VALUES (?, ?)",
    ("RJ45SH7917", 0)
)

conn.commit()
conn.close()

print("Database initialized successfully.")