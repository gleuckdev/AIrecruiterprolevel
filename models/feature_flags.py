"""
Feature Flag Models for AI Recruiter Pro

IMPORTANT: This module is DEPRECATED. Import from feature_flag_unified.py instead.
This module now simply imports from the unified model to avoid duplicate definitions.
"""

# Re-export the unified models with their original names for backwards compatibility
from .feature_flag_unified import UnifiedFeatureFlag as FeatureFlag
from .feature_flag_unified import UnifiedFeatureFlagOverride as FeatureFlagOverride
from .feature_flag_unified import UnifiedFeatureFlagStat as FeatureFlagStat

# Preserve top-level imports to avoid breaking code that imports from here
__all__ = ["FeatureFlag", "FeatureFlagOverride", "FeatureFlagStat"]
