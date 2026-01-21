import smtplib
import os
from email.mime.text import MIMEText


# ======================================================
# PASSWORD RESET EMAIL
# ======================================================
def send_reset_email(to_email, reset_link):
    """
    Sends password reset email
    """

    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")

    if not sender_email or not sender_password:
        print("❌ Email credentials not set in .env")
        return

    body = f"""
Hello,

We received a request to reset your password.

Click the link below to reset it:
{reset_link}

This link will expire in 30 minutes.

If you did not request this, please ignore this email.

Regards,
Intelligent DCET Preparation Platform
"""

    msg = MIMEText(body)
    msg["Subject"] = "Password Reset - DCET Platform"
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print(f"✅ Password reset email sent to {to_email}")
    except Exception as e:
        print("❌ Failed to send reset email:", e)


# ======================================================
# EMAIL VERIFICATION EMAIL
# ======================================================
def send_verification_email(to_email, verify_link):
    """
    Sends email verification link after registration
    """

    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")

    if not sender_email or not sender_password:
        print("❌ Email credentials not set in .env")
        return

    body = f"""
Hello,

Welcome to Intelligent DCET Preparation Platform 🎓

Please confirm that this email address belongs to you
by clicking the link below:

{verify_link}

This link will expire in 30 minutes.

If you did not create this account, please ignore this email.

Regards,
Intelligent DCET Team
"""

    msg = MIMEText(body)
    msg["Subject"] = "Confirm Your Email - DCET Platform"
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print(f"✅ Verification email sent to {to_email}")
    except Exception as e:
        print("❌ Failed to send verification email:", e)
