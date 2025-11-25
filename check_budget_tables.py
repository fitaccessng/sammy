"""
Check budget tables
"""
import sqlite3

conn = sqlite3.connect('instance/sammy.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%budget%'")
tables = cursor.fetchall()
print("Budget tables:")
for t in tables:
    print(f"  - {t[0]}")
conn.close()
