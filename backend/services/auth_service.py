"""
Authentication Service
Handles:
- Student register
- Student login
- Admin login
- JWT token
- Forgot password
- Reset password
- Email verification (optional, NOT blocking login)
- Password strength validation
"""

import os
import re
import secrets
from datetime import datetime, timedelta
import jwt
from passlib.hash import pbkdf2_sha256

from backend.models.database import SessionLocal, User

# ======================================================
# CONFIG
# ======================================================
SECRET_KEY = os.environ.get("SESSION_SECRET", "dcet-quiz-secret-key-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
EMAIL_VERIFY_EXPIRE_MINUTES = 30


# ======================================================
# PASSWORD STRENGTH VALIDATION
# ======================================================
def validate_password_strength(password: str):
    if len(password) < 8:
        return "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return "Password must contain at least one number"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character"
    return None


# ======================================================
# EMAIL VERIFICATION HELPERS
# ======================================================
def create_email_verification_token():
    return secrets.token_urlsafe(32)


# ======================================================
# STUDENT REGISTER
# ======================================================
def student_register(
    email: str,
    password: str,
    username: str,
    dcet_reg_number: str,
    college_name: str,
    mobile_number: str = None
):
    db = SessionLocal()
    try:
        email = email.strip().lower()
        username = username.strip()

        password_error = validate_password_strength(password)
        if password_error:
            return {"success": False, "message": password_error}

        # ✅ Prevent duplicate email
        if db.query(User).filter(User.email == email).first():
            return {"success": False, "message": "Email already registered"}

        # ✅ Prevent duplicate username (FIXES 500 ERROR)
        if db.query(User).filter(User.username == username).first():
            return {"success": False, "message": "Username already taken"}

        verify_token = create_email_verification_token()
        verify_expiry = datetime.utcnow() + timedelta(
            minutes=EMAIL_VERIFY_EXPIRE_MINUTES
        )

        user = User(
            email=email,
            password_hash=pbkdf2_sha256.hash(password),
            username=username,
            dcet_reg_number=dcet_reg_number.strip(),
            college_name=college_name.strip(),
            mobile_number=mobile_number.strip() if mobile_number else None,
            role="student",

            # 🔹 Email verification is OPTIONAL
            email_verified=False,
            email_verify_token=verify_token,
            email_verify_token_expiry=verify_expiry
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "success": True,
            "message": "Registration successful. Verification email sent.",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role
            }
        }
    finally:
        db.close()


# ======================================================
# STUDENT LOGIN (EMAIL VERIFICATION DOES NOT BLOCK LOGIN)
# ======================================================
def student_login(email: str, password: str):
    db = SessionLocal()
    try:
        email = email.strip().lower()
        user = db.query(User).filter(User.email == email).first()

        if not user:
            return {"success": False, "message": "Invalid email or password"}

        role = (user.role or "").strip().lower()
        if role != "student":
            return {"success": False, "message": "Not a student account"}

        if not pbkdf2_sha256.verify(password, user.password_hash):
            return {"success": False, "message": "Invalid email or password"}

        token = create_access_token(user.id, role)

        return {
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "dcet_reg_number": user.dcet_reg_number,
                "college_name": user.college_name,
                "role": role,
                "email_verified": user.email_verified
            }
        }
    finally:
        db.close()


# ======================================================
# ADMIN LOGIN
# ======================================================
def admin_login(username: str, password: str):
    db = SessionLocal()
    try:
        username = username.strip()
        user = db.query(User).filter(User.username == username).first()

        if not user:
            return {"success": False, "message": "Invalid credentials"}

        role = (user.role or "").strip().lower()
        if role != "admin":
            return {"success": False, "message": "Invalid credentials"}

        if not pbkdf2_sha256.verify(password, user.password_hash):
            return {"success": False, "message": "Invalid credentials"}

        token = create_access_token(user.id, role)

        return {
            "success": True,
            "message": "Admin login successful",
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": role
            }
        }
    finally:
        db.close()


# ======================================================
# JWT HELPERS
# ======================================================
def create_access_token(user_id: int, role: str):
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"success": True, "payload": payload}
    except jwt.ExpiredSignatureError:
        return {"success": False}
    except jwt.InvalidTokenError:
        return {"success": False}


def get_current_user(token: str):
    result = verify_token(token)
    if not result["success"]:
        return None

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == result["payload"]["user_id"]).first()
        if not user:
            return None

        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "mobile_number": user.mobile_number,
            "dcet_reg_number": user.dcet_reg_number,
            "college_name": user.college_name,
            "branch": user.branch,
            "semester": user.semester,
            "target_dcet_year": user.target_dcet_year,
            "role": (user.role or "").strip().lower(),
            "email_verified": user.email_verified
        }
    finally:
        db.close()


# ======================================================
# FORGOT / RESET PASSWORD
# ======================================================
def get_user_by_email(email: str):
    db = SessionLocal()
    try:
        email = email.strip().lower()
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        return {"id": user.id, "email": user.email}
    finally:
        db.close()


def save_reset_token(user_id: int, token: str, expiry: datetime):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.reset_token = token
            user.reset_token_expiry = expiry
            db.commit()
    finally:
        db.close()


def get_user_by_reset_token(token: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.reset_token == token,
            User.reset_token_expiry > datetime.utcnow()
        ).first()
        if not user:
            return None
        return {"id": user.id, "email": user.email}
    finally:
        db.close()


def update_user_password(user_id: int, new_password: str):
    password_error = validate_password_strength(new_password)
    if password_error:
        return {"success": False, "message": password_error}

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.password_hash = pbkdf2_sha256.hash(new_password)
            db.commit()
            return {"success": True}
    finally:
        db.close()


def clear_reset_token(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.reset_token = None
            user.reset_token_expiry = None
            db.commit()
    finally:
        db.close()
