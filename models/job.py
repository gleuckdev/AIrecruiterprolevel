"""
Job Models for AI Recruiter Pro

This module defines job-related models for storing job postings,
company information, and departments.
"""

from datetime import datetime, timedelta

from sqlalchemy.dialects.postgresql import JSONB

from .base import db


class Department(db.Model):
    """
    Department model for organizing jobs

    Attributes:
        id (int): Primary key
        name (str): Department name
        description (str): Department description
    """

    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)

    # Relationships
    jobs = db.relationship("Job", backref="department", lazy="dynamic")

    def __repr__(self):
        return f"<Department {self.name}>"


class Company(db.Model):
    """
    Company model for job postings

    Attributes:
        id (int): Primary key
        name (str): Company name
        description (str): Company description
        logo_url (str): URL to company logo
        website (str): Company website
        location (str): Company location
    """

    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    logo_url = db.Column(db.String(255))
    website = db.Column(db.String(255))
    location = db.Column(db.String(120))

    # Relationships
    jobs = db.relationship("Job", backref="company_obj", lazy="dynamic")

    def __repr__(self):
        return f"<Company {self.name}>"


class Job(db.Model):
    """
    Job model for storing job postings

    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to user who created the job
        title (str): Job title
        description (str): Job description
        requirements (str): Job requirements
        desired_skills (str): Desired skills for the job
        skills_array (list): Array of skills for easier searching
        location (str): Job location
        salary_min (int): Minimum salary
        salary_max (int): Maximum salary
        job_type (str): Job type (full-time, part-time, contract, etc.)
        experience_level (str): Required experience level (junior, mid, senior, etc.)
        education (str): Required education
        created_at (datetime): Record creation timestamp
        updated_at (datetime): Last update timestamp
        expires_at (datetime): When the job expires
        is_active (bool): Whether the job is active
        is_remote (bool): Whether the job is remote
        company_id (int): Foreign key to company
        department_id (int): Foreign key to department
        embedding (list): Vector embedding for semantic search
    """

    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True
    )  # Legacy field
    recruiter_id = db.Column(
        db.Integer, db.ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True
    )  # Current field

    # Add compatibility property to handle legacy code
    @property
    def user(self):
        """Legacy property to maintain compatibility with older code."""
        from models import Recruiter

        return Recruiter.query.get(self.recruiter_id) if self.recruiter_id else None

    # Make sure both user_id and recruiter_id stay in sync
    @staticmethod
    def before_save(mapper, connection, target):
        """Sync user_id and recruiter_id before saving to database"""
        if target.user_id is not None and target.recruiter_id is None:
            target.recruiter_id = target.user_id
        elif target.recruiter_id is not None and target.user_id is None:
            target.user_id = target.recruiter_id

    # Job details
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(120))
    experience = db.Column(db.String(120))
    education = db.Column(db.String(120))
    job_type = db.Column(db.String(20), default="full-time")
    salary_range = db.Column(db.String(120))  # stored as a range string
    company = db.Column(db.String(120))
    required_skills = db.Column(db.Text)  # instead of requirements
    preferred_skills = db.Column(db.Text)  # instead of desired_skills
    embedding = db.Column(JSONB)

    # Computed property for backwards compatibility with skills_array
    @property
    def skills_array(self):
        """Legacy property to maintain compatibility with older code."""
        if self.required_skills:
            return [skill.strip() for skill in self.required_skills.split(",")]
        return []

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=60))
    status = db.Column(db.String(20), default="active")  # active, closed, draft, expired
    notification_sent = db.Column(
        db.Boolean, default=False
    )  # Flag to track if expiration notification was sent
    last_renewed_at = db.Column(db.DateTime)
    token_id = db.Column(db.Integer)

    # Properties for backwards compatibility
    @property
    def is_active(self):
        return self.status == "active"

    @property
    def updated_at(self):
        return self.last_renewed_at or self.created_at

    @property
    def is_remote(self):
        return "remote" in self.location.lower() if self.location else False

    @property
    def salary_min(self):
        if not self.salary_range:
            return None
        parts = self.salary_range.split("-")
        if len(parts) >= 1:
            try:
                return int(parts[0].strip().replace("$", "").replace(",", ""))
            except:
                return None
        return None

    @property
    def salary_max(self):
        if not self.salary_range:
            return None
        parts = self.salary_range.split("-")
        if len(parts) >= 2:
            try:
                return int(parts[1].strip().replace("$", "").replace(",", ""))
            except:
                return None
        return None

    @property
    def experience_level(self):
        return self.experience

    @property
    def expiration_notification_date(self):
        """Legacy property to maintain compatibility with older code."""
        # Use the notification_sent field to determine if a notification was sent
        if self.notification_sent:
            # If notification was sent, return a date 7 days before expiry
            if self.expires_at:
                return self.expires_at - timedelta(days=7)
        return None

    # Relationship fields
    # These fields will be added to the database via migration
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )

    # The database already has 'company' field defined earlier as a string

    # Vector embedding for semantic search is already defined above at line 121
    # Removing duplicate definition

    def is_expired(self):
        """
        Check if the job is expired

        Returns:
            bool: True if expired, False otherwise
        """
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def days_until_expiry(self):
        """
        Calculate days until expiry

        Returns:
            int: Days until expiry, or 0 if already expired
        """
        if not self.expires_at:
            return 0

        if self.is_expired():
            return 0

        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)

    def renew(self, days=60):
        """
        Renew the job for a specified number of days

        Args:
            days (int): Number of days to extend the expiry by
        """
        if not self.expires_at or self.is_expired():
            self.expires_at = datetime.utcnow() + timedelta(days=days)
        else:
            self.expires_at = self.expires_at + timedelta(days=days)

    def to_dict(self):
        """
        Convert job to dictionary for API responses

        Returns:
            dict: Dictionary representation of job
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "skills_array": self.skills_array,
            "location": self.location,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_range": self.salary_range,
            "job_type": self.job_type,
            "experience_level": self.experience_level,
            "experience": self.experience,
            "education": self.education,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": (
                self.updated_at.isoformat()
                if hasattr(self, "updated_at") and self.updated_at
                else None
            ),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "is_remote": self.is_remote,
            "status": self.status,
            "notification_sent": self.notification_sent,
            "expiration_notification_date": (
                self.expiration_notification_date.isoformat()
                if hasattr(self, "expiration_notification_date")
                and self.expiration_notification_date
                else None
            ),
            "company": self.company,
            "days_until_expiry": self.days_until_expiry(),
            "is_expired": self.is_expired(),
            "recruiter_id": self.recruiter_id,
            "last_renewed_at": self.last_renewed_at.isoformat() if self.last_renewed_at else None,
            "token_id": self.token_id,
        }

    def __repr__(self):
        return f"<Job {self.title} ({self.id})>"


# Register the pre-save event listener to sync user_id and recruiter_id fields
from sqlalchemy import event

event.listen(Job, "before_insert", Job.before_save)
event.listen(Job, "before_update", Job.before_save)
