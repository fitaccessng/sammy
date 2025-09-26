from flask import Flask, render_template, session, flash, redirect, url_for
from flask_wtf.csrf import CSRFProtect, generate_csrf
from dotenv import load_dotenv
from extensions import db, migrate, mail
from flask_login import LoginManager
import os
import secrets
from datetime import timedelta
import logging

def create_app():
    app = Flask(__name__)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log')
        ]
    )
    
    # Load environment variables
    load_dotenv()
    
    # Security Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('WTF_CSRF_SECRET_KEY')
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)  # Set session lifetime
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    
    # Initialize CSRF protection with longer timeout
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    # Add CSRF token to all templates
    @app.context_processor
    def inject_csrf_token():
        token = generate_csrf()  # Call the function to generate token
        return dict(csrf_token=token)
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request_error(error):
        if "CSRF" in str(error):
            flash("The form expired. Please try again.", "error")
            return redirect(url_for('main.login'))
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden_error(error):
        flash("You don't have permission to access this resource.", "error")
        return render_template('errors/403.html'), 403

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
    
    # Initialize mail after configuration
    mail.init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Set up upload folder
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')

    # Import blueprints
    from routes.admin import admin_bp
    from routes.finance import finance_bp
    from routes.hr import hr_bp
    from routes.procurement import procurement_bp
    from routes.quarry import quarry_bp
    from routes.project import project_bp
    from routes.main import main_bp
    from routes.files import files_bp
    
    # Register Blueprints with their respective URL prefixes
    app.register_blueprint(main_bp, url_prefix='/')  # No prefix for main routes
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(finance_bp, url_prefix='/finance')
    app.register_blueprint(hr_bp, url_prefix='/hr')
    app.register_blueprint(procurement_bp, url_prefix='/procurement')
    app.register_blueprint(quarry_bp, url_prefix='/quarry')
    app.register_blueprint(project_bp, url_prefix='/project')
    app.register_blueprint(files_bp)
    
    # Initialize LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    from models import Employee
    @login_manager.user_loader
    def load_user(user_id):
        return Employee.query.get(int(user_id))

    return app
