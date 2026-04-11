"""
Email sending utilities using SendGrid.

Handles verification emails and password reset emails.
"""

import logging

from sendgrid import SendGridAPIClient  # type: ignore
from sendgrid.helpers.mail import Mail  # type: ignore

from app.core.config import FROM_EMAIL, SENDGRID_API_KEY

logger = logging.getLogger(__name__)


def send_verification_email(to_email: str, display_name: str, token: str) -> None:
    """Send an email verification token to the user."""
    if not SENDGRID_API_KEY:
        logger.warning("SENDGRID_API_KEY not set — skipping verification email")
        return
    try:
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=to_email,
            subject="Verify your Streamline account",
            html_content=(
                f"<h2>Hi {display_name},</h2>"
                f"<p>Your verification code is:</p>"
                f"<h1 style='letter-spacing:4px'>{token}</h1>"
                f"<p>Enter this code in the app to verify your account.</p>"
                f"<p>This code expires in <strong>24 hours</strong>.</p>"
            ),
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
    except Exception as e:
        logger.error("Failed to send verification email to %s: %s", to_email, e)


def send_password_reset_email(to_email: str, display_name: str, token: str) -> None:
    """Send a password reset token to the user."""
    if not SENDGRID_API_KEY:
        logger.warning("SENDGRID_API_KEY not set — skipping password reset email")
        return
    try:
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=to_email,
            subject="Reset your Streamline password",
            html_content=(
                f"<h2>Hi {display_name},</h2>"
                f"<p>Your password reset code is:</p>"
                f"<h1 style='letter-spacing:4px'>{token}</h1>"
                f"<p>Enter this code in the app to reset your password.</p>"
                f"<p>This code expires in <strong>1 hour</strong>.</p>"
                f"<p>If you did not request this, ignore this email.</p>"
            ),
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
    except Exception as e:
        logger.error("Failed to send password reset email to %s: %s", to_email, e)
