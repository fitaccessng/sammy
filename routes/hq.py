from flask import Blueprint

hq_bp = Blueprint("hq", __name__)

@hq_bp.route("/")
def hq_home():
    return "HQ Dashboard"
