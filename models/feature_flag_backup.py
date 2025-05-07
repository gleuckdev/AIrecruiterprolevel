"""
Feature Flag Models for AI Recruiter Pro

This module defines models for managing feature flags throughout the application.
Feature flags allow for controlled rollout of new features and A/B testing.
"""

from datetime import datetime

# Use db directly which already provides SQLAlchemy functionality
from .base import db


class FeatureFlag(db.Model):
    """
    Feature Flag Model

    Used to control the availability of features in the application.
    Supports boolean flags, percentage rollouts, user targeting, and time-bounded activations.
    """

    __tablename__ = "feature_flags"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    flag_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    enabled = db.Column(db.Boolean, default=False, nullable=False)
    description = db.Column(db.Text)
    configuration = db.Column(db.JSON, default={}, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    created_by = db.Column(db.Integer, db.ForeignKey("recruiters.id"))
    updated_by = db.Column(db.Integer, db.ForeignKey("recruiters.id"))

    # Relationships
    creator = db.relationship("Recruiter", foreign_keys=[created_by], lazy=True)
    updater = db.relationship("Recruiter", foreign_keys=[updated_by], lazy=True)
    stats = db.relationship(
        "FeatureFlagStats",
        foreign_keys="FeatureFlagStats.flag_key",
        primaryjoin="FeatureFlag.flag_key==FeatureFlagStats.flag_key",
        back_populates="feature_flag",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<FeatureFlag {self.flag_key} enabled={self.enabled}>"

    @property
    def is_simple_boolean(self):
        """
        Check if this is a simple boolean flag without complex configuration

        Returns:
            bool: True if this is a simple on/off flag
        """
        return not self.configuration or self.configuration == {}

    def is_enabled_for_user(self, user_id=None, role=None):
        """
        Check if flag is enabled for a specific user/role

        Args:
            user_id: The user ID to check
            role: The user's role to check

        Returns:
            bool: True if the flag is enabled for this user
        """
        if not self.enabled:
            return False

        # If no configuration, simple boolean check
        if self.is_simple_boolean:
            return self.enabled

        # Check user targeting
        if user_id is not None and "users" in self.configuration:
            if user_id in self.configuration.get("users", []):
                return True

        # Check role targeting
        if role is not None and "roles" in self.configuration:
            if role in self.configuration.get("roles", []):
                return True

        # Check percentage rollout
        if "percentage" in self.configuration:
            percentage = float(self.configuration.get("percentage", 0))

            # Deterministic user-based hashing for consistent percentage rollout
            # Only apply if we have a user_id
            if user_id is not None:
                import hashlib

                user_hash = int(hashlib.md5(f"{self.flag_key}:{user_id}".encode()).hexdigest(), 16)
                user_mod = (user_hash % 100) + 1  # 1-100
                return user_mod <= percentage

            # For system checks without a user, just use the raw percentage
            import random

            return random.random() * 100 <= percentage

        # Check time-bounded activation
        if "start_date" in self.configuration or "end_date" in self.configuration:
            now = datetime.utcnow()

            start_date = self.configuration.get("start_date")
            if start_date and datetime.fromisoformat(start_date.replace("Z", "+00:00")) > now:
                return False

            end_date = self.configuration.get("end_date")
            if end_date and datetime.fromisoformat(end_date.replace("Z", "+00:00")) < now:
                return False

        # Default to the enabled status if none of the targeting criteria matched
        return self.enabled

    def to_dict(self):
        """
        Convert flag to dictionary for API responses

        Returns:
            dict: Dictionary representation of feature flag
        """
        return {
            "id": self.id,
            "flag_key": self.flag_key,
            "enabled": self.enabled,
            "description": self.description,
            "configuration": self.configuration,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "is_simple_boolean": self.is_simple_boolean,
        }


class FeatureFlagStats(db.Model):
    """
    Feature Flag Statistics Model

    Used to track usage statistics for feature flags, including how often
    they are evaluated and how often they return true.
    """

    __tablename__ = "feature_flag_stats"
    __table_args__ = (
        db.UniqueConstraint("flag_key", "date", name="uix_flag_date"),
        {"extend_existing": True},
    )

    id = db.Column(db.Integer, primary_key=True)
    flag_key = db.Column(db.String(100), db.ForeignKey("feature_flags.flag_key"), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    evaluations = db.Column(db.Integer, default=0, nullable=False)
    successful_evaluations = db.Column(db.Integer, default=0, nullable=False)

    # Relationship to feature flag
    feature_flag = db.relationship(
        "FeatureFlag",
        foreign_keys=[flag_key],
        primaryjoin="FeatureFlag.flag_key==FeatureFlagStats.flag_key",
        back_populates="stats",
    )

    def __repr__(self):
        return (
            f"<FeatureFlagStats {self.flag_key} date={self.date.date()} evals={self.evaluations}>"
        )

    def to_dict(self):
        """
        Convert stats to dictionary for API responses

        Returns:
            dict: Dictionary representation of feature flag stats
        """
        success_rate = 0
        if self.evaluations > 0:
            success_rate = (self.successful_evaluations / self.evaluations) * 100

        return {
            "id": self.id,
            "flag_key": self.flag_key,
            "date": self.date.date().isoformat(),
            "evaluations": self.evaluations,
            "successful_evaluations": self.successful_evaluations,
            "success_rate": round(success_rate, 2),
        }
