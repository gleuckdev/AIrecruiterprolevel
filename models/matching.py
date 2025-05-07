"""
Matching Models for AI Recruiter Pro

This module defines models for tracking job-candidate matches
and related matching data.
"""

from datetime import datetime

import numpy as np
from sqlalchemy.dialects.postgresql import JSONB

from .base import db


class CandidateJobMatch(db.Model):
    """
    Model for storing matches between candidates and jobs

    Attributes:
        id (int): Primary key
        candidate_id (int): Foreign key to candidate
        job_id (int): Foreign key to job
        match_score (float): Overall match score between 0 and 1
        skills_match_score (float): Skills-based match score
        embedding_match_score (float): Embedding similarity score
        match_data (dict): Additional match details
        user_id (int): User who created this match
        created_at (datetime): When the match was created
        updated_at (datetime): When the match was last updated
    """

    __tablename__ = "candidate_job_matches"

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(
        db.Integer, db.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    match_score = db.Column(db.Float, default=0.0)
    skills_match_score = db.Column(db.Float, default=0.0)
    embedding_match_score = db.Column(db.Float, default=0.0)
    match_data = db.Column(JSONB)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Define a unique constraint so there's only one match per candidate-job pair
    __table_args__ = (db.UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job"),)

    def calculate_match_score(self, candidate=None, job=None):
        """
        Calculate match score between candidate and job

        Args:
            candidate: Optional Candidate object
            job: Optional Job object

        Returns:
            float: Match score between 0 and 1
        """
        from .candidate import Candidate
        from .job import Job

        # Get objects if not provided
        if not candidate:
            candidate = Candidate.query.get(self.candidate_id)
        if not job:
            job = Job.query.get(self.job_id)

        if not candidate or not job:
            return 0.0

        # Calculate skills match score (40%)
        self.skills_match_score = self._calculate_skills_match(candidate, job)

        # Calculate embedding match score (60%) if embeddings exist
        if (
            hasattr(candidate, "embedding")
            and candidate.embedding
            and hasattr(job, "embedding")
            and job.embedding
        ):
            self.embedding_match_score = self._calculate_embedding_match(
                candidate.embedding, job.embedding
            )
        else:
            # If embeddings don't exist, just use skills match with 100% weight
            self.embedding_match_score = 0.0
            self.match_score = self.skills_match_score
            return self.match_score

        # Combine scores with weights - convert numpy arrays to scalars
        skills_score = (
            float(self.skills_match_score)
            if hasattr(self.skills_match_score, "tolist")
            else self.skills_match_score
        )
        embedding_score = (
            float(self.embedding_match_score)
            if hasattr(self.embedding_match_score, "tolist")
            else self.embedding_match_score
        )
        self.match_score = (skills_score * 0.4) + (embedding_score * 0.6)

        # Update match data
        self.match_data = {
            "skills_match_score": float(skills_score),
            "embedding_match_score": float(embedding_score),
            "total_score": float(self.match_score),
            "calculation_timestamp": datetime.utcnow().isoformat(),
        }

        return self.match_score

    def _calculate_skills_match(self, candidate, job):
        """
        Calculate skill match score based on skill overlap

        Args:
            candidate: Candidate object
            job: Job object

        Returns:
            float: Skill match score between 0 and 1
        """
        # Get candidate skills
        candidate_skills = set()
        if hasattr(candidate, "skills_array") and candidate.skills_array:
            candidate_skills = {s.lower() for s in candidate.skills_array}

        # Get job skills
        job_skills = set()
        if hasattr(job, "skills_array") and job.skills_array:
            job_skills = {s.lower() for s in job.skills_array}

        # If either set is empty, return 0
        if not candidate_skills or not job_skills:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(candidate_skills.intersection(job_skills))
        union = len(candidate_skills.union(job_skills))

        return intersection / union if union > 0 else 0.0

    def _calculate_embedding_match(self, candidate_embedding, job_embedding):
        """
        Calculate cosine similarity between embeddings

        Args:
            candidate_embedding: Candidate embedding vector
            job_embedding: Job embedding vector

        Returns:
            float: Similarity score between 0 and 1
        """
        # Handle potential input types
        if isinstance(candidate_embedding, list):
            candidate_embedding = np.array(candidate_embedding)
        if isinstance(job_embedding, list):
            job_embedding = np.array(job_embedding)

        # Calculate cosine similarity
        dot_product = np.dot(candidate_embedding, job_embedding)
        norm_candidate = np.linalg.norm(candidate_embedding)
        norm_job = np.linalg.norm(job_embedding)

        if norm_candidate == 0 or norm_job == 0:
            return 0.0

        similarity = dot_product / (norm_candidate * norm_job)

        # Ensure result is within bounds
        return max(0.0, min(1.0, similarity))

    def to_dict(self):
        """
        Convert match to dictionary for API responses

        Returns:
            dict: Dictionary representation of match
        """
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "job_id": self.job_id,
            "match_score": self.match_score,
            "skills_match_score": self.skills_match_score,
            "embedding_match_score": self.embedding_match_score,
            "match_data": self.match_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<CandidateJobMatch {self.candidate_id}:{self.job_id} Score:{self.match_score:.2f}>"
