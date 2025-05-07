"""
User Models for AI Recruiter Pro

This module defines the user-related models for the application.
"""

import uuid
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .base import db


class RecruiterSharing(db.Model):
    """
    Model for sharing resources between recruiters

    Attributes:
        id (int): Primary key
        owner_id (int): ID of the recruiter who owns the resource
        shared_with_id (int): ID of the recruiter with whom the resource is shared
        resource_type (str): Type of resource being shared ('job' or 'candidate')
        resource_id (int): ID of the shared resource
        permissions (str): Comma-separated list of permissions (view, edit, etc.)
        created_at (datetime): When the sharing relationship was created
        updated_at (datetime): When the sharing relationship was last updated
    """

    __tablename__ = "recruiter_sharing"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    shared_with_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    resource_type = db.Column(db.String(20), nullable=False)  # 'job' or 'candidate'
    resource_id = db.Column(db.Integer, nullable=False)
    permissions = db.Column(
        db.String(255), default="view"
    )  # Comma-separated list: view, edit, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Define foreign key relationships
    owner = db.relationship("User", foreign_keys=[owner_id], backref="shared_resources")
    shared_with = db.relationship(
        "User", foreign_keys=[shared_with_id], backref="accessible_resources"
    )

    def __repr__(self):
        return f"<RecruiterSharing {self.resource_type}:{self.resource_id} from {self.owner_id} to {self.shared_with_id}>"


class User(UserMixin, db.Model):
    """
    Core user model for AI Recruiter Pro

    UserMixin provides is_authenticated, is_active, is_anonymous, and get_id methods

    Attributes:
        id (int): Primary key
        username (str): Unique username
        email (str): Unique email address
        password_hash (str): Hashed password
        first_name (str): User's first name
        last_name (str): User's last name
        created_at (datetime): Account creation timestamp
        last_login (datetime): Last login timestamp
        is_admin (bool): Whether the user is an admin
        is_active (bool): Whether the user account is active
        is_demo (bool): Whether this is a demo user account
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_demo = db.Column(db.Boolean, default=False)
    api_key = db.Column(db.String(255), unique=True)

    # Relationships
    roles = db.relationship(
        "Role", secondary="user_roles", backref=db.backref("users", lazy="dynamic")
    )

    def __init__(self, username=None, email=None, password=None, **kwargs):
        """
        Initialize a new user

        Args:
            username (str, optional): Unique username
            email (str, optional): User's email address
            password (str, optional): Plain text password
            **kwargs: Additional attributes
        """
        super().__init__(**kwargs)

        # Only set these if provided (for compatibility with existing code that uses **kwargs)
        if username is not None:
            self.username = username
        if email is not None:
            self.email = email

        if password:
            self.set_password(password)

        # Generate API key if not provided
        if not kwargs.get("api_key") and not getattr(self, "api_key", None):
            self.generate_api_key()

    def set_password(self, password):
        """
        Set password hash from plain text password

        Args:
            password (str): Plain text password
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verify password against stored hash

        Args:
            password (str): Plain text password to check

        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)

    def generate_api_key(self):
        """Generate a unique API key for this user"""
        self.api_key = str(uuid.uuid4())

    def update_last_login(self):
        """Update last login timestamp to now"""
        self.last_login = datetime.utcnow()

    def get_full_name(self):
        """
        Get user's full name

        Returns:
            str: Full name or username if name not set
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def is_admin_user(self):
        """
        Check if user is an admin

        Returns:
            bool: True if user is an admin, False otherwise
        """
        # Check the is_admin field
        if hasattr(self, "is_admin") and self.is_admin:
            return True

        # Also check roles for an admin role
        if hasattr(self, "roles"):
            for role in self.roles:
                if role.name == "admin":
                    return True
        return False

    def __repr__(self):
        return f"<User {self.username}>"
