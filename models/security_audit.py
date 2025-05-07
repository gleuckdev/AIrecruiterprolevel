"""
Security Audit Models for AI Recruiter Pro

This module defines models for tracking security-relevant events and managing IP blacklists.
"""

import ipaddress
from datetime import datetime

from .base import db


class SecurityAuditLog(db.Model):
    """
    Security Audit Log Model

    Used to track security-relevant events for compliance and security monitoring.
    """

    __tablename__ = "security_audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("recruiters.id"), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 can be up to 45 chars
    user_agent = db.Column(db.String(255), nullable=True)
    resource_type = db.Column(db.String(50), nullable=True, index=True)
    resource_id = db.Column(db.String(50), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False, default="success", index=True)
    details = db.Column(db.JSON, nullable=True)

    # Relationships
    user = db.relationship("Recruiter", foreign_keys=[user_id], lazy=True)

    def __repr__(self):
        return f"<SecurityAuditLog {self.event_type} by user {self.user_id} at {self.timestamp}>"

    def to_dict(self):
        """
        Convert audit log entry to dictionary for API responses

        Returns:
            dict: Dictionary representation of audit log
        """
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "status": self.status,
            "details": self.details,
        }


class IPBlacklist(db.Model):
    """
    IP Blacklist Model

    Used to block access from specific IP addresses or ranges.
    """

    __tablename__ = "ip_blacklist"

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, unique=True)  # Single IP or CIDR notation
    reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("recruiters.id"), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)  # NULL means never expires

    # Relationships
    creator = db.relationship("Recruiter", foreign_keys=[created_by], lazy=True)

    def __repr__(self):
        return f"<IPBlacklist {self.ip_address}>"

    def is_expired(self) -> bool:
        """
        Check if the blacklist entry is expired

        Returns:
            True if expired, False otherwise
        """
        if self.expires_at is None:
            return False

        return datetime.utcnow() > self.expires_at

    def matches_ip(self, ip_to_check: str) -> bool:
        """
        Check if an IP address matches this blacklist entry

        Args:
            ip_to_check: IP address to check

        Returns:
            True if the IP matches, False otherwise
        """
        # Handle CIDR notation
        if "/" in self.ip_address:
            try:
                network = ipaddress.ip_network(self.ip_address, strict=False)
                ip = ipaddress.ip_address(ip_to_check)
                return ip in network
            except ValueError:
                return False

        # Simple exact match
        return self.ip_address == ip_to_check

    def to_dict(self):
        """
        Convert blacklist entry to dictionary for API responses

        Returns:
            dict: Dictionary representation of blacklist entry
        """
        return {
            "id": self.id,
            "ip_address": self.ip_address,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_expired": self.is_expired(),
        }
