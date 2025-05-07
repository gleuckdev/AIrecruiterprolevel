"""
API models for AI Recruiter Pro.

This module contains models related to API usage tracking, invitations,
and password resets.
"""

from datetime import datetime, timedelta
import uuid
from app.app_factory import db


class ApiLog(db.Model):
    """
    ApiLog model for tracking API usage.
    
    This model stores information about API requests for monitoring,
    debugging, and usage analytics.
    """
    __tablename__ = 'api_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.String(36), nullable=False, index=True)
    path = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    
    # User information
    user_id = db.Column(db.Integer, index=True)
    organization = db.Column(db.String(255))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    
    # Request details
    content_type = db.Column(db.String(100))
    key_type = db.Column(db.String(20))  # api_key, jwt, etc.
    
    # Response details
    status_code = db.Column(db.Integer)
    response_time_ms = db.Column(db.Integer)
    
    # Timestamps
    request_timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    response_timestamp = db.Column(db.DateTime)
    
    # Size tracking
    request_size = db.Column(db.Integer)
    response_size = db.Column(db.Integer)
    
    # Enhanced tracking
    correlation_id = db.Column(db.String(36), index=True)
    api_key_index = db.Column(db.Integer)
    provider_name = db.Column(db.String(50))  # OpenAI, Claude, etc.
    model_name = db.Column(db.String(50))  # GPT-4, claude-3-opus-20240229, etc.
    
    def __repr__(self):
        return f'<ApiLog {self.request_id} {self.path} {self.status_code}>'


class Invitation(db.Model):
    """
    Invitation model for storing and tracking recruiter invitations.
    """
    __tablename__ = 'invitations'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    token = db.Column(db.String(64), nullable=False, unique=True, index=True)
    
    # Role assignment
    role = db.Column(db.String(50), nullable=False, default='recruiter')
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='SET NULL'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime, nullable=True)
    
    # Permissions
    share_jobs = db.Column(db.Boolean, default=False)
    share_candidates = db.Column(db.Boolean, default=False)
    
    # Creator
    created_by = db.Column(db.Integer, db.ForeignKey('recruiters.id', ondelete='SET NULL'), nullable=True)
    
    # Relationships
    creator = db.relationship('Recruiter', backref='sent_invitations')
    assigned_role = db.relationship('Role', backref='invitations')
    
    def __repr__(self):
        return f'<Invitation {self.email} {self.used}>'
    
    @staticmethod
    def generate_token():
        """Generate a secure invitation token."""
        return str(uuid.uuid4())
    
    @staticmethod
    def create_invitation(email, role, expires_in_days=7, created_by=None):
        """Create a new invitation."""
        invitation = Invitation(
            email=email,
            token=Invitation.generate_token(),
            role=role,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
            created_by=created_by
        )
        db.session.add(invitation)
        db.session.commit()
        return invitation


class PasswordReset(db.Model):
    """
    PasswordReset model for storing password reset tokens.
    """
    __tablename__ = 'password_resets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    token = db.Column(db.String(64), nullable=False, index=True, unique=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))
    used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<PasswordReset {self.user_id} {self.used}>'
    
    @staticmethod
    def generate_token():
        """Generate a secure password reset token."""
        return str(uuid.uuid4())
    
    @staticmethod
    def create_reset_token(user_id, expires_in_hours=24):
        """Create a new password reset token."""
        token = PasswordReset(
            user_id=user_id,
            token=PasswordReset.generate_token(),
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours)
        )
        db.session.add(token)
        db.session.commit()
        return token