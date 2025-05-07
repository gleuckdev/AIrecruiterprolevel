"""
Models package for AI Recruiter Pro.

This package contains all database models used in the application.
"""

from app.models.user import Permission, Role, Recruiter, Session
from app.models.candidate import Skill, Candidate, CandidateRating, CandidateProcessingHistory
from app.models.job import Job, JobToken, Company, Department
from app.models.matching import CandidateJobMatch, MatchDetail, BiasAudit
from app.models.api import ApiLog, Invitation, PasswordReset

# Import all models here so they are available through the models package
__all__ = [
    'Permission',
    'Role',
    'Recruiter',
    'Session',
    'Skill',
    'Candidate',
    'CandidateRating',
    'CandidateProcessingHistory',
    'Job',
    'JobToken',
    'Company',
    'Department',
    'CandidateJobMatch',
    'MatchDetail',
    'BiasAudit',
    'ApiLog',
    'Invitation',
    'PasswordReset'
]