"""
Role Models for AI Recruiter Pro

This module defines role and permission models for the application.
"""

from datetime import datetime

from .base import db


class Role(db.Model):
    """
    Role model for user role-based access control

    Attributes:
        id (int): Primary key
        role_id (str): Role identifier (admin, recruiter, etc.)
        name (str): Display name for the role
        permissions (str): Comma-separated list of permissions
        inherits (str): Parent role if any
        created_at (datetime): When the role was created
    """

    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(64), unique=True, nullable=False)
    permissions = db.Column(db.JSON, default=list)
    inherits = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with Recruiters (reverse side of the many-to-many)
    recruiters_with_role = db.relationship(
        "Recruiter",
        secondary="user_roles",
        primaryjoin="Role.id == user_roles.c.role_id",
        secondaryjoin="Recruiter.id == user_roles.c.user_id",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Role {self.name}>"


# Association table for many-to-many relationship between users and roles
user_roles = db.Table(
    "user_roles",
    db.Column(
        "user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    db.Column(
        "role_id", db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
)
