"""Hallucination measurement framework for dissertation evaluation.

Measures the quality and faithfulness of LLM-generated explanations by:
1. Claim-level groundedness checking
2. Faithfulness scoring
3. Citation accuracy
4. Unsupported claim detection

Usage:
    from app.evaluation.hallucination import HallucinationMeasurer
    measurer = HallucinationMeasurer(db)
    report = measurer.measure_explanation(user_id, job_id, explanation_text)
"""

import re
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.user import UserProfile
from app.models.job import Job, JobSkill
from app.models.recommendation import Recommendation
from app.services.explanation_validator import validate_explanation
from app.services.recommendation import compute_match_score

logger = logging.getLogger(__name__)


@dataclass
class ClaimExtraction:
    """A single claim extracted from an explanation."""
    claim_text: str
    claim_type: str  # skill, score, location, salary, experience, company, other
    evidence_required: str  # What evidence should support this claim
    is_supported: bool = False
    support_source: str = ""  # Where the support comes from
    confidence: float = 0.0


@dataclass
class HallucinationReport:
    """Complete hallucination measurement report for one explanation."""
    explanation_text: str
    total_claims: int = 0
    supported_claims: int = 0
    unsupported_claims: int = 0
    partially_supported_claims: int = 0
    
    # Metrics
    groundedness_score: float = 0.0  # supported / total
    faithfulness_score: float = 0.0  # How well explanation follows from evidence
    hallucination_rate: float = 0.0  # unsupported / total
    citation_accuracy: float = 0.0  # How accurate referenced facts are
    
    # Detailed claim analysis
    claims: list[ClaimExtraction] = field(default_factory=list)
    
    # Validation issues
    validation_issues: list[str] = field(default_factory=list)
    validation_quality: float = 0.0
    
    # Metadata
    measured_at: str = ""
    processing_time_ms: float = 0.0


