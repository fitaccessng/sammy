"""
Script to consolidate all route files into app.py
This will create a single monolithic app.py file with all routes
WARNING: This creates a very large (~17,500 line) file
"""
import os
import re

def read_file(filepath):
    """Read file content"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return ""

def extract_routes_from_blueprint(content, blueprint_name):
    """Extract routes from blueprint file, removing blueprint references"""
    # Remove blueprint creation line
    content = re.sub(r'^\s*\w+_bp\s*=\s*Blueprint\([^)]+\).*$', '', content, flags=re.MULTILINE)
    
    # Replace @blueprint_bp.route with @app.route
    content = re.sub(r'@\w+_bp\.route\(', '@app.route(', content)
    
    # Remove blueprint imports
    content = re.sub(r'from flask import.*Blueprint.*', 'from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, current_app', content)
    
    return content

def consolidate_routes():
    """Main consolidation function"""
    base_path = r"c:\Users\Nwakanma\Desktop\Fitaccess\sammy"
    routes_path = os.path.join(base_path, "routes")
    
    # Read current app.py
    current_app = read_file(os.path.join(base_path, "app.py"))
    
    # Get all route files
    route_files = [
        'main.py',
        'files.py', 
        'dashboard.py',
        'cost_control.py',
        'hq.py',
        'procurement.py',
        'quarry.py',
        'finance.py',
        'hr.py',
        'admin.py',
        'admin_clean.py',
        'project.py'
    ]
    
    # Start building new app.py
    new_app_content = '''"""
CONSOLIDATED APP.PY
All routes consolidated from separate blueprint files
WARNING: This is a very large file (~17,500+ lines)
Generated automatically by consolidate_routes.py
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, current_app
from flask_wtf.csrf import CSRFProtect, generate_csrf
from dotenv import load_dotenv
from extensions import db, migrate, mail
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
import os
import secrets
from datetime import timedelta, datetime
import logging
from werkzeug.utils import secure_filename
from utils.decorators import role_required
from utils.constants import Roles
from utils.email import send_verification_email, send_email
from models import *
import pandas as pd
from io import BytesIO
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
import random
import string
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Load environment variables
    load_dotenv()
    
    # Security Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('WTF_CSRF_SECRET_KEY')
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['DEBUG'] = True
    
    # Database Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///sammy.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Mail Configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 2525))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    app.config['MAIL_DEBUG'] = os.environ.get('MAIL_DEBUG', 'True').lower() == 'true'
    
    # Upload folder
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    
    # Initialize extensions
    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    # Add CSRF token to all templates
    @app.context_processor
    def inject_csrf_token():
        try:
            from flask import has_request_context, request as flask_request
            if has_request_context() and flask_request:
                token = generate_csrf()
                return dict(csrf_token=token)
            else:
                return dict(csrf_token='')
        except Exception as e:
            print(f"CSRF token generation error: {e}")
            return dict(csrf_token='')
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request_error(error):
        if "CSRF" in str(error):
            flash("The form expired. Please refresh the page and try again.", "error")
            from flask import request as flask_request
            referer = flask_request.headers.get('Referer')
            if referer:
                return redirect(referer)
            return redirect(url_for('dashboard'))
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden_error(error):
        flash("You don't have permission to access this resource.", "error")
        return render_template('errors/403.html'), 403
    
    # Initialize LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # ============================================================================
    # HELPER FUNCTIONS
    # ============================================================================
    
    def get_dashboard_route(role):
        """Get dashboard route based on user role"""
        dashboard_routes = {
            Roles.SUPER_HQ: 'dashboard',
            Roles.HQ_FINANCE: 'finance_home',
            Roles.HQ_HR: 'hr_home',
            Roles.HQ_PROCUREMENT: 'procurement_home',
            Roles.QUARRY_MANAGER: 'quarry_home',
            Roles.PROJECT_MANAGER: 'project_home',
            Roles.FINANCE_STAFF: 'staff_home',
            Roles.HR_STAFF: 'staff_home',
            Roles.PROCUREMENT_STAFF: 'staff_home',
            Roles.QUARRY_STAFF: 'staff_home',
            Roles.PROJECT_STAFF: 'staff_home'
        }
        return dashboard_routes.get(role, 'main_home')
    
'''
    
    print("Starting consolidation...")
    print(f"Base path: {base_path}")
    print(f"Routes path: {routes_path}")
    
    # Add routes from each file
    for route_file in route_files:
        filepath = os.path.join(routes_path, route_file)
        if os.path.exists(filepath):
            print(f"Processing {route_file}...")
            content = read_file(filepath)
            if content:
                # Remove imports and blueprint declarations
                lines = content.split('\n')
                filtered_lines = []
                skip_import = False
                
                for line in lines:
                    # Skip import lines
                    if line.strip().startswith(('from flask import', 'import ', 'from extensions', 'from utils', 'from models', 'from datetime')):
                        continue
                    # Skip blueprint creation
                    if '_bp = Blueprint' in line:
                        continue
                    # Replace blueprint route decorators
                    if '@' in line and '_bp.route' in line:
                        line = line.replace('_bp.route', 'app.route')
                    
                    filtered_lines.append(line)
                
                route_content = '\n'.join(filtered_lines)
                
                # Add section header
                new_app_content += f"\n\n    # {'='*76}\n"
                new_app_content += f"    # ROUTES FROM {route_file.upper()}\n"
                new_app_content += f"    # {'='*76}\n\n"
                
                # Add the route content with proper indentation
                for line in filtered_lines:
                    if line.strip() and not line.strip().startswith('#'):
                        new_app_content += f"    {line}\n"
                    else:
                        new_app_content += f"{line}\n"
        else:
            print(f"File not found: {filepath}")
    
    # Close the create_app function and add main block
    new_app_content += '''
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
'''
    
    # Write the new consolidated app.py
    output_path = os.path.join(base_path, "app_consolidated.py")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(new_app_content)
        print(f"\n✓ Consolidated app.py created: {output_path}")
        print(f"✓ Total size: ~{len(new_app_content)} characters")
        print(f"✓ Estimated lines: ~{len(new_app_content.split(chr(10)))}")
        print("\nNOTE: This file is very large. Review carefully before using.")
        print("To use: Backup your current app.py, then rename app_consolidated.py to app.py")
    except Exception as e:
        print(f"Error writing consolidated file: {e}")

if __name__ == "__main__":
    consolidate_routes()
