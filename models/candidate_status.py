#!/usr/bin/env python
"""
Candidate status transition module.

This module defines the candidate processing status states and transitions.
"""

from datetime import datetime

# Use db directly which already provides SQLAlchemy functionality to avoid LSP errors
from .base import db


class CandidateProcessingHistory(db.Model):
    """
    Model for tracking candidate processing status history.

    This model records transitions between processing states, including timestamps
    and error messages if applicable.
    """

    __tablename__ = "candidate_processing_history"

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(
        db.Integer, db.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    from_status = db.Column(db.String(20), nullable=False)
    to_status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    error_message = db.Column(db.Text)
    duration = db.Column(db.Float, default=0.0)  # Processing duration in seconds

    # Set extend_existing=True to handle duplicate model definitions across modules
    __table_args__ = {"extend_existing": True}

    # Note: The backref approach is used in Candidate model, so we don't define the reverse relationship here

    def __repr__(self):
        """String representation of a processing history entry"""
        return f"<Processing History: {self.from_status} -> {self.to_status} at {self.timestamp}>"


# Status transition function to be added to the Candidate model
def add_status_transition_methods(cls):
    """
    Add status transition methods to the Candidate model.

    This function adds methods for status validation and transitions to the provided class.

    Args:
        cls: The class to add methods to (typically the Candidate model)

    Returns:
        The modified class
    """
    # Define valid status transitions
    status_transitions = {
        "pending": ["processing"],
        "processing": ["complete", "failed"],
        "complete": ["pending"],  # Allow reprocessing of complete candidates
        "failed": ["pending"],  # Allow retrying failed candidates
    }

    def is_valid_transition(self, new_status):
        """
        Check if a status transition is valid

        Args:
            new_status: The new status to transition to

        Returns:
            bool: True if valid, False otherwise
        """
        if self.processing_status not in status_transitions:
            return False

        valid_transitions = status_transitions.get(self.processing_status, [])
        return new_status in valid_transitions

    def transition_to(self, new_status, error_message=None, updated_by_id=None):
        """
        Transition to a new processing status and record in history

        Args:
            new_status: The new status
            error_message: Optional error message (for failed status)
            updated_by_id: ID of the recruiter who triggered the transition

        Raises:
            ValueError: If transition is invalid

        Returns:
            self: For method chaining
        """
        if not self.is_valid_transition(new_status):
            raise ValueError(
                f"Invalid transition from '{self.processing_status}' to '{new_status}'. "
                f"Valid transitions: {status_transitions.get(self.processing_status, [])}"
            )

        old_status = self.processing_status
        self.processing_status = new_status

        if new_status == "failed":
            self.error_message = error_message

        if updated_by_id:
            self.status_updated_by = updated_by_id

        self.add_status_history(old_status, new_status, error_message)
        return self

    def add_status_history(self, from_status, to_status, error_message=None, duration=0.0):
        """
        Add an entry to the status history

        Args:
            from_status: Previous status
            to_status: New status
            error_message: Optional error message
            duration: Processing duration in seconds
        """
        history_entry = CandidateProcessingHistory(
            candidate_id=self.id,
            from_status=from_status,
            to_status=to_status,
            error_message=error_message,
            duration=duration,
        )
        db.session.add(history_entry)

        # Add to relationship for easy access
        if hasattr(self, "processing_history"):
            self.processing_history.append(history_entry)

    # Add methods to the class
    cls.is_valid_transition = is_valid_transition
    cls.transition_to = transition_to
    cls.add_status_history = add_status_history

    return cls
