"""
Authentication Routes
Handles student registration, login, admin login,
forgot password, reset password, and email verification
"""

from flask import Blueprint, request, jsonify, redirect
from datetime import datetime, timedelta
import secrets

from backend.services.auth_service import (
    student_login,
    student_register,
    admin_login,
    get_current_user,
    get_user_by_email,
    save_reset_token,
    get_user_by_reset_token,
    update_user_password,
    clear_reset_token,
    create_access_token  # ✅ REQUIRED FOR AUTO LOGIN
)

from backend.models.database import SessionLocal, User
from backend.utils.mailer import send_reset_email, send_verification_email

auth_bp = Blueprint("auth", __name__)


# ======================================================
# STUDENT LOGIN
# ======================================================
@auth_bp.route("/login", methods=["POST"])
def login_route():
    data = request.get_json() or {}

    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required"
        }), 200

    result = student_login(email, password)
    return jsonify(result), 200


# ======================================================
# STUDENT REGISTER
# ======================================================
@auth_bp.route("/register", methods=["POST"])
def register_route():
    data = request.get_json() or {}

    result = student_register(
        username=data.get("username", "").strip(),
        email=data.get("email", "").strip(),
        password=data.get("password", ""),
        mobile_number=data.get("mobile_number", "").strip(),
        dcet_reg_number=data.get("dcet_reg_number", "").strip(),
        college_name=data.get("college_name", "").strip()
    )

    # 🔔 Send verification email ONLY if registration succeeded
    if result.get("success") is True:
        db = SessionLocal()
        try:
            user = db.query(User).filter(
                User.email == data.get("email", "").strip().lower()
            ).first()

            if user and user.email_verify_token:
                verify_link = (
                    f"http://127.0.0.1:5000/auth/verify-email/"
                    f"{user.email_verify_token}"
                )
                send_verification_email(user.email, verify_link)
        finally:
            db.close()

    return jsonify(result), 200


# ======================================================
# ADMIN LOGIN
# ======================================================
@auth_bp.route("/admin-login", methods=["POST"])
def admin_login_route():
    data = request.get_json() or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required"
        }), 200

    result = admin_login(username, password)
    return jsonify(result), 200


# ======================================================
# VERIFY TOKEN (SESSION CHECK)
# ======================================================
@auth_bp.route("/verify-token", methods=["GET"])
def verify_token_route():
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return jsonify({
            "success": False,
            "message": "No token provided"
        }), 401

    token = auth_header.split(" ")[1]
    user = get_current_user(token)

    if user:
        return jsonify({
            "success": True,
            "user": user
        }), 200

    return jsonify({
        "success": False,
        "message": "Invalid token"
    }), 401


# ======================================================
# FORGOT PASSWORD
# ======================================================
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password_route():
    data = request.get_json() or {}
    email = data.get("email", "").strip()

    if not email:
        return jsonify({"success": True}), 200

    user = get_user_by_email(email)
    if not user:
        return jsonify({"success": True}), 200

    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(minutes=30)

    save_reset_token(user["id"], token, expiry)

    reset_link = f"http://127.0.0.1:5000/reset-password/{token}"
    send_reset_email(email, reset_link)

    return jsonify({
        "success": True,
        "message": "Password reset link sent to your email"
    }), 200


# ======================================================
# RESET PASSWORD
# ======================================================
@auth_bp.route("/reset-password/<token>", methods=["POST"])
def reset_password_route(token):
    data = request.get_json() or {}
    new_password = data.get("password", "")

    if not new_password:
        return jsonify({
            "success": False,
            "message": "Password is required"
        }), 200

    user = get_user_by_reset_token(token)
    if not user:
        return jsonify({
            "success": False,
            "message": "Invalid or expired reset link"
        }), 200

    update_user_password(user["id"], new_password)
    clear_reset_token(user["id"])

    return jsonify({
        "success": True,
        "message": "Password updated successfully"
    }), 200


# ======================================================
# EMAIL VERIFICATION → AUTO LOGIN + REDIRECT ✅
# ======================================================
@auth_bp.route("/verify-email/<token>", methods=["GET"])
def verify_email_route(token):
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.email_verify_token == token,
            User.email_verify_token_expiry > datetime.utcnow()
        ).first()

        if not user:
            return redirect("/?verify=failed")

        # ✅ VERIFY EMAIL
        user.email_verified = True
        user.email_verify_token = None
        user.email_verify_token_expiry = None
        db.commit()

        # ✅ AUTO LOGIN
        jwt_token = create_access_token(user.id, user.role)

        # ✅ REDIRECT WITH TOKEN
        return redirect(f"/dashboard?token={jwt_token}")

    finally:
        db.close()
