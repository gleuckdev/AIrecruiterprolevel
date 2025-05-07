"""
Base Database Models for AI Recruiter Pro

This module defines the base model classes and database instance used throughout
the application.
"""

from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from extensions import db

# Re-export db and PostgreSQL types for easier imports and LSP compliance
__all__ = ["ARRAY", "JSONB", "db"]
