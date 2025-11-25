"""
Migration script to add cost_approvals table
"""
import sqlite3
from datetime import datetime

def migrate():
    conn = sqlite3.connect('instance/sammy.db')
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cost_approvals'")
    if cursor.fetchone():
        print("✓ 'cost_approvals' table already exists")
        conn.close()
        return
    
    # Create cost_approvals table
    cursor.execute('''
    CREATE TABLE cost_approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reference_type VARCHAR(64) NOT NULL,
        reference_id INTEGER NOT NULL,
        project_id INTEGER NOT NULL,
        required_role VARCHAR(64) NOT NULL,
        amount FLOAT NOT NULL,
        description TEXT NOT NULL,
        status VARCHAR(32) DEFAULT 'pending',
        approver_id INTEGER,
        approved_at DATETIME,
        comments TEXT,
        action_taken VARCHAR(32),
        created_by INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id),
        FOREIGN KEY (approver_id) REFERENCES user(id),
        FOREIGN KEY (created_by) REFERENCES user(id)
    )
    ''')
    
    conn.commit()
    print("✓ Created 'cost_approvals' table successfully")
    conn.close()

if __name__ == '__main__':
    migrate()
