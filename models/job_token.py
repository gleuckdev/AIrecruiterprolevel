"""
Job Token Models for AI Recruiter Pro

This module defines job token-related models for detecting
similar job postings and preventing duplicates.
"""

from datetime import datetime

from app import db


class JobToken(db.Model):
    """
    Job Token Model

    This model stores embedding vectors for jobs to enable similarity comparison.

    Attributes:
        id (int): Primary key
        job_id (int): Foreign key to job
        token (array): Vector embedding of the job description
        created_at (datetime): When the token was created
        updated_at (datetime): When the token was last updated
    """

    __tablename__ = "job_tokens"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(
        db.Integer,
        db.ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    token = db.Column(db.JSON)  # Store vector as JSON array
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to Job model
    job = db.relationship(
        "Job", backref=db.backref("token", uselist=False, cascade="all, delete-orphan"), lazy=True
    )

    def __repr__(self):
        return f"<JobToken for job {self.job_id}>"


class JobSimilarity(db.Model):
    """
    Job Similarity Model

    This model records similarity between jobs based on token comparison.

    Attributes:
        id (int): Primary key
        job_id (int): Foreign key to source job
        similar_job_id (int): Foreign key to similar job
        similarity_score (float): Similarity score between 0 and 1
        created_at (datetime): When the similarity was detected
        updated_at (datetime): When the similarity was last updated
    """

    __tablename__ = "job_similarities"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(
        db.Integer, db.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    similar_job_id = db.Column(
        db.Integer, db.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    similarity_score = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Define unique constraint
    __table_args__ = (db.UniqueConstraint("job_id", "similar_job_id", name="uix_job_similarity"),)

    # Relationships to Job model
    job = db.relationship(
        "Job", foreign_keys=[job_id], backref=db.backref("similar_jobs", lazy=True)
    )
    similar_job = db.relationship(
        "Job", foreign_keys=[similar_job_id], backref=db.backref("similar_to", lazy=True)
    )

    def __repr__(self):
        return (
            f"<JobSimilarity {self.job_id} -> {self.similar_job_id}: {self.similarity_score:.2f}>"
        )
