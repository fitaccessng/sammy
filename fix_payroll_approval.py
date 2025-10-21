#!/usr/bin/env python3
"""
Script to check and fix PayrollApproval table
"""

import sqlite3
import os

def fix_payroll_approval_table():
    """Check and fix PayrollApproval table structure"""
    db_path = os.path.join('instance', 'sammy.db')
    
    if not os.path.exists(db_path):
        print("Database file not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if PayrollApproval table exists and has data
    try:
        cursor.execute("SELECT COUNT(*) FROM payroll_approval")
        count = cursor.fetchone()[0]
        print(f"PayrollApproval table has {count} records")
        
        if count == 0:
            print("No data in PayrollApproval table. Safe to recreate.")
            
            # Drop the table
            cursor.execute("DROP TABLE IF EXISTS payroll_approval")
            
            # Create the new table with correct structure
            cursor.execute("""
                CREATE TABLE payroll_approval (
                    id INTEGER PRIMARY KEY,
                    period_year INTEGER NOT NULL,
                    period_month INTEGER NOT NULL,
                    total_amount FLOAT NOT NULL,
                    employee_count INTEGER NOT NULL,
                    status VARCHAR(32) DEFAULT 'pending_admin',
                    submitted_by INTEGER NOT NULL,
                    admin_approved_by INTEGER,
                    finance_processed_by INTEGER,
                    rejected_by INTEGER,
                    submitted_at DATETIME,
                    admin_approved_at DATETIME,
                    finance_processed_at DATETIME,
                    rejected_at DATETIME,
                    rejection_reason TEXT,
                    FOREIGN KEY (submitted_by) REFERENCES user (id),
                    FOREIGN KEY (admin_approved_by) REFERENCES user (id),
                    FOREIGN KEY (finance_processed_by) REFERENCES user (id),
                    FOREIGN KEY (rejected_by) REFERENCES user (id)
                )
            """)
            
            conn.commit()
            print("PayrollApproval table recreated successfully!")
        else:
            print("Table has data. Migration would be needed.")
            
    except sqlite3.Error as e:
        print(f"Error: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    fix_payroll_approval_table()