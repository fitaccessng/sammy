from app import create_app
from extensions import db

app = create_app()
with app.app_context():
    # Add status column
    try:
        db.session.execute(db.text('ALTER TABLE budgets ADD COLUMN status VARCHAR(32) DEFAULT "active"'))
        print("Added status column")
    except Exception as e:
        print(f"Status column error (may already exist): {e}")
    
    # Add fiscal_year column
    try:
        db.session.execute(db.text('ALTER TABLE budgets ADD COLUMN fiscal_year INTEGER'))
        print("Added fiscal_year column")
    except Exception as e:
        print(f"Fiscal_year column error (may already exist): {e}")
    
    db.session.commit()
    print("Done!")
