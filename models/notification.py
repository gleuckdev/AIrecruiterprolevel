"""
Notification Models for AI Recruiter Pro

This module defines notification-related models for storing
notification data and notification types.
"""

from datetime import datetime

from app import db


class NotificationType(db.Model):
    """
    Notification Type Model

    This model defines different types of notifications that can be sent
    to users, such as system notifications, job matches, etc.

    Attributes:
        id (int): Primary key
        name (str): Name of the notification type
        description (str): Description of the notification type
        icon (str): Icon to display for this notification type
        color (str): Color to use for this notification type
        created_at (datetime): When the notification type was created
    """

    __tablename__ = "notification_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(255))
    icon = db.Column(db.String(50))
    color = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    notifications = db.relationship("Notification", backref="type", lazy=True)

    def __repr__(self):
        return f"<NotificationType {self.name}>"


class Notification(db.Model):
    """
    Notification Model

    This model represents a notification sent to a user.

    Attributes:
        id (int): Primary key
        user_id (int): User who received the notification
        type_id (int): Foreign key to notification type
        title (str): Title of the notification
        message (str): Message content
        data (str): Additional JSON data for the notification
        is_read (bool): Whether the notification has been read
        created_at (datetime): When the notification was created
        expires_at (datetime): When the notification expires
    """

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey("notification_types.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    data = db.Column(db.Text)  # JSON data
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    # Define indexes for better query performance
    __table_args__ = (
        db.Index("idx_notification_user_id", "user_id"),
        db.Index("idx_notification_is_read", "is_read"),
        db.Index("idx_notification_created_at", "created_at"),
        db.Index("idx_notification_expires_at", "expires_at"),
    )

    # Relationship to User model
    user = db.relationship("User", backref=db.backref("notifications", lazy=True))

    def __repr__(self):
        return f"<Notification {self.id}: {self.title[:20]}...>"
