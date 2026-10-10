import sqlite3

# Step 1: connect (creates playground.db if it doesn't exist)
conn = sqlite3.connect("playground.db")
cursor = conn.cursor()

# Step 2: create the table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        role TEXT NOT NULL,
        base_salary REAL NOT NULL
    )
""")
employees_to_insert = [
    ("John Doe", "Manager", 5000.0),
    ("Jane Smith", "Developer", 4000.0),
    ("Bob Wilson", "Intern", 2000.0),
]

for name, role, salary in employees_to_insert:
    try:
        cursor.execute(
            "INSERT INTO employees (name, role, base_salary) VALUES (?, ?, ?)",
            (name, role, salary)
        )
    except sqlite3.IntegrityError as e:
        print(f"Skipping '{name}': {e}")
# Step 4: commit so the writes are actually saved to disk
conn.commit()

# Step 5: read everything back
cursor.execute("SELECT * FROM employees")
rows = cursor.fetchall()

for row in rows:
    print(row)

# Step 6: read just the Developer
cursor.execute(
    "SELECT * FROM employees WHERE role = ?",
    ("Developer",)
)

developer = cursor.fetchone()
print("Developer:", developer)

# Close the database connection
conn.close()