#!/usr/bin/env python
"""Create purchase order tables"""

from flask import Flask
from extensions import db
from models import PurchaseOrder, PurchaseOrderItem, Vendor

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sammy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    # Create the tables
    db.create_all()
    print("✓ Purchase order tables created successfully!")
    
    # Verify tables exist
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    if 'purchase_orders' in tables:
        print("✓ purchase_orders table exists")
    if 'purchase_order_items' in tables:
        print("✓ purchase_order_items table exists")
    
    print("\nAll tables in database:")
    for table in sorted(tables):
        print(f"  - {table}")
