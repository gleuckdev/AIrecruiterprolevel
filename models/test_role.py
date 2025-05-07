"""
Test Role model for integration tests.

This module provides a TestRole model that matches the actual database schema,
ensuring compatibility in test environments.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from .base import db


class TestRole(db.Model):
    """
    TestRole model for testing that matches the actual database schema.
    """

    __tablename__ = "roles"
    __table_args__ = {"extend_existing": True}

    # Define columns based on what exists in the database
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    role_id = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    inherits = Column(String(50), nullable=True)
    permissions = Column(Text)

    def __repr__(self):
        return f"<TestRole {self.id}>"
