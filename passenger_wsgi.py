import sys
import os

# Add your project directory to the sys.path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import the Flask application
from app import app as application

# This is for Passenger WSGI
if __name__ == '__main__':
    application.run()
