"""
Verify that cost_approvals and budget_adjustments tables exist
"""
import sqlite3

def verify():
    conn = sqlite3.connect('instance/sammy.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    required_tables = ['cost_approvals', 'budget_adjustments', 'cost_tracking_entries']
    
    print("\nVerifying Cost Control tables:")
    print("-" * 50)
    for table_name in required_tables:
        exists = any(table_name in t for t in tables)
        status = "✓" if exists else "✗"
        print(f"{status} {table_name}")
        
        if exists:
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"  Columns: {len(columns)}")
            for col in columns[:5]:  # Show first 5 columns
                print(f"    - {col[1]} ({col[2]})")
            if len(columns) > 5:
                print(f"    ... and {len(columns) - 5} more columns")
    
    conn.close()
    print("-" * 50)
    print("✓ Verification complete")

if __name__ == '__main__':
    verify()
