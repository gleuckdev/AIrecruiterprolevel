"""
Unified Feature Flag Models for AI Recruiter Pro

This module combines and harmonizes all feature flag-related models into a single consistent module.
It replaces both feature_flag.py and feature_flags.py to avoid duplicate model definitions.
"""

from datetime import datetime

from .base import db


# Primary Feature Flag model
class UnifiedFeatureFlag(db.Model):
    """
    Feature Flag Model (Unified)

    This model represents a feature flag that can be used to control
    the availability of features in the application.

    Attributes:
        id (int): Primary key
        flag_key (str): Unique identifier for the feature flag
        enabled (bool): Whether the feature is enabled by default
        description (str): Description of the feature flag
        configuration (dict): JSON configuration for targeting, percentage rollout, etc.
        created_at (datetime): When the flag was created
        updated_at (datetime): When the flag was last updated
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

    # Backwards compatibility fields from the other model
    key = db.Column(db.String(100))  # Maps to flag_key
    flag_type = db.Column(db.String(20), default="boolean")
    value = db.Column(db.Text)  # Stores JSON string version of configuration
    group_ids = db.Column(db.Text)  # For user_group type flags

    # Relationships
    creator = db.relationship("Recruiter", foreign_keys=[created_by], lazy=True)
    updater = db.relationship("Recruiter", foreign_keys=[updated_by], lazy=True)
    overrides = db.relationship(
        "UnifiedFeatureFlagOverride",
        backref=db.backref("feature_flag", lazy=True),
        lazy=True,
        cascade="all, delete-orphan",
    )
    stats = db.relationship(
        "UnifiedFeatureFlagStat",
        foreign_keys="UnifiedFeatureFlagStat.flag_id",
        primaryjoin="UnifiedFeatureFlag.id==UnifiedFeatureFlagStat.flag_id",
        backref="flag",
        lazy=True,
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


class UnifiedFeatureFlagOverride(db.Model):
    """
    Feature Flag Override Model (Unified)

    This model represents a user-specific override for a feature flag.
    """

    __tablename__ = "feature_flag_overrides"
    __table_args__ = (
        db.UniqueConstraint("flag_id", "user_id", name="uix_feature_flag_override"),
        {"extend_existing": True},
    )

    id = db.Column(db.Integer, primary_key=True)
    flag_id = db.Column(
        db.Integer, db.ForeignKey("feature_flags.id", ondelete="CASCADE"), nullable=False
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False
    )
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to User (Recruiter)
    user = db.relationship("Recruiter", backref=db.backref("feature_flag_overrides", lazy=True))

    def __repr__(self):
        return f"<FeatureFlagOverride {self.flag_id} for user {self.user_id}>"


class UnifiedFeatureFlagStat(db.Model):
    """
    Feature Flag Statistics Model (Unified)

    This model records usage statistics for feature flags, tracking
    when flags are checked and their values.
    """

    __tablename__ = "feature_flag_stats"
    __table_args__ = (
        db.Index("idx_feature_flag_stat_flag_id", "flag_id"),
        db.Index("idx_feature_flag_stat_user_id", "user_id"),
        db.Index("idx_feature_flag_stat_created_at", "created_at"),
        {"extend_existing": True},
    )

    id = db.Column(db.Integer, primary_key=True)
    flag_id = db.Column(
        db.Integer, db.ForeignKey("feature_flags.id", ondelete="CASCADE"), nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    value = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to User model
    user = db.relationship("User", backref=db.backref("feature_flag_stats", lazy=True))

    def __repr__(self):
        return (
            f"<FeatureFlagStat {self.flag_id} for user {self.user_id or 'anonymous'}: {self.value}>"
        )

    def to_dict(self):
        """
        Convert stats to dictionary for API responses

        Returns:
            dict: Dictionary representation of feature flag stats
        """
        success_rate = 0
        if (
            hasattr(self, "evaluations")
            and hasattr(self, "successful_evaluations")
            and self.evaluations > 0
        ):
            success_rate = (self.successful_evaluations / self.evaluations) * 100

        return {
            "id": self.id,
            "flag_id": self.flag_id,
            "user_id": self.user_id,
            "value": self.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "success_rate": round(success_rate, 2) if success_rate else None,
        }


# Create compatibility aliases for backwards compatibility
FeatureFlag = UnifiedFeatureFlag
FeatureFlagOverride = UnifiedFeatureFlagOverride
FeatureFlagStat = UnifiedFeatureFlagStat
