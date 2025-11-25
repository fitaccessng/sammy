"""
Add workflow fields to purchase_order table
"""
from app import create_app
from extensions import db

def add_workflow_columns():
    """Add workflow-related columns to purchase_order table"""
    app = create_app()
    
    with app.app_context():
        print("Adding workflow columns to purchase_order table...")
        
        try:
            # Add workflow_id column
            db.session.execute(db.text("""
                ALTER TABLE purchase_order 
                ADD COLUMN workflow_id INTEGER;
            """))
            print("✓ Added workflow_id column")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("✓ workflow_id column already exists")
            else:
                print(f"✗ Error adding workflow_id: {e}")
        
        try:
            # Add cost_control_approved_by column
            db.session.execute(db.text("""
                ALTER TABLE purchase_order 
                ADD COLUMN cost_control_approved_by INTEGER;
            """))
            print("✓ Added cost_control_approved_by column")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("✓ cost_control_approved_by column already exists")
            else:
                print(f"✗ Error adding cost_control_approved_by: {e}")
        
        try:
            # Add cost_control_approved_at column
            db.session.execute(db.text("""
                ALTER TABLE purchase_order 
                ADD COLUMN cost_control_approved_at DATETIME;
            """))
            print("✓ Added cost_control_approved_at column")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("✓ cost_control_approved_at column already exists")
            else:
                print(f"✗ Error adding cost_control_approved_at: {e}")
        
        try:
            # Add cost_control_comments column
            db.session.execute(db.text("""
                ALTER TABLE purchase_order 
                ADD COLUMN cost_control_comments TEXT;
            """))
            print("✓ Added cost_control_comments column")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("✓ cost_control_comments column already exists")
            else:
                print(f"✗ Error adding cost_control_comments: {e}")
        
        try:
            # Add finance_approved_by column
            db.session.execute(db.text("""
                ALTER TABLE purchase_order 
                ADD COLUMN finance_approved_by INTEGER;
            """))
            print("✓ Added finance_approved_by column")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("✓ finance_approved_by column already exists")
            else:
                print(f"✗ Error adding finance_approved_by: {e}")
        
        try:
            # Add finance_approved_at column
            db.session.execute(db.text("""
                ALTER TABLE purchase_order 
                ADD COLUMN finance_approved_at DATETIME;
            """))
            print("✓ Added finance_approved_at column")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("✓ finance_approved_at column already exists")
            else:
                print(f"✗ Error adding finance_approved_at: {e}")
        
        try:
            # Add finance_comments column
            db.session.execute(db.text("""
                ALTER TABLE purchase_order 
                ADD COLUMN finance_comments TEXT;
            """))
            print("✓ Added finance_comments column")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("✓ finance_comments column already exists")
            else:
                print(f"✗ Error adding finance_comments: {e}")
        
        # Commit changes
        db.session.commit()
        print("\n✅ Successfully added workflow columns to purchase_order table!")
        
        # Verify columns
        result = db.session.execute(db.text("PRAGMA table_info(purchase_order)"))
        columns = [row[1] for row in result]
        
        print("\nVerifying columns:")
        required_columns = [
            'workflow_id',
            'cost_control_approved_by',
            'cost_control_approved_at',
            'cost_control_comments',
            'finance_approved_by',
            'finance_approved_at',
            'finance_comments'
        ]
        
        for col in required_columns:
            if col in columns:
                print(f"  ✓ {col}")
            else:
                print(f"  ✗ {col} - MISSING!")

if __name__ == '__main__':
    add_workflow_columns()
