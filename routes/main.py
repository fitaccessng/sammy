from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user
from models import User, db
from utils.constants import Roles
from utils.email import send_verification_email
import random
import string
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def main_home():
    return render_template("index.html")

@main_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    try:
        if request.method == 'POST':
            name = request.form.get("name")
            email = request.form.get("email")
            role = request.form.get("role")
            password = request.form.get("password")

            # Input validation
            if not all([name, email, role, password]):
                flash("All fields are required", "error")
                return redirect(url_for("main.signup"))

            # Role validation
            if role not in vars(Roles).values():
                flash("Invalid role selected", "error")
                return redirect(url_for("main.signup"))

            # Check existing user
            if User.query.filter_by(email=email).first():
                flash("Email already registered", "error")
                return redirect(url_for("main.signup"))

            # Always set SUPER_HQ for admin/super admin/super_hq
            if str(role).strip().lower() in ["super_hq", "super admin", "admin"]:
                db_role = Roles.SUPER_HQ
            else:
                db_role = role
            new_user = User(name=name, email=email, role=db_role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            # Only store user_id in session
            session["user_id"] = new_user.id
            print("Signed up with role:", db_role)  # Debug
            session.permanent = True
            flash("Account created! Please verify your email.", "success")
            return redirect(url_for("main.login"))

    except Exception as e:
        print(f"Signup error: {str(e)}")  # Debug print
        flash("An error occurred during signup.", "error")
        return redirect(url_for("main.signup"))
        
    return render_template("auth/signup.html")


def get_dashboard_route(role):
    dashboard_routes = {
        # HQ Level Routes
        Roles.SUPER_HQ: 'admin.dashboard',      # Fixed endpoint name
        Roles.HQ_FINANCE: 'finance.finance_home',
        Roles.HQ_HR: 'hr.hr_home',
        Roles.HQ_PROCUREMENT: 'procurement.procurement_home',
        Roles.QUARRY_MANAGER: 'quarry.quarry_home',
        Roles.PROJECT_MANAGER: 'project.project_home',
        # Staff Level Routes
        Roles.FINANCE_STAFF: 'finance.staff_home',
        Roles.HR_STAFF: 'hr.staff_home',
        Roles.PROCUREMENT_STAFF: 'procurement.staff_home',
        Roles.QUARRY_STAFF: 'quarry.staff_home',
        Roles.PROJECT_STAFF: 'project.staff_home'
    }
    return dashboard_routes.get(role, 'main.home')

# Login
@main_bp.route("/login", methods=["GET", "POST"])
def login():
    try:
        if request.method == "POST":
            email = request.form["email"]
            password = request.form["password"]

            user = User.query.filter_by(email=email).first()
            if not user:
                flash("Invalid email or password", "error")
                return render_template("auth/login.html")
            if not user.is_verified:
                try:
                    # Generate new verification code
                    verification_code = ''.join(random.choices(string.digits, k=6))
                    user.verification_code = verification_code
                    db.session.commit()
                    
                    # Send verification email
                    send_verification_email(user.email, verification_code)
                    flash("Please verify your email first. A new verification code has been sent.", "info")
                    return redirect(url_for("main.verify_email_page", email=email))
                    
                except Exception as e:
                    logger.error(f"Verification email error: {str(e)}")
                    db.session.rollback()
                    flash("Unable to send verification email. Please try again later.", "error")
                    return render_template("auth/login.html")
            if user.check_password(password):
                login_user(user)
                session["user_id"] = user.id
                # Normalize dashboard role for super admin, else use user.role
                dashboard_role = user.role
                if str(user.role).strip().upper() in ["super_hq", "super admin", "admin"]:
                    dashboard_role = Roles.SUPER_HQ
                print("Logged in as user_id:", session["user_id"], "dashboard_role:", dashboard_role)  # Debug
                session.permanent = True
                return redirect(url_for(get_dashboard_route(dashboard_role)))
            flash("Invalid email or password", "error")
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        flash("An error occurred. Please try again.", "error")
    return render_template("auth/login.html")

@main_bp.route("/verify-email", methods=["GET", "POST"])
def verify_email_page():
    if request.method == "POST":
        email = request.form.get("email")
        verification_code = request.form.get("verification_code")
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash("Email not found", "error")
            return render_template("auth/verification.html")
            
        if user.verification_code != verification_code:
            flash("Invalid verification code", "error")
            return render_template("auth/verification.html")
            
        user.is_verified = True
        user.verification_code = None
        db.session.commit()
        
        flash("Email verified successfully! You can now login.", "success")
        return redirect(url_for("main.login"))
        
    return render_template("auth/verification.html")


# Forgot Password
@main_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()
        if user:
            token = str(uuid.uuid4())
            user.reset_token = token
            db.session.commit()
            # TODO: send reset email with link
            flash("Password reset link sent to your email.", "info")
        else:
            flash("Email not found", "error")
    return render_template("auth/forgot_password.html")


# Reset Password
@main_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user:
        flash("Invalid or expired token", "error")
        return redirect(url_for("main.login"))

    if request.method == "POST":
        new_password = request.form["password"]
        user.set_password(new_password)
        user.reset_token = None
        db.session.commit()
        flash("Password reset successful! You can now log in.", "success")
        return redirect(url_for("main.login"))

    return render_template("auth/reset_password.html", token=token)


# Email Verification (dummy for now)
@main_bp.route("/verify/<public_id>")
def verify_email(public_id):
    user = User.query.filter_by(public_id=public_id).first()
    if user:
        user.email_verified = True
        db.session.commit()
        flash("Email verified! You can now log in.", "success")
    return redirect(url_for("main.login"))

@main_bp.route('/drop-db', methods=["GET", "POST"])
def drop_db():
    # Only allow if logged in and role is Super Admin or SUPER_HQ
    # if 'user_id' not in session or session.get('role') not in ['Super Admin', 'SUPER_HQ']:
    #     flash('Unauthorized', 'error')
    #     return redirect(url_for('main.login'))
    try:
        db.drop_all()
        db.session.commit()
        flash('Database dropped successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error dropping database: {str(e)}', 'error')
    return redirect(url_for('main.main_home'))


@main_bp.route('/logout')
def logout():
    from flask_login import logout_user
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.login'))

