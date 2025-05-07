"""
User models for AI Recruiter Pro.

This module contains models related to users, roles, and permissions.
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from app.app_factory import db


# Role-permission association table
role_permissions = db.Table(
    'role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)


class Permission(db.Model):
    """
    Permission model for defining granular access controls.
    """
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<Permission {self.name}>'


class Role(db.Model):
    """
    Role model for role-based access control.
    """
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))
    
    # Relationships
    permissions = db.relationship('Permission', secondary=role_permissions,
                                  backref=db.backref('roles', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def has_permission(self, permission_name):
        """Check if this role has a specific permission."""
        return any(p.name == permission_name for p in self.permissions)


class Recruiter(UserMixin, db.Model):
    """
    Recruiter model - primary user entity for recruiters and admins.
    """
    __tablename__ = 'recruiters'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    company = db.Column(db.String(120))
    title = db.Column(db.String(120))
    
    # Status and tracking
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Role-based access control
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    role = db.relationship('Role', backref='users')
    
    # Relationships
    sessions = db.relationship('Session', backref='user', lazy='dynamic',
                               cascade='all, delete-orphan')
    
    @property
    def password(self):
        """Password getter - raises an error to prevent access."""
        raise AttributeError('Password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        """Hash and store the password."""
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        """Verify a password against the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def has_permission(self, permission_name):
        """Check if the user has a specific permission."""
        return self.role and self.role.has_permission(permission_name)
    
    def is_admin(self):
        """Check if the user is an admin."""
        return self.role and self.role.name == 'admin'
    
    def __repr__(self):
        return f'<Recruiter {self.username}>'


class Session(db.Model):
    """
    Session model for tracking user sessions.
    """
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('recruiters.id'), nullable=False)
    token_hash = db.Column(db.String(256), nullable=False, index=True, unique=True)
    
    # Device information
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    device_info = db.Column(db.JSON)
    
    # Status and tracking
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Session {self.id} for User {self.user_id}>'