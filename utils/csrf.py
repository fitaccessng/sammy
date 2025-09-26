from functools import wraps
from flask import request, session, abort

def csrf_protect(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "POST":
            token = session.get('csrf_token')
            form_token = request.form.get('csrf_token')
            
            # Debug print statements (remove in production)
            print(f"Session token: {token}")
            print(f"Form token: {form_token}")
            
            if not token or not form_token or token != form_token:
                abort(403)
        return f(*args, **kwargs)
    return decorated_function