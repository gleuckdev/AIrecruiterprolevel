"""
Models Package for AI Recruiter Pro

This package contains all database models used in the application,
organized into logical modules.
"""

# Re-export the db instance from base (created in extensions.py)
from .auth import TokenBlocklist
from .base import db
from .bias import BiasAudit, BiasPromptTemplate, FairnessMetric, JobBiasAudit
from .candidate import Candidate, CandidateProcessingHistory, CandidateStatusHistory

# Import from the unified feature flags module to avoid conflicts
from .feature_flag_unified import UnifiedFeatureFlag as FeatureFlag
from .feature_flag_unified import UnifiedFeatureFlagOverride as FeatureFlagOverride
from .feature_flag_unified import UnifiedFeatureFlagStat as FeatureFlagStat
from .invitation import Invitation
from .job import Company, Department, Job
from .match import JobCandidateMatch, MatchHistory
from .matching import CandidateJobMatch
from .rating import (
    CandidateRating,
    FlaggedPrompt,
    PromptAudit,
    PromptTemplate,
    RatingCriterion,
    RatingScale,
)
from .recruiter import Recruiter
from .role import Role, user_roles
from .session import Session

# Import models that were moved to dedicated modules
from .shared import CandidateSkill, JobSkill, Skill
from .sharing import CandidateSharing, JobSharing
from .status import CandidateStatus

# Import our core model objects
from .user import RecruiterSharing, User

# For external use, we'll initialize an adapter module
RecruiterAdapter = None  # Will be populated later

RevokedToken = None
JobToken = None

# For migration support
__all__ = [
    # Bias detection models
    "BiasAudit",
    "BiasPromptTemplate",
    # Core model schemas
    "Candidate",
    "CandidateJobMatch",
    "CandidateProcessingHistory",
    "CandidateRating",
    "CandidateSharing",
    # Models moved to dedicated modules
    "CandidateSkill",
    "CandidateStatus",
    "CandidateStatusHistory",
    "Company",
    "Department",
    "FairnessMetric",
    # Feature flag models
    "FeatureFlag",
    "FeatureFlagOverride",
    "FeatureFlagStat",
    "FlaggedPrompt",
    "Invitation",
    "Job",
    "JobBiasAudit",
    "JobCandidateMatch",
    # Sharing models
    "JobSharing",
    "JobSkill",
    "JobToken",
    "MatchHistory",
    "PromptAudit",
    "PromptTemplate",
    "RatingCriterion",
    "RatingScale",
    # Legacy model names for compatibility
    "Recruiter",
    "RecruiterSharing",
    "RevokedToken",
    "Role",
    "Session",
    "Skill",
    "TokenBlocklist",
    "User",
    # Core database models
    "db",
    "user_roles",
]
