"""
Job models for AI Recruiter Pro.

This module contains models related to job postings, their requirements, and tokens.
"""

from datetime import datetime
from app.app_factory import db


# Association table for many-to-many relationship between jobs and skills
job_skills = db.Table(
    'job_skills',
    db.Column('job_id', db.Integer, db.ForeignKey('jobs.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skills.id'), primary_key=True)
)


class Job(db.Model):
    """
    Job model - core entity for job postings.
    """
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    
    # Company details
    company = db.Column(db.String(100))
    department = db.Column(db.String(100))
    location = db.Column(db.String(100))
    remote = db.Column(db.Boolean, default=False)
    
    # Job details
    job_type = db.Column(db.String(50))  # full-time, part-time, contract, etc.
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    currency = db.Column(db.String(3), default='USD')
    
    # Tracking
    status = db.Column(db.String(20), default='draft')  # draft, open, closed
    posted_date = db.Column(db.DateTime)
    closing_date = db.Column(db.DateTime)
    
    # External IDs
    external_id = db.Column(db.String(100))  # ID from external ATS
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_by = db.Column(db.Integer, db.ForeignKey('recruiters.id'))
    creator = db.relationship('Recruiter', backref='jobs')
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    
    skills = db.relationship('Skill', secondary=job_skills,
                           backref=db.backref('jobs', lazy='dynamic'))
    tokens = db.relationship('JobToken', backref='job', lazy='dynamic',
                           cascade='all, delete-orphan')
    matches = db.relationship('CandidateJobMatch', backref='job', lazy='dynamic',
                            cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Job {self.title}>'
    
    @property
    def skill_list(self):
        """Get a list of skill names."""
        return [skill.name for skill in self.skills]
    
    @property
    def salary_range(self):
        """Get the salary range as a formatted string."""
        if not self.salary_min and not self.salary_max:
            return None
        
        if self.salary_min and self.salary_max:
            return f"{self.salary_min:,} - {self.salary_max:,} {self.currency}"
        elif self.salary_min:
            return f"{self.salary_min:,}+ {self.currency}"
        else:
            return f"Up to {self.salary_max:,} {self.currency}"


class JobToken(db.Model):
    """
    JobToken model for semantic analysis of job descriptions.
    
    These tokens are used to find similar jobs and for semantic matching
    with candidate profiles.
    """
    __tablename__ = 'job_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    token = db.Column(db.String(50), nullable=False)
    weight = db.Column(db.Float, default=1.0)
    token_type = db.Column(db.String(20))  # skill, requirement, qualification, etc.
    
    def __repr__(self):
        return f'<JobToken {self.token} for Job {self.job_id}>'


class Company(db.Model):
    """
    Company model for organizing jobs by company.
    """
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    website = db.Column(db.String(255))
    industry = db.Column(db.String(100))
    
    # Relationships
    jobs = db.relationship('Job', backref='company_obj')
    departments = db.relationship('Department', backref='company',
                                cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Company {self.name}>'


class Department(db.Model):
    """
    Department model for organizing jobs by department within companies.
    """
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Relationships
    jobs = db.relationship('Job', backref='department_obj')
    
    def __repr__(self):
        return f'<Department {self.name} at {self.company.name}>'