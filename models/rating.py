"""
Rating and prompt-related models for AI Recruiter Pro

This module contains all rating-related models including:
- CandidateRating: For storing recruiter ratings of candidates
- RatingCriterion: For defining rating criteria
- RatingScale: For defining rating scales
- PromptTemplate: For versioned prompt templates
- PromptAudit: For auditing AI prompt usage
- FlaggedPrompt: For tracking problematic prompts
"""

import logging
from datetime import datetime

from .base import db

# Set up logger
logger = logging.getLogger(__name__)


class CandidateRating(db.Model):
    """
    Model for storing recruiter ratings of candidates
    """

    __tablename__ = "candidate_ratings"

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False)
    recruiter_id = db.Column(db.Integer, db.ForeignKey("recruiters.id"), nullable=False)
    score = db.Column(db.Float, nullable=False)  # 0-1 rating scale (aligned with OpenAI scores)
    notes = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)  # Whether this rating is active
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    candidate = db.relationship("Candidate", backref=db.backref("ratings", lazy=True))
    # Define a one-way relationship to Recruiter with overlaps parameter
    recruiter = db.relationship("Recruiter", foreign_keys=[recruiter_id], overlaps="ratings")

    def __repr__(self):
        return f"<CandidateRating {self.candidate_id} by {self.recruiter_id}: {self.score}>"


class RatingCriterion(db.Model):
    """
    Model for defining rating criteria
    """

    __tablename__ = "rating_criteria"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    weight = db.Column(db.Float, default=1.0)  # Importance weight for weighted averages
    job_specific = db.Column(db.Boolean, default=False)  # Whether this criterion is job-specific
    job_id = db.Column(
        db.Integer, db.ForeignKey("jobs.id"), nullable=True
    )  # Only set if job_specific is True
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<RatingCriterion {self.name}>"


class RatingScale(db.Model):
    """
    Model for defining rating scales
    """

    __tablename__ = "rating_scales"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    min_value = db.Column(db.Float, nullable=False, default=0.0)
    max_value = db.Column(db.Float, nullable=False, default=1.0)
    step = db.Column(db.Float, nullable=False, default=0.1)  # Increment step
    labels = db.Column(db.JSON)  # Optional value-to-label mapping
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<RatingScale {self.name} ({self.min_value}-{self.max_value})>"


class PromptTemplate(db.Model):
    """
    Stores versioned prompt templates used by the system
    Allows for tracking changes and auditing prompt evolution
    """

    __tablename__ = "prompt_templates"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # e.g., 'resume_parse'
    version = db.Column(db.String(10), nullable=False)  # e.g., 'v1', 'v2'
    template_text = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    parameters = db.Column(db.JSON)  # Parameter definitions and defaults
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("recruiters.id"))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    bias_evaluation = db.Column(db.Text, nullable=True)
    bias_categories = db.Column(db.Text, nullable=True)

    # Define unique constraint on name and version
    __table_args__ = (
        db.UniqueConstraint("name", "version", name="uq_prompt_template_name_version"),
    )

    # Relationships
    creator = db.relationship("Recruiter", foreign_keys=[created_by])

    @classmethod
    def get_active_template(cls, name):
        """Get the currently active template for a given name"""
        return cls.query.filter_by(name=name, is_active=True).order_by(cls.version.desc()).first()

    def __repr__(self):
        return f"<PromptTemplate {self.name} {self.version}>"


class PromptAudit(db.Model):
    """
    Stores anonymized prompt audit logs for review by administrators
    This model provides oversight of AI prompt usage and results
    """

    __tablename__ = "prompt_audits"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    prompt_type = db.Column(
        db.String(50), nullable=False, index=True
    )  # e.g., 'resume_parse', 'persona', etc.
    prompt_version = db.Column(db.String(10), nullable=False)  # e.g., 'v1', 'v2'
    prompt_text = db.Column(db.Text)  # Redacted prompt text
    input_data = db.Column(db.JSON)  # Anonymized input data
    ai_response_snippet = db.Column(db.Text)  # Snippet/summary of AI response
    user_id = db.Column(db.String(50))  # Obfuscated user ID
    candidate_id = db.Column(db.String(50))  # Obfuscated candidate ID
    has_been_reviewed = db.Column(db.Boolean, default=False)
    review_notes = db.Column(db.Text)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("recruiters.id"))

    # Relationships
    reviewer = db.relationship("Recruiter", foreign_keys=[reviewed_by])

    def __repr__(self):
        return f"<PromptAudit {self.id} {self.prompt_type}>"


class FlaggedPrompt(db.Model):
    """
    Stores prompts that have been flagged for potential bias or issues
    """

    __tablename__ = "flagged_prompts"

    id = db.Column(db.Integer, primary_key=True)
    prompt_audit_id = db.Column(db.Integer, db.ForeignKey("prompt_audits.id"), nullable=False)
    flagged_by = db.Column(db.Integer, db.ForeignKey("recruiters.id"), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    resolution = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")  # 'pending', 'resolved', 'dismissed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey("recruiters.id"))

    # Relationships
    audit = db.relationship("PromptAudit", backref="flags")
    flagger = db.relationship("Recruiter", foreign_keys=[flagged_by])
    resolver = db.relationship("Recruiter", foreign_keys=[resolved_by])

    def __repr__(self):
        return f"<FlaggedPrompt {self.id} {self.status}>"
