"""
Bias Detection and Fairness Models

This module defines models for tracking bias detection, auditing, and fairness metrics
in the AI recruitment system.
"""

import json
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import db


class BiasAudit(db.Model):
    """
    Stores records of bias detection in candidate processing

    Attributes:
        id (int): Primary key
        candidate_id (int): Foreign key to candidate
        timestamp (datetime): When the audit occurred
        findings (JSON): Detected bias issues (serialized)
        prompt_bias (JSON): Bias detected in prompts used (serialized)
        prompt_used (str): The actual prompt used for processing
        mitigation_applied (bool): Whether bias mitigation was applied
        mitigation_actions (JSON): Actions taken to mitigate bias (serialized)
    """

    __tablename__ = "bias_audits"

    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    findings = Column(Text)  # JSON string of bias findings
    prompt_bias = Column(Text)  # JSON string of prompt bias analysis
    prompt_used = Column(Text)  # The actual prompt used
    mitigation_applied = Column(Boolean, default=False)
    mitigation_actions = Column(Text)  # JSON string of mitigation actions

    # Relationships
    candidate = relationship("Candidate", backref="bias_audits")

    @property
    def has_bias(self):
        """Check if any bias was detected"""
        try:
            findings = json.loads(self.findings) if self.findings else []
            prompt_bias = json.loads(self.prompt_bias) if self.prompt_bias else []
            return len(findings) > 0 or len(prompt_bias) > 0
        except:
            return False

    @property
    def bias_summary(self):
        """Get a summary of bias findings"""
        try:
            findings = json.loads(self.findings) if self.findings else []
            categories = {}

            for finding in findings:
                finding_type = finding.get("type", "unknown")
                if finding_type not in categories:
                    categories[finding_type] = []

                if finding_type == "protected_attribute":
                    categories[finding_type].append(finding.get("attribute", "unknown"))
                elif finding_type == "biased_language":
                    categories[finding_type].append(finding.get("term", "unknown"))

            return categories
        except:
            return {"error": "Could not parse findings"}

    def __repr__(self):
        return f"<BiasAudit {self.id} for candidate {self.candidate_id}>"


class JobBiasAudit(db.Model):
    """
    Stores records of bias detection in job descriptions

    Attributes:
        id (int): Primary key
        job_id (int): Foreign key to job
        timestamp (datetime): When the audit occurred
        bias_terms (JSON): Biased terms detected (serialized)
        biased_requirements (JSON): Potentially biased requirements (serialized)
        bias_score (float): Overall bias score (0.0-1.0)
        recommendations (JSON): Recommendations for reducing bias (serialized)
        debiased_text (Text): Auto-generated debiased version of text
        changes_made (JSON): List of changes made in debiasing (serialized)
    """

    __tablename__ = "job_bias_audits"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    bias_terms = Column(Text)  # JSON string of bias terms found
    biased_requirements = Column(Text)  # JSON string of biased requirements
    bias_score = Column(Float, default=0.0)  # 0.0 (no bias) to 1.0 (high bias)
    recommendations = Column(Text)  # JSON string of recommendations
    debiased_text = Column(Text)  # Auto-generated debiased text
    changes_made = Column(Text)  # JSON string of changes made

    # Relationships
    job = relationship("Job", backref="bias_audits")

    @property
    def has_bias(self):
        """Check if any significant bias was detected"""
        return self.bias_score >= 0.3

    @property
    def bias_level(self):
        """Get a human-readable bias level"""
        if self.bias_score < 0.3:
            return "Low"
        elif self.bias_score < 0.6:
            return "Medium"
        else:
            return "High"

    def __repr__(self):
        return f"<JobBiasAudit {self.id} for job {self.job_id}>"


class FairnessMetric(db.Model):
    """
    Stores system-wide fairness metrics over time

    Attributes:
        id (int): Primary key
        timestamp (datetime): When metrics were calculated
        metric_type (str): Type of metric (system, candidate, job)
        metric_data (JSON): The actual metrics (serialized)
    """

    __tablename__ = "fairness_metrics"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    metric_type = Column(String(50), nullable=False)  # 'system', 'candidate', 'job', etc.
    metric_data = Column(Text)  # JSON string of metrics

    def __repr__(self):
        return f"<FairnessMetric {self.id} ({self.metric_type})>"


class BiasPromptTemplate(db.Model):
    """
    Stores versioned prompt templates with bias evaluation

    Attributes:
        id (int): Primary key
        name (str): Template name (e.g., 'resume_parse')
        version (str): Version identifier (e.g., 'v1')
        template_text (str): The prompt template
        description (str): Description of the template
        bias_evaluated (bool): Whether bias has been evaluated
        bias_score (float): Calculated bias score (0.0-1.0)
        is_active (bool): Whether this is the active version
        created_at (datetime): Creation timestamp
        created_by (int): User who created the template
        approved_by (int): User who approved the template
    """

    __tablename__ = "bias_prompt_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    version = Column(String(10), nullable=False)
    template_text = Column(Text, nullable=False)
    description = Column(Text)
    bias_evaluated = Column(Boolean, default=False)
    bias_score = Column(Float, default=0.0)
    bias_findings = Column(Text)  # JSON string of bias findings
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Define unique constraint on name and version
    __table_args__ = (
        db.UniqueConstraint("name", "version", name="uq_prompt_template_name_version"),
    )

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])

    @classmethod
    def get_active_template(cls, name):
        """
        Get the active template for a given prompt name

        Args:
            name: Template name

        Returns:
            BiasPromptTemplate: Active template or None
        """
        return cls.query.filter_by(name=name, is_active=True).order_by(cls.version.desc()).first()

    def __repr__(self):
        return f"<PromptTemplate {self.name} {self.version}>"
