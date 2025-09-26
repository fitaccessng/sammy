from app import create_app
import os
from flask import Flask
from flask_talisman import Talisman
import logging
from logging.handlers import RotatingFileHandler
from flask_login import LoginManager
from models import User

# Set development mode environment variable
os.environ['FLASK_ENV'] = 'development'

# Create the application instance
app = create_app()

# Apply Flask-Talisman for security headers (temporarily relax CSP for Tailwind CDN and inline styles/scripts)
csp = {
    'default-src': [
        '\'self\'',
        'https://cdn.tailwindcss.com',
        'https://fonts.googleapis.com',
        'https://fonts.gstatic.com',
        'https://code.jquery.com'
    ],
    'script-src': [
        '\'self\'',
        'https://cdn.tailwindcss.com',
        'https://code.jquery.com',
        '\'unsafe-inline\''
    ],
    'style-src': [
        '\'self\'',
        'https://fonts.googleapis.com',
        'https://cdn.tailwindcss.com',
        '\'unsafe-inline\''
    ]
}

Talisman(app, content_security_policy=csp)

# Structured logging setup
log_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')
handler = RotatingFileHandler(log_file, maxBytes=1000000, backupCount=3)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Example usage in routes:
# app.logger.info('App started')
# app.logger.error('An error occurred')

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Configure development settings
if __name__ == "__main__":
    app.config['DEBUG'] = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True
    
    # Run the development server
    app.run(
        host='0.0.0.0',  # Allow external access
        port=5000,       # Default Flask port
        debug=True,      # Enable debug mode
        use_reloader=True  # Enable auto-reload on code changes
    )