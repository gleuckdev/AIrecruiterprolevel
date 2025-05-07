"""
Status Models for AI Recruiter Pro

This module defines enum classes for various status values used across the application.
"""

import enum


class CandidateStatus(enum.Enum):
    """
    Enum for candidate status options.
    Used for type safety and consistent status values across the application.
    """

    NEW = "new"
    REVIEWING = "reviewing"
    SHORTLISTED = "shortlisted"
    CONTACTED = "contacted"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDREW = "withdrew"
