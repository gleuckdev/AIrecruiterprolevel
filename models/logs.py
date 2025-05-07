"""
Logging Models

This module defines database models for storing various types of logs,
including error logs, candidate processing history, API request logs,
and other important events for auditing and monitoring.
"""

import json
from datetime import datetime

from sqlalchemy import inspect

from extensions import db


class ErrorLog(db.Model):
    """
    Model for storing application errors.

    This model keeps a record of errors that occur in the application for later
    analysis, troubleshooting, and pattern detection.
    """

    __tablename__ = "error_logs"

    id = db.Column(db.Integer, primary_key=True)
    error_type = db.Column(db.String(255), nullable=False, index=True)
    message = db.Column(db.String(1000), nullable=False)
    details = db.Column(db.Text, nullable=True)  # JSON string with full error details
    url = db.Column(db.String(2000), nullable=True, index=True)
    method = db.Column(db.String(10), nullable=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    occurred_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved = db.Column(db.Boolean, default=False, nullable=False, index=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    resolution_date = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship("User", backref=db.backref("error_logs", lazy=True))

    def __repr__(self):
        return f"<ErrorLog {self.id} - {self.error_type}: {self.message[:50]}>"

    def to_dict(self):
        """Convert the model to a dictionary."""
        result = {}
        for column in inspect(self.__class__).columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value

        # Parse JSON details if present
        if self.details:
            try:
                result["details"] = json.loads(self.details)
            except json.JSONDecodeError:
                result["details"] = self.details

        return result


class ApiLog(db.Model):
    """
    Model for logging API requests.

    This model records information about API requests, particularly to external
    services, for monitoring, debugging, and usage tracking.
    """

    __tablename__ = "api_logs"

    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(1000), nullable=False, index=True)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer, nullable=True, index=True)
    request_data = db.Column(db.Text, nullable=True)  # JSON string of request params/data
    response_data = db.Column(db.Text, nullable=True)  # Redacted/sanitized response
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    duration_ms = db.Column(db.Integer, nullable=True)  # Request duration in milliseconds
    service = db.Column(
        db.String(255), nullable=False, index=True
    )  # e.g., "openai", "google", "twilio"
    occurred_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    correlation_id = db.Column(
        db.String(255), nullable=True, index=True
    )  # Request correlation ID for tracing
    api_key_index = db.Column(
        db.Integer, nullable=True
    )  # Index of API key used (for multi-key services)
    provider_name = db.Column(
        db.String(50), nullable=True, index=True
    )  # LLM provider name (openai, anthropic, etc.)
    model_name = db.Column(
        db.String(50), nullable=True, index=True
    )  # Specific model used (gpt-4o, claude-3-5-sonnet, etc.)

    # Token usage and cost tracking
    tokens_used = db.Column(db.Integer, nullable=True)  # Total tokens used
    tokens_prompt = db.Column(db.Integer, nullable=True)  # Tokens in the prompt
    tokens_completion = db.Column(db.Integer, nullable=True)  # Tokens in the completion
    cost = db.Column(db.Float, nullable=True)  # Estimated cost in USD

    # Relationships
    user = db.relationship("User", backref=db.backref("api_logs", lazy=True))

    def __repr__(self):
        return f"<ApiLog {self.id} - {self.service}: {self.endpoint} ({self.status_code})>"

    def to_dict(self):
        """Convert the model to a dictionary."""
        result = {}
        for column in inspect(self.__class__).columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value

        # Parse JSON data if present
        for field in ["request_data", "response_data"]:
            if getattr(self, field):
                try:
                    result[field] = json.loads(getattr(self, field))
                except json.JSONDecodeError:
                    result[field] = getattr(self, field)

        return result


# Import the CandidateProcessingHistory model from models.candidate
# This is needed for backwards compatibility with existing imports


class AuditLog(db.Model):
    """
    Model for tracking user actions for auditing purposes.

    This model records significant user actions for compliance, security monitoring,
    and audit trail purposes.
    """

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action = db.Column(
        db.String(255), nullable=False, index=True
    )  # e.g., "login", "update_job", "delete_candidate"
    resource_type = db.Column(
        db.String(255), nullable=True, index=True
    )  # e.g., "job", "candidate", "user"
    resource_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)  # JSON string with additional details
    ip_address = db.Column(db.String(45), nullable=True)  # Supports IPv6
    user_agent = db.Column(db.String(1000), nullable=True)
    occurred_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = db.relationship("User", backref=db.backref("audit_logs", lazy=True))

    def __repr__(self):
        return f"<AuditLog {self.id} - {self.user_id}: {self.action} on {self.resource_type}/{self.resource_id}>"

    def to_dict(self):
        """Convert the model to a dictionary."""
        result = {}
        for column in inspect(self.__class__).columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value

        # Parse JSON details if present
        if self.details:
            try:
                result["details"] = json.loads(self.details)
            except json.JSONDecodeError:
                result["details"] = self.details

        return result
