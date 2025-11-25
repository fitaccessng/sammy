"""
Migration script to add budget_adjustments table
"""
import sqlite3
from datetime import datetime

def migrate():
    conn = sqlite3.connect('instance/sammy.db')
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='budget_adjustments'")
    if cursor.fetchone():
        print("✓ 'budget_adjustments' table already exists")
        conn.close()
        return
    
    # Create budget_adjustments table
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
    print("✓ Created 'budget_adjustments' table successfully")
    conn.close()

if __name__ == '__main__':
    migrate()
