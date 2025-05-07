"""
Invitation Model

This module contains the database model for recruiter invitations.
"""

import logging
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from extensions import db

# Set up logger
logger = logging.getLogger(__name__)


class Invitation(db.Model):
    """
    Invitation Model

    Used to store invitations for new recruiters. Each invitation has:
    - A unique token for accessing the join URL
    - Role information for the invitee
    - Reference to the recruiter who created the invitation
    - Optional job and candidate sharing flags
    """

    __tablename__ = "invitations"

    # Primary key
    id = Column(Integer, primary_key=True)

    # Invitation details
    email = Column(String(120), nullable=False, index=True)
    token = Column(String(64), nullable=False, unique=True, index=True)
    role = Column(String(50), nullable=False, default="recruiter")
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)

    # Sharing options
    share_jobs = Column(Boolean, default=False)
    share_candidates = Column(Boolean, default=False)

    # Creator reference
    created_by = Column(Integer, ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True)
    creator = relationship("Recruiter", foreign_keys=[created_by], backref="created_invitations")

    # Role relationship (if using explicit roles table)
    role_relation = relationship("Role", foreign_keys=[role_id], backref="invitations")

    def __repr__(self):
        """String representation of invitation"""
        return f"<Invitation {self.id} for {self.email} (role: {self.role})>"

    def is_expired(self):
        """Check if invitation has expired"""
        return datetime.utcnow() > self.expires_at

    def to_dict(self):
        """Convert invitation to dictionary for API responses"""
        return {
            "id": self.id,
            "email": self.email,
            "token": self.token,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "used": self.used,
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "share_jobs": self.share_jobs,
            "share_candidates": self.share_candidates,
            "created_by": self.created_by,
        }
