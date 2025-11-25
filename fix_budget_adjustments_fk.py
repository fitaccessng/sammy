"""
Fix budget_adjustments table foreign key
"""
import sqlite3

conn = sqlite3.connect('instance/sammy.db')
cursor = conn.cursor()

# Drop existing table
cursor.execute("DROP TABLE IF EXISTS budget_adjustments")
print("✓ Dropped old budget_adjustments table")

# Create budget_adjustments table with correct foreign key
cursor.execute('''
CREATE TABLE budget_adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    budget_id INTEGER NOT NULL,
    category VARCHAR(64) NOT NULL,
    old_amount FLOAT NOT NULL,
    new_amount FLOAT NOT NULL,
    adjustment_amount FLOAT NOT NULL,
    adjustment_type VARCHAR(32) NOT NULL,
    reason TEXT NOT NULL,
    impact_analysis TEXT,
    status VARCHAR(32) DEFAULT 'pending',
    approved_by INTEGER,
    approved_at DATETIME,
    approval_comments TEXT,
    requested_by INTEGER NOT NULL,
    requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (budget_id) REFERENCES budgets(id),
    FOREIGN KEY (approved_by) REFERENCES user(id),
    FOREIGN KEY (requested_by) REFERENCES user(id)
)
''')

conn.commit()
print("✓ Created budget_adjustments table with correct foreign key")
conn.close()
