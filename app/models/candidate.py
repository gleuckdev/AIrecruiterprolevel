"""
Candidate models for AI Recruiter Pro.

This module contains models related to candidates, their skills, and ratings.
"""

from datetime import datetime
from app.app_factory import db


# Association table for many-to-many relationship between candidates and skills
candidate_skills = db.Table(
    'candidate_skills',
    db.Column('candidate_id', db.Integer, db.ForeignKey('candidates.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skills.id'), primary_key=True)
)


class Skill(db.Model):
    """
    Skill model for tracking technical and non-technical skills.
    """
    __tablename__ = 'skills'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50))  # e.g., 'technical', 'soft', 'language'
    
    def __repr__(self):
        return f'<Skill {self.name}>'


class Candidate(db.Model):
    """
    Candidate model - core entity for candidate information.
    """
    __tablename__ = 'candidates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), index=True)
    phone = db.Column(db.String(20))
    location = db.Column(db.String(120))
    
    # Resume details
    resume_path = db.Column(db.String(255))
    resume_text = db.Column(db.Text)
    summary = db.Column(db.Text)
    
    # Experience
    years_experience = db.Column(db.Integer)
    current_title = db.Column(db.String(100))
    current_company = db.Column(db.String(100))
    
    # Education
    education = db.Column(db.Text)
    highest_degree = db.Column(db.String(100))
    
    # Processing metadata
    processing_status = db.Column(db.String(20), default='pending')  # pending, processing, complete, failed
    error_message = db.Column(db.Text)
    source = db.Column(db.String(50))  # manual, public_application, bulk_upload, etc.
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    skills = db.relationship('Skill', secondary=candidate_skills,
                            backref=db.backref('candidates', lazy='dynamic'))
    ratings = db.relationship('CandidateRating', backref='candidate', lazy='dynamic',
                             cascade='all, delete-orphan')
    matches = db.relationship('CandidateJobMatch', backref='candidate', lazy='dynamic',
                             cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Candidate {self.name}>'
    
    @property
    def status(self):
        """Get the candidate's processing status."""
        return self.processing_status
    
    @property
    def skill_list(self):
        """Get a list of skill names."""
        return [skill.name for skill in self.skills]
    
    @property
    def average_rating(self):
        """Calculate the average rating for this candidate."""
        ratings = [r.rating for r in self.ratings if r.active]
        return sum(ratings) / len(ratings) if ratings else 0


class CandidateRating(db.Model):
    """
    Candidate Rating model for storing recruiter evaluations.
    """
    __tablename__ = 'candidate_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('recruiters.id'), nullable=False)
    
    rating = db.Column(db.Integer, nullable=False)  # 1-5 scale
    comment = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)  # For soft deletion
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    recruiter = db.relationship('Recruiter', backref=db.backref('candidate_ratings', lazy='dynamic'))
    
    def __repr__(self):
        return f'<CandidateRating {self.candidate_id} by {self.recruiter_id}: {self.rating}>'


class CandidateProcessingHistory(db.Model):
    """
    Candidate Processing History for tracking status changes.
    """
    __tablename__ = 'candidate_processing_history'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    previous_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    message = db.Column(db.Text)
    
    # Relationships
    candidate = db.relationship('Candidate', backref=db.backref('processing_history', lazy='dynamic'))
    
    def __repr__(self):
        return f'<CandidateProcessingHistory {self.candidate_id}: {self.previous_status} -> {self.new_status}>'