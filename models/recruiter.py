"""
Recruiter Model for AI Recruiter Pro

This module defines the Recruiter model used by the application.
"""

from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .base import db


class Recruiter(UserMixin, db.Model):
    """
    Recruiter model for AI Recruiter Pro platform.

    This model is mapped to the 'recruiters' table in the database.
    It represents recruiters that can log in and manage jobs and candidates.

    Attributes:
        id (int): Primary key
        name (str): Recruiter's full name
        email (str): Unique email address for login
        password_hash (str): Hashed password for authentication
        role (str): Role string ('recruiter', 'admin', etc.)
        role_id (str): Foreign key to roles table
        created_at (datetime): Account creation timestamp
    """

    __tablename__ = "recruiters"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # Role fields
    role = db.Column(
        db.String(20), default="recruiter"
    )  # Legacy field, kept for backward compatibility
    role_id = db.Column(
        db.String(50),
        db.ForeignKey("roles.role_id", name="fk_recruiter_role_id"),
        nullable=True,
        default="recruiter",
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # Define relationships
    # Job relationship using the new recruiter_id field
    jobs = db.relationship("Job", foreign_keys="Job.recruiter_id", backref="recruiter", lazy=True)
    # CandidateRating relationship without backref
    ratings = db.relationship(
        "CandidateRating",
        foreign_keys="CandidateRating.recruiter_id",
        primaryjoin="Recruiter.id == CandidateRating.recruiter_id",
        lazy=True,
    )
    candidates = db.relationship(
        "Candidate",
        foreign_keys="Candidate.uploaded_by",
        backref="uploaded_by_recruiter",
        lazy=True,
    )
    # Relationship to Role model
    assigned_role = db.relationship("Role", foreign_keys=[role_id], backref="recruiters", lazy=True)

    # Many-to-many relationship with roles (for future multi-role support)
    roles = db.relationship(
        "Role",
        secondary="user_roles",
        primaryjoin="Recruiter.id == user_roles.c.user_id",
        secondaryjoin="Role.id == user_roles.c.role_id",
        overlaps="recruiters_with_role,roles,users",
        lazy="dynamic",
    )

    def set_password(self, password):
        """
        Set the password hash from a plain text password

        Args:
            password (str): Plain text password
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Check if a plain text password matches the stored hash

        Args:
            password (str): Plain text password to check

        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        """String representation of the recruiter"""
        return f"<Recruiter {self.name} ({self.email})>"

    def is_admin(self):
        """
        Check if this recruiter has admin privileges

        Returns:
            bool: True if admin, False otherwise
        """
        # First check the string role (backward compatibility)
        if self.role == "admin":
            return True

        # Then check if role_id points to admin role via assigned_role
        if self.assigned_role and self.assigned_role.name == "admin":
            return True

        # Finally check if any role in the many-to-many relationship is admin
        return any(role.name == "admin" for role in self.roles.all())

    def has_permission(self, permission):
        """
        Check if this recruiter has a specific permission

        Args:
            permission (str): The permission string to check

        Returns:
            bool: True if the recruiter has the permission, False otherwise
        """
        # Admins have all permissions
        if self.is_admin():
            return True

        # Check assigned role permissions
        if self.assigned_role and self.assigned_role.permissions:
            permissions_list = self.assigned_role.permissions.split(",")
            if permission in permissions_list:
                return True

        # Check permissions from many-to-many roles
        for role in self.roles.all():
            if role.permissions and permission in role.permissions.split(","):
                return True

        return False

    def get_permissions(self):
        """
        Get all permissions this recruiter has

        Returns:
            set: Set of all permission strings
        """
        all_permissions = set()

        # Get permissions from assigned role
        if self.assigned_role and self.assigned_role.permissions:
            all_permissions.update(self.assigned_role.permissions.split(","))

        # Get permissions from many-to-many roles
        for role in self.roles.all():
            if role.permissions:
                all_permissions.update(role.permissions.split(","))

        return all_permissions