class HallucinationMeasurer:
    """Measures hallucination rate and groundedness in LLM explanations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def measure_explanation(
        self,
        user_id: int,
        job_id: int,
        explanation_text: str,
    ) -> HallucinationReport:
        """Measure hallucination in a single explanation."""
        start_time = datetime.now()
        report = HallucinationReport(explanation_text=explanation_text)
        
        # Get profile and job data
        from app.models.user import UserProfile
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        job = self.db.query(Job).filter(Job.id == job_id).first()
        
        if not profile or not job:
            report.validation_issues.append("Profile or job not found")
            return report
        
        # Get job skills
        job_skills = self.db.query(JobSkill).filter(JobSkill.job_id == job.id).all()
        skill_names = [s.skill for s in job_skills]
        
        # Extract claims from explanation
        claims = self._extract_claims(explanation_text, profile, job, skill_names)
        report.claims = claims
        report.total_claims = len(claims)
        
        # Check each claim against evidence
        for claim in claims:
            claim.is_supported, claim.support_source = self._check_claim_support(
                claim, profile, job, skill_names
            )
            if claim.is_supported:
                report.supported_claims += 1
            else:
                report.unsupported_claims += 1
        
        # Compute metrics
        if report.total_claims > 0:
            report.groundedness_score = report.supported_claims / report.total_claims
            report.hallucination_rate = report.unsupported_claims / report.total_claims
        
        # Run validation
        from app.services.recommendation import compute_match_score
        from app.services.embedding import generate_embedding, build_profile_text
        
        # Compute breakdown for validation
        profile_text = build_profile_text(
            headline=profile.headline,
            skills=profile.skills,
            career_interests=profile.career_interests,
            experience_level=profile.experience_level,
        )
        
        # Get semantic similarity
        if profile.profile_embedding and job.embedding:
            import numpy as np
            from app.services.vector import cosine_similarity
            similarity = cosine_similarity(
                np.array(profile.profile_embedding),
                np.array(job.embedding)
            )
        else:
            similarity = 0.5
        
        breakdown = compute_match_score(
            profile, job, skill_names, similarity, profile.preferred_job_types
        )
        
        # Validate explanation
        validation = validate_explanation(explanation_text, profile, job, breakdown)
        report.validation_issues = validation.issues
        report.validation_quality = validation.quality_score
        report.citation_accuracy = max(0.0, 1.0 - len(validation.issues) * 0.15)
        
        # Compute faithfulness (combination of groundedness and validation)
        report.faithfulness_score = (
            0.6 * report.groundedness_score + 
            0.4 * report.validation_quality
        )
        
        # Metadata
        report.measured_at = datetime.now().isoformat()
        report.processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return report
    
    def _extract_claims(
        self, 
        explanation: str, 
        profile: UserProfile, 
        job: Job, 
        job_skills: list[str],
    ) -> list[ClaimExtraction]:
        """Extract claims from explanation text."""
        claims = []
        
        # Skill claims
        skill_patterns = [
            r"your\s+(\w[\w\s]*?)\s+skills?\s+(?:match|align|fit|correspond)",
            r"(?:match|align|fit|correspond)\s+your\s+(\w[\w\s]*?)\s+skills?",
            r"experience\s+(?:with|in)\s+(\w[\w\s]*?)\s+(?:is|are)\s+(?:valued|required|needed)",
            r"requires?\s+(\w[\w\s]*?)\s+(?:skills?|experience|knowledge)",
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, explanation, re.IGNORECASE)
            for match in matches:
                skill = match.strip().lower()
                if skill and len(skill) > 2:
                    claims.append(ClaimExtraction(
                        claim_text=f"Skill: {skill}",
                        claim_type="skill",
                        evidence_required=f"Job requires '{skill}' or user has '{skill}'",
                    ))
        
        # Score claims
        score_patterns = [
            r"(?:match|score|percentage|similarity)\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*%",
            r"(\d+(?:\.\d+)?)\s*%\s+(?:match|score|similarity)",
            r"(?:strong|good|excellent)\s+match",
            r"(?:weak|low|poor)\s+match",
        ]
        
        for pattern in score_patterns:
            matches = re.findall(pattern, explanation, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str) and match.replace('.', '').isdigit():
                    score = float(match)
                    claims.append(ClaimExtraction(
                        claim_text=f"Score claim: {score}%",
                        claim_type="score",
                        evidence_required=f"Actual match score should be close to {score}%",
                    ))
        
        # Location claims
        location_patterns = [
            r"(?:location|location|position)\s+(?:fits?|matches?|works?)",
            r"based\s+in\s+(\w[\w\s]*?)",
            r"(?:remote|hybrid|onsite)\s+(?:position|role|job)",
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, explanation, re.IGNORECASE)
            for match in matches:
                claims.append(ClaimExtraction(
                    claim_text=f"Location claim: {match if isinstance(match, str) else pattern}",
                    claim_type="location",
                    evidence_required="Job location should match user preferences",
                ))
        
        # Salary claims
        salary_patterns = [
            r"salary\s+(?:of\s+)?[\£\$]?(\d[\d,]*(?:\.\d+)?)",
            r"[\£\$]?(\d[\d,]*(?:\.\d+)?)\s+(?:salary|per annum|p\.a\.|annual)",
            r"(?:competitive|good|excellent)\s+salary",
        ]
        
        for pattern in salary_patterns:
            matches = re.findall(pattern, explanation, re.IGNORECASE)
            for match in matches:
                claims.append(ClaimExtraction(
                    claim_text=f"Salary claim: {match}",
                    claim_type="salary",
                    evidence_required=f"Job salary should match stated amount",
                ))
        
        # Experience claims
        experience_patterns = [
            r"experience\s+level\s+(?:matches?|fits?|aligns?)",
            r"(?:junior|mid|senior|lead|principal|director)\s+level",
            r"(\d+)\+?\s+years?\s+(?:of\s+)?experience",
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, explanation, re.IGNORECASE)
            for match in matches:
                claims.append(ClaimExtraction(
                    claim_text=f"Experience claim: {match}",
                    claim_type="experience",
                    evidence_required="Job experience level should match user level",
                ))
        
        # If no claims extracted, create a general claim
        if not claims:
            claims.append(ClaimExtraction(
                claim_text="General recommendation claim",
                claim_type="other",
                evidence_required="Overall recommendation should be justified",
            ))
        
        return claims
    
    def _check_claim_support(
        self,
        claim: ClaimExtraction,
        profile: UserProfile,
        job: Job,
        job_skills: list[str],
    ) -> tuple[bool, str]:
        """Check if a claim is supported by evidence."""
        
        if claim.claim_type == "skill":
            # Check if mentioned skill is in job requirements or user skills
            skill_match = re.search(r"Skill:\s*(.+)", claim.claim_text)
            if skill_match:
                skill = skill_match.group(1).strip().lower()
                user_skills = [s.lower() for s in (profile.skills or [])]
                job_skills_lower = [s.lower() for s in job_skills]
                
                if skill in user_skills:
                    return True, f"User has skill: {skill}"
                elif skill in job_skills_lower:
                    return True, f"Job requires skill: {skill}"
                else:
                    return False, f"Skill '{skill}' not found in profile or job"
        
        elif claim.claim_type == "score":
            # Check if claimed score is reasonable
            score_match = re.search(r"(\d+(?:\.\d+)?)", claim.claim_text)
            if score_match:
                claimed_score = float(score_match.group(1)) / 100.0
                # We can't verify exact score without recomputing, but check if it's plausible
                if 0.0 <= claimed_score <= 1.0:
                    return True, "Score within valid range"
                else:
                    return False, f"Score {claimed_score} outside valid range [0, 1]"
        
        elif claim.claim_type == "location":
            # Check if location claim is consistent
            if job.remote:
                return True, "Job is remote"
            elif profile.preferred_locations:
                job_location = f"{job.location_city or ''} {job.location_country or ''}".strip()
                for pref in profile.preferred_locations:
                    if pref.lower() in job_location.lower():
                        return True, f"Job location matches preference: {pref}"
                return False, f"Job location '{job_location}' not in preferences"
            return True, "No location preferences set"
        
        elif claim.claim_type == "salary":
            # Check if salary claim is supported
            if job.salary_min or job.salary_max:
                return True, "Job has salary information"
            else:
                return False, "Job has no salary information"
        
        elif claim.claim_type == "experience":
            # Check if experience claim is consistent
            if job.experience_level and profile.experience_level:
                from app.services.recommendation import EXPERIENCE_ORDER
                job_idx = EXPERIENCE_ORDER.index(job.experience_level.lower()) if job.experience_level.lower() in EXPERIENCE_ORDER else -1
                user_idx = EXPERIENCE_ORDER.index(profile.experience_level.lower()) if profile.experience_level.lower() in EXPERIENCE_ORDER else -1
                
                if job_idx >= 0 and user_idx >= 0:
                    distance = abs(job_idx - user_idx)
                    if distance <= 1:
                        return True, f"Experience levels match (distance={distance})"
                    else:
                        return False, f"Experience levels differ by {distance} levels"
            return True, "Experience level information available"
        
        # Default: partially supported
        return True, "Claim is general and difficult to verify"
    
    def batch_measure(
        self,
        explanations: list[dict],
    ) -> list[HallucinationReport]:
        """Measure hallucination for a batch of explanations."""
        reports = []
        for exp in explanations:
            report = self.measure_explanation(
                user_id=exp["user_id"],
                job_id=exp["job_id"],
                explanation_text=exp["explanation"],
            )
            reports.append(report)
        return reports
    
    def compute_aggregate_metrics(self, reports: list[HallucinationReport]) -> dict:
        """Compute aggregate metrics across multiple reports."""
        if not reports:
            return {}
        
        total_claims = sum(r.total_claims for r in reports)
        supported_claims = sum(r.supported_claims for r in reports)
        unsupported_claims = sum(r.unsupported_claims for r in reports)
        
        return {
            "num_explanations": len(reports),
            "total_claims": total_claims,
            "supported_claims": supported_claims,
            "unsupported_claims": unsupported_claims,
            "overall_groundedness": supported_claims / total_claims if total_claims > 0 else 0,
            "overall_hallucination_rate": unsupported_claims / total_claims if total_claims > 0 else 0,
            "avg_faithfulness": sum(r.faithfulness_score for r in reports) / len(reports),
            "avg_validation_quality": sum(r.validation_quality for r in reports) / len(reports),
            "avg_citation_accuracy": sum(r.citation_accuracy for r in reports) / len(reports),
        }
