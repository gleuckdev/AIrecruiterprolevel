"""
Candidate Models for AI Recruiter Pro

This module defines candidate-related models for storing resume data,
processing history, and status tracking.
"""

import uuid
from datetime import datetime

# Import ARRAY and JSONB directly from the base module to avoid LSP import issues
from .base import JSONB, db


class Candidate(db.Model):
    """
    Candidate model for storing resume information

    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to recruiter who uploaded/owns this candidate
        first_name (str): Candidate's first name
        last_name (str): Candidate's last name
        email (str): Candidate's email
        phone (str): Candidate's phone number
        location (str): Geographic location
        title (str): Current or most recent job title
        resume_url (str): URL to stored resume file
        resume_text (str): Extracted text from resume
        skills (str): Comma-separated list of skills
        skills_array (list): Array of skills for easier searching
        experience_level (str): Experience level (junior, mid, senior, etc.)
        summary (str): Brief professional summary
        created_at (datetime): Record creation timestamp
        updated_at (datetime): Last update timestamp
        source (str): Source of the candidate (manual, bulk_upload, public_application)
        processing_status (str): Current processing state (pending, processing, complete, failed)
        error_message (str): Error message if processing failed
        reference_number (str): Unique reference number for public applicants
        embedding (list): Vector embedding for semantic search
    """

    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True)
    uploaded_by = db.Column(
        db.Integer, db.ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=True
    )

    # Personal information
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))

    # Properties for backwards compatibility
    @property
    def first_name(self):
        """Get first name from name field"""
        if self.name and " " in self.name:
            return self.name.split(" ")[0]
        return self.name

    @first_name.setter
    def first_name(self, value):
        """Set first name part of name field"""
        if value:
            last = self.last_name or ""
            self.name = f"{value} {last}".strip()

    @property
    def last_name(self):
        """Get last name from name field"""
        if self.name and " " in self.name:
            return " ".join(self.name.split(" ")[1:])
        return ""

    @last_name.setter
    def last_name(self, value):
        """Set last name part of name field"""
        if value:
            first = self.first_name or ""
            self.name = f"{first} {value}".strip()

    # Compatibility for user_id
    @property
    def user_id(self):
        """Get user_id from uploaded_by field"""
        return self.uploaded_by

    @user_id.setter
    def user_id(self, value):
        """Set uploaded_by field from user_id"""
        self.uploaded_by = value

    phone = db.Column(db.String(20))
    # location is not in the actual DB schema
    resume_file = db.Column(db.String(255))
    gcs_url = db.Column(db.String(255))
    job_id = db.Column(db.Integer)

    # Compatibility property for location
    @property
    def location(self):
        """Compatibility property for location"""
        return None

    @location.setter
    def location(self, value):
        """Silently ignore location setting"""
        pass

    # Professional information
    parsed_data = db.Column(db.JSON)
    persona = db.Column(db.JSON)
    status = db.Column(db.String(20))
    status_notes = db.Column(db.Text)
    status_updated_at = db.Column(db.DateTime)
    status_updated_by = db.Column(
        db.Integer, db.ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True
    )
    match_score = db.Column(db.Float)
    resume_text = db.Column(db.Text)

    # Compatibility properties for missing fields
    @property
    def title(self):
        """Get title from parsed_data"""
        if self.parsed_data and "title" in self.parsed_data:
            return self.parsed_data["title"]
        return None

    @title.setter
    def title(self, value):
        """Set title in parsed_data"""
        if not self.parsed_data:
            self.parsed_data = {}
        if value:
            self.parsed_data["title"] = value

    @property
    def resume_url(self):
        """Compatibility for resume_url"""
        return self.gcs_url

    @resume_url.setter
    def resume_url(self, value):
        """Set resume_url to gcs_url"""
        self.gcs_url = value

    @property
    def skills(self):
        """Get skills from parsed_data"""
        if self.parsed_data and "skills" in self.parsed_data:
            return self.parsed_data["skills"]
        return None

    @skills.setter
    def skills(self, value):
        """Set skills in parsed_data"""
        if not self.parsed_data:
            self.parsed_data = {}
        if value:
            self.parsed_data["skills"] = value

    @property
    def skills_array(self):
        """Get skills array from parsed_data"""
        if self.parsed_data and "skills_array" in self.parsed_data:
            return self.parsed_data["skills_array"]
        return []

    @skills_array.setter
    def skills_array(self, value):
        """Set skills_array in parsed_data"""
        if not self.parsed_data:
            self.parsed_data = {}
        if value:
            self.parsed_data["skills_array"] = value

    @property
    def experience_level(self):
        """Get experience_level from parsed_data"""
        if self.parsed_data and "experience_level" in self.parsed_data:
            return self.parsed_data["experience_level"]
        return None

    @experience_level.setter
    def experience_level(self, value):
        """Set experience_level in parsed_data"""
        if not self.parsed_data:
            self.parsed_data = {}
        if value:
            self.parsed_data["experience_level"] = value

    @property
    def summary(self):
        """Get summary from parsed_data"""
        if self.parsed_data and "summary" in self.parsed_data:
            return self.parsed_data["summary"]
        return None

    @summary.setter
    def summary(self, value):
        """Set summary in parsed_data"""
        if not self.parsed_data:
            self.parsed_data = {}
        if value:
            self.parsed_data["summary"] = value

    # Metadata and processing information
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = db.Column(db.String(20), default="manual")
    processing_status = db.Column(db.String(20), default="pending")
    error_message = db.Column(db.Text)

    # Virtual property for reference_number (not in DB schema)
    _reference_number = None

    @property
    def reference_number(self):
        """Get reference number (generated on demand)"""
        if not self._reference_number:
            self._reference_number = str(uuid.uuid4())
        return self._reference_number

    @reference_number.setter
    def reference_number(self, value):
        """Store reference number in memory only"""
        self._reference_number = value

    # Vector embedding for semantic search
    embedding = db.Column(JSONB)

    # Relationships
    processing_history = db.relationship(
        "CandidateProcessingHistory",
        backref="candidate",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    status_history = db.relationship(
        "CandidateStatusHistory", backref="candidate", lazy="dynamic", cascade="all, delete-orphan"
    )

    # User will be added back in later once both models are created
    # user = db.relationship('User', backref=db.backref('candidates', lazy='dynamic'))

    # Valid status transitions
    _status_transitions = {
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
        current = self.processing_status
        if current not in self._status_transitions:
            return False

        return new_status in self._status_transitions[current]

    def transition_to(self, new_status, error_message=None):
        """
        Transition to a new processing status and record in history

        Args:
            new_status: The new status
            error_message: Optional error message (for failed status)

        Raises:
            ValueError: If transition is invalid
        """
        if not self.is_valid_transition(new_status):
            raise ValueError(f"Invalid status transition: {self.processing_status} -> {new_status}")

        old_status = self.processing_status
        self.processing_status = new_status

        # Handle error message for failed status
        if new_status == "failed":
            self.error_message = error_message
        elif new_status == "pending" and old_status == "failed":
            # Clear error message when retrying
            self.error_message = None

        # Record in history
        self.add_status_history(old_status, new_status, error_message)

    def add_status_history(self, from_status, to_status, error_message=None):
        """
        Add an entry to the status history

        Args:
            from_status: Previous status
            to_status: New status
            error_message: Optional error message
        """
        # Calculate duration (placeholder)
        duration = 0.0

        history = CandidateProcessingHistory(
            candidate_id=self.id,
            from_status=from_status,
            to_status=to_status,
            error_message=error_message,
            duration=duration,
        )
        db.session.add(history)

    def __init__(self, **kwargs):
        """Initialize a new candidate"""
        super().__init__(**kwargs)

        # Generate reference number if not provided
        if not self.reference_number:
            self.reference_number = str(uuid.uuid4())

    def get_full_name(self):
        """
        Get candidate's full name

        Returns:
            str: Full name or 'Unknown Candidate' if not available
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return "Unknown Candidate"

    def to_dict(self):
        """
        Convert candidate to dictionary for API responses

        Returns:
            dict: Dictionary representation of candidate
        """
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "title": self.title,
            "skills": self.skills,
            "skills_array": self.skills_array,
            "experience_level": self.experience_level,
            "summary": self.summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "source": self.source,
            "processing_status": self.processing_status,
            "reference_number": self.reference_number,
            "has_resume": bool(self.resume_url),
        }

    def __repr__(self):
        return f"<Candidate {self.get_full_name()} {self.id}>"


class CandidateStatusHistory(db.Model):
    """
    Track changes to candidate status during the recruitment process

    Attributes:
        id (int): Primary key
        candidate_id (int): Foreign key to candidate
        from_status (str): Previous status (database column)
        to_status (str): New status (database column)
        timestamp (datetime): When the change occurred
        notes (str): Optional note about the change (database column)
        updated_by (int): ID of the user who made the change (database column)
    """

    __tablename__ = "candidate_status_history"

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(
        db.Integer, db.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    from_status = db.Column(db.String(20), nullable=False)
    to_status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey("recruiters.id"), nullable=True)

    # Define indexes for better query performance
    __table_args__ = (
        db.Index("idx_candidate_status_history_candidate_id", "candidate_id"),
        db.Index("idx_candidate_status_history_timestamp", "timestamp"),
    )

    # Define relationships
    updater = db.relationship("Recruiter", foreign_keys=[updated_by], backref="status_changes")

    # For backward compatibility with code using the new column names
    @property
    def old_status(self):
        return self.from_status

    @old_status.setter
    def old_status(self, value):
        self.from_status = value

    @property
    def new_status(self):
        return self.to_status

    @new_status.setter
    def new_status(self, value):
        self.to_status = value

    @property
    def note(self):
        return self.notes

    @note.setter
    def note(self, value):
        self.notes = value

    @property
    def user_id(self):
        return self.updated_by

    @user_id.setter
    def user_id(self, value):
        self.updated_by = value

    def __repr__(self):
        return (
            f"<CandidateStatusHistory {self.candidate_id} {self.from_status} -> {self.to_status}>"
        )


class CandidateProcessingHistory(db.Model):
    """
    Track processing attempts and errors for candidate resume processing

    Attributes:
        id (int): Primary key
        candidate_id (int): Foreign key to candidate
        from_status (str): Previous processing status
        to_status (str): New processing status
        timestamp (datetime): When the change occurred
        error_message (str): Error message if processing failed
        duration (float): How long the processing took in seconds
    """

    __tablename__ = "candidate_processing_history"

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(
        db.Integer, db.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    from_status = db.Column(db.String(20), nullable=False)
    to_status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    error_message = db.Column(db.Text)
    duration = db.Column(db.Float, default=0.0)

    # Define indexes for better query performance and set extend_existing=True
    # to handle duplicate model definitions across modules
    __table_args__ = (
        db.Index("idx_candidate_processing_history_candidate_id", "candidate_id"),
        db.Index("idx_candidate_processing_history_timestamp", "timestamp"),
        {"extend_existing": True},
    )

    # Backward compatibility property
    @property
    def old_status(self):
        """Get old_status from from_status"""
        return self.from_status

    @old_status.setter
    def old_status(self, value):
        """Set from_status from old_status"""
        self.from_status = value

    # Backward compatibility property
    @property
    def new_status(self):
        """Get new_status from to_status"""
        return self.to_status

    @new_status.setter
    def new_status(self, value):
        """Set to_status from new_status"""
        self.to_status = value

    def __repr__(self):
        return f"<CandidateProcessingHistory {self.candidate_id} {self.from_status} -> {self.to_status}>"
