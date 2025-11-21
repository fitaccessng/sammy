from app import create_app
from extensions import db

app = create_app()

with app.app_context():
    try:
        # Add purchase_cost column
        db.session.execute(db.text('ALTER TABLE asset ADD COLUMN purchase_cost FLOAT DEFAULT 0.0'))
        print("Added purchase_cost column")
    except Exception as e:
        print(f"purchase_cost column might already exist: {e}")
    
    try:
        # Add current_value column
        db.session.execute(db.text('ALTER TABLE asset ADD COLUMN current_value FLOAT DEFAULT 0.0'))
        print("Added current_value column")
    except Exception as e:
        print(f"current_value column might already exist: {e}")
    
    try:
        # Add depreciation_rate column
        db.session.execute(db.text('ALTER TABLE asset ADD COLUMN depreciation_rate FLOAT DEFAULT 0.0'))
        print("Added depreciation_rate column")
    except Exception as e:
        print(f"depreciation_rate column might already exist: {e}")
    
    db.session.commit()
    print("Asset columns added successfully!")
