from flask import Blueprint

cost_control_bp = Blueprint("cost_control", __name__)

@cost_control_bp.route("/")
def cost_control_home():
    return "cost_control Dashboard"