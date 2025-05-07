"""
Matching models for AI Recruiter Pro.

This module contains models related to candidate-job matching and match details.
"""

from datetime import datetime
from app.app_factory import db


class CandidateJobMatch(db.Model):
    """
    CandidateJobMatch model for storing match results between candidates and jobs.
    """
    __tablename__ = 'candidate_job_matches'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    
    # Overall match score
    match_score = db.Column(db.Float, default=0.0)  # 0-100 scale
    
    # Component scores
    embedding_score = db.Column(db.Float)  # Semantic embedding similarity
    skill_score = db.Column(db.Float)  # Direct skill matching
    experience_score = db.Column(db.Float)  # Experience level match
    
    # Matching metadata
    matched_at = db.Column(db.DateTime, default=datetime.utcnow)
    model_version = db.Column(db.String(20))  # Version of matching algorithm used
    
    # Status tracking
    status = db.Column(db.String(20), default='new')  # new, reviewed, contacted, rejected
    reviewed_by = db.Column(db.Integer, db.ForeignKey('recruiters.id'))
    reviewer = db.relationship('Recruiter', backref='reviewed_matches')
    
    # Relationships
    details = db.relationship('MatchDetail', backref='match', lazy='dynamic',
                             cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CandidateJobMatch C:{self.candidate_id} J:{self.job_id} Score:{self.match_score:.1f}>'
    
    # Define unique constraint to prevent duplicate matches
    __table_args__ = (
        db.UniqueConstraint('candidate_id', 'job_id', name='_candidate_job_match_uc'),
    )


class MatchDetail(db.Model):
    """
    MatchDetail model for storing detailed matching information.
    """
    __tablename__ = 'match_details'
    
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('candidate_job_matches.id'), nullable=False)
    
    category = db.Column(db.String(50), nullable=False)  # skills, experience, education, etc.
    name = db.Column(db.String(100), nullable=False)  # specific detail being matched
    
    # Match scores
    weight = db.Column(db.Float, default=1.0)  # Weight of this detail in overall score
    score = db.Column(db.Float)  # Score for this specific detail
    
    # Explanation
    notes = db.Column(db.Text)  # Explanation of the match detail
    
    def __repr__(self):
        return f'<MatchDetail {self.category}:{self.name} Score:{self.score:.1f}>'


class BiasAudit(db.Model):
    """
    BiasAudit model for tracking potential bias in the matching process.
    """
    __tablename__ = 'bias_audits'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=True)
    
    # Bias detection
    bias_type = db.Column(db.String(50), nullable=False)  # gender, age, ethnicity, etc.
    confidence = db.Column(db.Float)  # Confidence in bias detection (0-1)
    severity = db.Column(db.Integer)  # Severity level (1-5)
    
    # Context
    context = db.Column(db.Text)  # The text that triggered the bias detection
    remediation = db.Column(db.Text)  # Suggested remediation
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed = db.Column(db.Boolean, default=False)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('recruiters.id'))
    
    # Relationships
    candidate = db.relationship('Candidate', backref='bias_audits')
    job = db.relationship('Job', backref='bias_audits')
    reviewer = db.relationship('Recruiter', backref='bias_reviews')
    
    def __repr__(self):
        return f'<BiasAudit {self.bias_type} C:{self.candidate_id} Severity:{self.severity}>'