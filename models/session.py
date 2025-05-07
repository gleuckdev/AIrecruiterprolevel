"""
Session Model for AI Recruiter Pro
This module contains the Session model for tracking user login sessions.
"""

import hashlib
import hmac
import os
import uuid
from datetime import datetime

from flask import current_app

from .base import db


class Session(db.Model):
    """
    Represents a user session for authentication.
    Associates JWT tokens with recruiter accounts and tracks expiration.

    This model stores:
    - When the session expires
    - IP address and user agent for security auditing
    - Timestamps for tracking
    - Token hash for revocation
    - Activity status for session management
    - Device info and last activity for security auditing
    """

    __tablename__ = "sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recruiter_id = db.Column(db.Integer, db.ForeignKey("recruiters.id"), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    # Enhanced security fields (added via migration)
    token_hash = db.Column(db.String(100), nullable=True, index=True)  # Keyed hash of the token
    is_active = db.Column(db.Boolean, default=True)  # For session tracking/revocation
    last_activity = db.Column(db.DateTime, nullable=True)  # For tracking user activity
    device_info = db.Column(db.String(255), nullable=True)  # For device fingerprinting

    # Relationships
    recruiter = db.relationship("Recruiter", backref=db.backref("sessions", lazy=True))

    @staticmethod
    def hash_token(token, secret_key=None):
        """
        Create a keyed hash of a JWT token for secure storage.

        Args:
            token: The JWT token to hash
            secret_key: Secret key for HMAC (defaults to app's secret_key)

        Returns:
            str: The HMAC-SHA256 hexdigest of the token
        """
        # Get secret key from app if not provided
        if not secret_key:
            try:
                secret_key = (
                    current_app.config.get("JWT_SECRET_KEY")
                    or current_app.config.get("SECRET_KEY")
                    or os.environ.get("JWT_SECRET_KEY")
                    or os.environ.get("SECRET_KEY")
                )
            except RuntimeError:
                # Outside app context, use environment directly
                secret_key = os.environ.get("JWT_SECRET_KEY") or os.environ.get("SECRET_KEY")

        if not secret_key:
            # Last resort fallback
            secret_key = "airecruiter_default_session_key"

        # Create HMAC with SHA-256
        return hmac.new(secret_key.encode(), token.encode(), hashlib.sha256).hexdigest()

    @classmethod
    def find_by_token(cls, token):
        """
        Find a session by its JWT token.

        Args:
            token: The JWT token to look up

        Returns:
            Session or None: The session with the matching token hash
        """
        if not token:
            return None

        token_hash = cls.hash_token(token)
        return cls.query.filter_by(token_hash=token_hash, is_active=True).first()

    @classmethod
    def create_session(cls, recruiter_id, expires_at, request=None, token=None):
        """
        Factory method to create a new session with proper tracking data.

        Args:
            recruiter_id: ID of the recruiter/user
            expires_at: When this session expires
            request: Flask request object for IP/agent extraction
            token: JWT token (for token_hash calculation)

        Returns:
            Session: The created session object (unsaved)
        """
        ip = None
        agent = None
        device_info = None

        if request:
            # Get IP address with proxy support
            if request.headers.get("X-Forwarded-For"):
                ip = request.headers.get("X-Forwarded-For").split(",")[0].strip()
            else:
                ip = request.remote_addr

            # Get user agent
            agent = request.user_agent.string if request.user_agent else "Unknown"

            # Create simple device fingerprint from available headers
            platform = request.user_agent.platform if request.user_agent else "Unknown"
            browser = request.user_agent.browser if request.user_agent else "Unknown"
            version = request.user_agent.version if request.user_agent else "Unknown"
            device_info = f"{platform}/{browser} {version}"

        session = cls(
            recruiter_id=recruiter_id,
            expires_at=expires_at,
            ip_address=ip,
            user_agent=agent,
            device_info=device_info,
            last_activity=datetime.utcnow(),
            is_active=True,
        )

        # Hash and store the token if provided
        if token:
            session.token_hash = cls.hash_token(token)

        return session

    def update_activity(self):
        """
        Update the last_activity timestamp to now.
        """
        self.last_activity = datetime.utcnow()
        return self

    def deactivate(self):
        """
        Deactivate this session (mark as logged out or expired).
        """
        self.is_active = False
        return True

    def is_valid(self):
        """
        Check if this session is still valid (not expired, not revoked).
        """
        # Check if expired
        if datetime.utcnow() > self.expires_at:
            return False

        # Check if explicitly deactivated
        return self.is_active

    def get_device_description(self):
        """
        Get a human-friendly description of the device for display.
        """
        if self.device_info:
            return self.device_info
        elif self.user_agent:
            # Try to extract useful info from user agent
            if "iPhone" in self.user_agent or "iPad" in self.user_agent:
                return "iOS Device"
            elif "Android" in self.user_agent:
                return "Android Device"
            elif "Windows" in self.user_agent:
                return "Windows Computer"
            elif "Macintosh" in self.user_agent:
                return "Mac Computer"
            elif "Linux" in self.user_agent:
                return "Linux Computer"
            else:
                return "Unknown Device"
        else:
            return "Unknown Device"

    def __repr__(self):
        status = "Active" if getattr(self, "is_active", True) else "Inactive"
        return f"<Session {self.id[:8]}... ({status}, Recruiter {self.recruiter_id})>"
