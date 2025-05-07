"""
Authentication Models

This module defines all authentication-related models:
- Role and permission models
- TokenBlocklist for JWT token revocation
- Session for tracking user sessions
- PasswordReset for password reset tokens
"""

import logging
import secrets
from datetime import datetime, timedelta

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
)

from extensions import db

# Set up logging
logger = logging.getLogger(__name__)


class TokenBlocklist(db.Model):
    """
    Token Blocklist Model

    Used to store revoked JWT tokens to implement proper logout functionality.
    Tokens in this list are considered invalid and should be rejected by
    the application.
    """

    __tablename__ = "token_blocklist"

    id = Column(Integer, primary_key=True)
    jti = Column(String(36), nullable=False, index=True)
    type = Column(String(16), nullable=False)
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TokenBlocklist {self.jti}>"


# Note: Session model has been moved to models/session.py


class PasswordReset(db.Model):
    """
    Password Reset Model

    Used to store password reset tokens and track their usage.
    """

    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    token = Column(String(64), nullable=False, index=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))
    used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<PasswordReset for user {self.user_id}>"

    def is_valid(self):
        """
        Check if the token is valid (not expired, not used)

        Returns:
            bool: True if valid, False otherwise
        """
        now = datetime.utcnow()
        return not self.used and now < self.expires_at

    def mark_used(self):
        """Mark token as used"""
        self.used = True
        self.used_at = datetime.utcnow()

    @classmethod
    def generate_token(cls, user_id):
        """
        Generate a new password reset token

        Args:
            user_id: ID of the user requesting password reset

        Returns:
            PasswordReset: New password reset token object
        """
        # Generate a secure token
        token = secrets.token_urlsafe(48)

        # Create new password reset
        reset = cls(
            user_id=user_id,
            token=token,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )

        return reset

    @classmethod
    def cleanup_expired_tokens(cls, days=7):
        """
        Clean up expired tokens older than the specified days

        Args:
            days: Number of days after which tokens are cleaned up
        """
        cleanup_date = datetime.utcnow() - timedelta(days=days)
        expired_tokens = cls.query.filter(
            (cls.expires_at < datetime.utcnow()) | (cls.created_at < cleanup_date)
        ).all()

        if expired_tokens:
            for token in expired_tokens:
                db.session.delete(token)
            db.session.commit()
            logger.info(f"Cleaned up {len(expired_tokens)} expired password reset tokens")
