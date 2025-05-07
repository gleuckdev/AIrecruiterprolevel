"""
Match Models for AI Recruiter Pro

This module defines models for tracking job-candidate matches,
match history, and score calculations.
"""

from datetime import datetime

import numpy as np
from sqlalchemy.dialects.postgresql import JSONB

from .base import db


class JobCandidateMatch(db.Model):
    """
    Model for storing matches between jobs and candidates

    Attributes:
        id (int): Primary key
        job_id (int): Foreign key to job
        candidate_id (int): Foreign key to candidate
        score (float): Match score between 0 and 1
        match_data (dict): Detailed match data (skill matches, etc.)
        created_at (datetime): When the match was created
        updated_at (datetime): When the match was last updated
        status (str): Current status of the match (new, viewed, shortlisted, etc.)
        user_id (int): User who created/updated this match
    """

    __tablename__ = "job_candidate_matches"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    candidate_id = db.Column(
        db.Integer, db.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    score = db.Column(db.Float, default=0.0)
    match_data = db.Column(JSONB)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default="new")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # These relationships will be uncommented once all models are fully created
    # job = db.relationship('Job', backref=db.backref('candidate_matches', lazy='dynamic', cascade='all, delete-orphan'))
    # candidate = db.relationship('Candidate', backref=db.backref('job_matches', lazy='dynamic', cascade='all, delete-orphan'))
    # user = db.relationship('User', backref=db.backref('created_matches', lazy='dynamic'))

    def calculate_score(self, job_embedding=None, candidate_embedding=None):
        """
        Calculate match score between job and candidate

        Uses a combination of:
        - Cosine similarity between embeddings (60%)
        - Skill overlap (40%)

        Args:
            job_embedding (list, optional): Job embedding (if not stored on job)
            candidate_embedding (list, optional): Candidate embedding (if not stored on candidate)

        Returns:
            float: Match score between 0 and 1
        """
        from models import Candidate, Job

        # Get embeddings
        if not job_embedding:
            job = Job.query.get(self.job_id)
            job_embedding = job.embedding if job else None

        if not candidate_embedding:
            candidate = Candidate.query.get(self.candidate_id)
            candidate_embedding = candidate.embedding if candidate else None

        # If embeddings are missing, fall back to skill matching only
        if not job_embedding or not candidate_embedding:
            return self._calculate_skill_match_score()

        # Calculate embedding similarity (60% of score)
        embedding_similarity = self._cosine_similarity(job_embedding, candidate_embedding)
        embedding_score = embedding_similarity * 0.6

        # Calculate skill match (40% of score)
        skill_score = self._calculate_skill_match_score() * 0.4

        # Combine scores
        total_score = embedding_score + skill_score

        # Update score
        self.score = total_score
        self.match_data = self.match_data or {}
        self.match_data.update(
            {
                "embedding_similarity": float(embedding_similarity),
                "skill_match_score": float(skill_score),
                "total_score": float(total_score),
                "last_calculated_at": datetime.utcnow().isoformat(),
            }
        )

        return total_score

    def _cosine_similarity(self, vector_a, vector_b):
        """
        Calculate cosine similarity between two vectors

        Args:
            vector_a: First vector
            vector_b: Second vector

        Returns:
            float: Similarity between 0 and 1
        """
        if not vector_a or not vector_b:
            return 0.0

        # Convert to numpy arrays
        if isinstance(vector_a, list):
            vector_a = np.array(vector_a)
        if isinstance(vector_b, list):
            vector_b = np.array(vector_b)

        # Calculate cosine similarity
        dot_product = np.dot(vector_a, vector_b)
        norm_a = np.linalg.norm(vector_a)
        norm_b = np.linalg.norm(vector_b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        similarity = dot_product / (norm_a * norm_b)

        # Ensure result is within bounds
        return max(0.0, min(1.0, similarity))

    def _calculate_skill_match_score(self):
        """
        Calculate skill match score based on skill overlap

        Returns:
            float: Score between 0 and 1
        """
        from models import Candidate, Job

        # Get job and candidate
        job = Job.query.get(self.job_id)
        candidate = Candidate.query.get(self.candidate_id)

        if not job or not candidate:
            return 0.0

        # Get skills
        job_skills = {s.lower() for s in (job.skills_array or [])}
        candidate_skills = {s.lower() for s in (candidate.skills_array or [])}

        # If either set is empty, return 0
        if not job_skills or not candidate_skills:
            return 0.0

        # Calculate Jaccard similarity: intersection / union
        intersection = len(job_skills.intersection(candidate_skills))
        union = len(job_skills.union(candidate_skills))

        if union == 0:
            return 0.0

        return intersection / union

    def to_dict(self):
        """
        Convert match to dictionary for API responses

        Returns:
            dict: Dictionary representation of match
        """
        return {
            "id": self.id,
            "job_id": self.job_id,
            "candidate_id": self.candidate_id,
            "score": self.score,
            "match_data": self.match_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "status": self.status,
        }

    def __repr__(self):
        return f"<JobCandidateMatch Job:{self.job_id} Candidate:{self.candidate_id} Score:{self.score:.2f}>"


class MatchHistory(db.Model):
    """
    Model for tracking match history

    Attributes:
        id (int): Primary key
        match_id (int): Foreign key to job-candidate match
        old_score (float): Previous match score
        new_score (float): New match score
        old_status (str): Previous match status
        new_status (str): New match status
        note (str): Optional note about the change
        user_id (int): User who made the change
        timestamp (datetime): When the change occurred
    """

    __tablename__ = "match_history"

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(
        db.Integer, db.ForeignKey("job_candidate_matches.id", ondelete="CASCADE"), nullable=False
    )
    old_score = db.Column(db.Float)
    new_score = db.Column(db.Float)
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20))
    note = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MatchHistory {self.match_id} {self.old_status or 'No status'} -> {self.new_status or 'No status'}>"
