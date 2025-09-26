from flask import abort, session, redirect, url_for
from flask_login import current_user
from functools import wraps
from .constants import Roles

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('main.login'))
            if not any(current_user.has_role(role) for role in allowed_roles):
                print(f"[DEBUG] role_required: user_role={current_user.role}, allowed_roles={allowed_roles}")
                return "Unauthorized", 401
            return f(*args, **kwargs)
        return decorated_function
    return decorator