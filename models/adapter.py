"""
Model Adapters for AI Recruiter Pro

This module contains adapter classes to ensure compatibility between
different model structures in the system.
"""

import logging
from datetime import datetime

from werkzeug.security import generate_password_hash

from .base import db

# Set up logging
logger = logging.getLogger(__name__)


class RecruiterAdapter:
    """
    Adapter for converting between User and Recruiter models.

    This adapter addresses the inconsistency between the 'users' and 'recruiters'
    tables in the database by providing methods to work with either model.
    """

    @staticmethod
    def create_demo_user(email="demo@example.com", password=None, name="Demo Admin", role="admin"):
        """
        Create a demo user in the recruiters table.

        Args:
            email (str): Email address for the demo user
            password (str, optional): Password for the user (defaults to 'demo123')
            name (str): Name for the demo user
            role (str): Role for the demo user (default 'admin')

        Returns:
            tuple: (bool success, dict user_data)
        """
        if password is None:
            password = "demo123"

        try:
            from models import Recruiter

            # Try to find existing recruiter
            recruiter = Recruiter.query.filter_by(email=email).first()

            if recruiter:
                logger.info(f"Found existing recruiter: {recruiter.name} (ID: {recruiter.id})")

                # Update password
                if hasattr(recruiter, "set_password"):
                    recruiter.set_password(password)
                else:
                    recruiter.password_hash = generate_password_hash(password)

                recruiter.role = role
                if hasattr(recruiter, "role_id"):
                    recruiter.role_id = role

                db.session.commit()
                return True, {"id": recruiter.id, "email": recruiter.email, "role": recruiter.role}
            else:
                # Create new recruiter
                logger.info(f"Creating new recruiter: {name} <{email}>")

                try:
                    # Try with role_id
                    new_recruiter = Recruiter(name=name, email=email, role=role, role_id=role)
                except Exception as e:
                    logger.warning(f"Failed to create recruiter with role_id, trying without: {e}")
                    # Try without role_id
                    new_recruiter = Recruiter(name=name, email=email, role=role)

                # Handle password
                if hasattr(new_recruiter, "set_password"):
                    new_recruiter.set_password(password)
                else:
                    new_recruiter.password_hash = generate_password_hash(password)

                db.session.add(new_recruiter)
                db.session.commit()

                return True, {
                    "id": new_recruiter.id,
                    "email": new_recruiter.email,
                    "role": new_recruiter.role,
                }

        except Exception as e:
            logger.error(f"Error in RecruiterAdapter.create_demo_user: {e}")
            db.session.rollback()
            return False, {"error": str(e)}

    @staticmethod
    def check_demo_user(email="demo@example.com"):
        """
        Check if a demo user exists and return its details.

        Args:
            email (str): Email of the demo user to check

        Returns:
            tuple: (bool exists, dict user_data)
        """
        try:
            from models import Recruiter

            recruiter = Recruiter.query.filter_by(email=email).first()

            if recruiter:
                return True, {
                    "id": recruiter.id,
                    "email": recruiter.email,
                    "role": recruiter.role,
                    "name": recruiter.name if hasattr(recruiter, "name") else "Unknown",
                }
            else:
                return False, {"error": "Demo user not found"}

        except Exception as e:
            logger.error(f"Error in RecruiterAdapter.check_demo_user: {e}")
            return False, {"error": str(e)}

    @staticmethod
    def user_to_recruiter_data(user):
        """
        Convert a User model instance to a dictionary with Recruiter-compatible fields.

        Args:
            user (User): User model instance

        Returns:
            dict: Dictionary with Recruiter-compatible fields
        """
        if not user:
            return None

        # Create a name from first and last name if available
        name = None
        if hasattr(user, "first_name") and hasattr(user, "last_name"):
            name = f"{user.first_name} {user.last_name}".strip()
        elif hasattr(user, "username"):
            name = user.username

        return {
            "id": user.id,
            "email": user.email,
            "name": name,
            "role": "admin" if getattr(user, "is_admin", False) else "recruiter",
            "created_at": getattr(user, "created_at", datetime.utcnow()),
        }
