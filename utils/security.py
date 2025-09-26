from functools import wraps
from flask import request, session, abort

def csrf_protect(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "POST":
            token = session.get('csrf_token')
            if not token or token != request.form.get('csrf_token'):
                abort(403)
        return f(*args, **kwargs)
    return decorated_function