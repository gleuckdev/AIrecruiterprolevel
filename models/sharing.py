"""
Sharing models for job and candidate collaboration.

This module contains models for tracking sharing relationships between
recruiters for jobs and candidates.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from extensions import db


class JobSharing(db.Model):
    """
    Job Sharing model.

    Represents a sharing relationship between recruiters for a job.
    """

    __tablename__ = "job_sharing"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    permissions = Column(
        String(255), nullable=False, default="view"
    )  # Comma-separated list of permissions
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job = relationship("Job", foreign_keys=[job_id], backref="shared_with")
    owner = relationship("User", foreign_keys=[owner_id], backref="job_shares_given")
    recipient = relationship("User", foreign_keys=[recipient_id], backref="job_shares_received")

    def __repr__(self):
        return f"<JobSharing job_id={self.job_id} recipient_id={self.recipient_id}>"

    @property
    def permission_list(self):
        """Get permissions as a list."""
        if not self.permissions:
            return []
        return self.permissions.split(",")

    def has_permission(self, permission):
        """Check if the sharing relationship has a specific permission."""
        return permission in self.permission_list


class CandidateSharing(db.Model):
    """
    Candidate Sharing model.

    Represents a sharing relationship between recruiters for a candidate.
    """

    __tablename__ = "candidate_sharing"

    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    permissions = Column(
        String(255), nullable=False, default="view"
    )  # Comma-separated list of permissions
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    candidate = relationship("Candidate", foreign_keys=[candidate_id], backref="shared_with")
    owner = relationship("User", foreign_keys=[owner_id], backref="candidate_shares_given")
    recipient = relationship(
        "User", foreign_keys=[recipient_id], backref="candidate_shares_received"
    )

    def __repr__(self):
        return (
            f"<CandidateSharing candidate_id={self.candidate_id} recipient_id={self.recipient_id}>"
        )

    @property
    def permission_list(self):
        """Get permissions as a list."""
        if not self.permissions:
            return []
        return self.permissions.split(",")

    def has_permission(self, permission):
        """Check if the sharing relationship has a specific permission."""
        return permission in self.permission_list
