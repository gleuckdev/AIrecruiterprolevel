"""
Shared Models for AI Recruiter Pro

This module defines shared models used across multiple areas of the application.
These include skill-related models and other common entities.
"""

from datetime import datetime

from .base import db


class Skill(db.Model):
    """
    Skill model for storing skills used by both jobs and candidates

    Attributes:
        id (int): Primary key
        name (str): Skill name
        category (str): Skill category (programming, soft skills, etc.)
        created_at (datetime): When the skill was created
    """

    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Skill {self.name}>"


class CandidateSkill(db.Model):
    """
    Association model for linking candidates to skills

    Attributes:
        id (int): Primary key
        candidate_id (int): Foreign key to candidate
        skill_id (int): Foreign key to skill
        years_experience (int): Years of experience with this skill
        proficiency_level (str): Self-assessed proficiency level
        is_highlighted (bool): Whether this is a highlighted/featured skill
    """

    __tablename__ = "candidate_skills"

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(
        db.Integer, db.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    years_experience = db.Column(db.Integer, default=0)
    proficiency_level = db.Column(db.String(20))
    is_highlighted = db.Column(db.Boolean, default=False)

    # Define a unique constraint so candidates can't have duplicate skills
    __table_args__ = (db.UniqueConstraint("candidate_id", "skill_id", name="uq_candidate_skill"),)

    # Relationships
    skill = db.relationship(
        "Skill",
        backref=db.backref("candidate_skills", lazy="dynamic", cascade="all, delete-orphan"),
    )

    def __repr__(self):
        return f"<CandidateSkill {self.candidate_id}:{self.skill_id}>"


class JobSkill(db.Model):
    """
    Association model for linking jobs to skills

    Attributes:
        id (int): Primary key
        job_id (int): Foreign key to job
        skill_id (int): Foreign key to skill
        is_required (bool): Whether this skill is required or just preferred
        min_years_experience (int): Minimum years of experience required for this skill
        importance (int): Importance weight for matching algorithm (1-10)
    """

    __tablename__ = "job_skills"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    is_required = db.Column(db.Boolean, default=True)
    min_years_experience = db.Column(db.Integer, default=0)
    importance = db.Column(db.Integer, default=5)  # 1-10 scale

    # Define a unique constraint so jobs can't have duplicate skills
    __table_args__ = (db.UniqueConstraint("job_id", "skill_id", name="uq_job_skill"),)

    # Relationships
    skill = db.relationship(
        "Skill", backref=db.backref("job_skills", lazy="dynamic", cascade="all, delete-orphan")
    )

    def __repr__(self):
        return f"<JobSkill {self.job_id}:{self.skill_id} ({'Required' if self.is_required else 'Preferred'})>"
