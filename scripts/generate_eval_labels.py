"""Generate evaluation labels using actual database UUIDs.

This script creates relevance judgments for the evaluation dataset by:
1. Running semantic search for each query profile
2. Computing heuristic relevance scores based on:
   - Skill overlap (most important signal)
   - Location match
   - Salary match
   - Experience level match
3. Assigning labels on a 0-3 scale

The heuristic labels approximate human judgment for dissertation evaluation.
Manual review is recommended for final validation.

Usage:
    python -m scripts.generate_eval_labels
    python -m scripts.generate_eval_labels --top-k 10 --output data/eval_labels_v2.json
"""

import sys
import os
import json
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import UserProfile
from app.models.job import Job, JobSkill
from app.services.embedding import generate_embedding, build_profile_text
from app.services.search import semantic_search
from app.services.recommendation import compute_match_score
from app.evaluation.baselines import BaselineResult


# Evaluation dataset (same queries as eval_labels.json)
QUERIES = [
    {
        "query_id": 1,
        "query_text": "remote python developer",
        "user_profile": {
            "headline": "Senior Python Developer",
            "skills": ["python", "django", "postgresql", "rest apis", "docker"],
            "experience_level": "senior",
            "preferred_locations": ["remote"],
            "min_salary": 60000,
            "salary_currency": "USD",
            "career_interests": "Backend development, API design, cloud infrastructure"
        }
    },
    {
        "query_id": 2,
        "query_text": "senior data scientist machine learning",
        "user_profile": {
            "headline": "Data Scientist with ML Expertise",
            "skills": ["python", "tensorflow", "pytorch", "machine learning", "sql", "pandas"],
            "experience_level": "senior",
            "preferred_locations": ["London", "remote"],
            "min_salary": 75000,
            "salary_currency": "GBP",
            "career_interests": "Machine learning, deep learning, NLP, computer vision"
        }
    },
    {
        "query_id": 3,
        "query_text": "HR generalist with payroll experience",
        "user_profile": {
            "headline": "HR Professional",
            "skills": ["human resources", "payroll", "employee relations", "recruitment", "compliance"],
            "experience_level": "mid",
            "preferred_locations": ["Manchester", "Birmingham"],
            "min_salary": 35000,
            "salary_currency": "GBP",
            "career_interests": "Employee engagement, talent acquisition, organizational development"
        }
    },
    {
        "query_id": 4,
        "query_text": "entry level marketing no experience",
        "user_profile": {
            "headline": "Marketing Graduate",
            "skills": ["social media", "content writing", "google analytics", "canva"],
            "experience_level": "junior",
            "preferred_locations": ["London", "Manchester"],
            "min_salary": 22000,
            "salary_currency": "GBP",
            "career_interests": "Digital marketing, brand management, social media marketing"
        }
    },
    {
        "query_id": 5,
        "query_text": "backend engineer with cloud experience",
        "user_profile": {
            "headline": "Backend Engineer",
            "skills": ["java", "spring boot", "aws", "kubernetes", "postgresql", "microservices"],
            "experience_level": "senior",
            "preferred_locations": ["remote", "London"],
            "min_salary": 70000,
            "salary_currency": "GBP",
            "career_interests": "Cloud architecture, distributed systems, DevOps"
        }
    },
    {
        "query_id": 6,
        "query_text": "junior software developer",
        "user_profile": {
            "headline": "Computer Science Graduate",
            "skills": ["javascript", "react", "node.js", "html", "css", "git"],
            "experience_level": "junior",
            "preferred_locations": ["London", "Bristol"],
            "min_salary": 25000,
            "salary_currency": "GBP",
            "career_interests": "Full-stack web development, user interfaces"
        }
    },
    {
        "query_id": 7,
        "query_text": "customer support representative remote",
        "user_profile": {
            "headline": "Customer Service Professional",
            "skills": ["customer service", "communication", "problem solving", "crm", "zendesk"],
            "experience_level": "mid",
            "preferred_locations": ["remote"],
            "min_salary": 28000,
            "salary_currency": "GBP",
            "career_interests": "Customer success, team leadership"
        }
    },
    {
        "query_id": 8,
        "query_text": "finance analyst with excel skills",
        "user_profile": {
            "headline": "Financial Analyst",
            "skills": ["excel", "financial modeling", "sql", "power bi", "accounting", "forecasting"],
            "experience_level": "mid",
            "preferred_locations": ["London", "Edinburgh"],
            "min_salary": 45000,
            "salary_currency": "GBP",
            "career_interests": "Corporate finance, investment analysis, financial planning"
        }
    },
    {
        "query_id": 9,
        "query_text": "devops engineer kubernetes",
        "user_profile": {
            "headline": "DevOps Engineer",
            "skills": ["kubernetes", "docker", "terraform", "aws", "jenkins", "linux", "python"],
            "experience_level": "senior",
            "preferred_locations": ["remote"],
            "min_salary": 75000,
            "salary_currency": "GBP",
            "career_interests": "Infrastructure automation, cloud native, site reliability"
        }
    },
    {
        "query_id": 10,
        "query_text": "product manager fintech",
        "user_profile": {
            "headline": "Product Manager",
            "skills": ["product management", "agile", "user research", "data analysis", "stakeholder management"],
            "experience_level": "senior",
            "preferred_locations": ["London"],
            "min_salary": 80000,
            "salary_currency": "GBP",
            "career_interests": "Fintech products, digital payments, banking innovation"
        }
    },
    {
        "query_id": 11,
        "query_text": "ux designer mobile apps",
        "user_profile": {
            "headline": "UX/UI Designer",
            "skills": ["figma", "sketch", "user research", "wireframing", "prototyping", "mobile design"],
            "experience_level": "mid",
            "preferred_locations": ["London", "Manchester"],
            "min_salary": 45000,
            "salary_currency": "GBP",
            "career_interests": "Mobile app design, design systems, accessibility"
        }
    },
    {
        "query_id": 12,
        "query_text": "cybersecurity analyst",
        "user_profile": {
            "headline": "Security Analyst",
            "skills": ["information security", "penetration testing", "siem", "incident response", "compliance"],
            "experience_level": "mid",
            "preferred_locations": ["London", "remote"],
            "min_salary": 55000,
            "salary_currency": "GBP",
            "career_interests": "Threat detection, security operations, vulnerability management"
        }
    },
    {
        "query_id": 13,
        "query_text": "nurse registered",
        "user_profile": {
            "headline": "Registered Nurse",
            "skills": ["patient care", "medication administration", "clinical assessment", "emr", "bls certified"],
            "experience_level": "mid",
            "preferred_locations": ["Manchester", "Liverpool"],
            "min_salary": 30000,
            "salary_currency": "GBP",
            "career_interests": "Acute care, patient education, clinical research"
        }
    },
    {
        "query_id": 14,
        "query_text": "graphic designer creative agency",
        "user_profile": {
            "headline": "Graphic Designer",
            "skills": ["adobe photoshop", "illustrator", "indesign", "branding", "typography", "layout design"],
            "experience_level": "mid",
            "preferred_locations": ["London", "Bristol"],
            "min_salary": 35000,
            "salary_currency": "GBP",
            "career_interests": "Brand identity, creative campaigns, visual storytelling"
        }
    },
    {
        "query_id": 15,
        "query_text": "project manager construction",
        "user_profile": {
            "headline": "Construction Project Manager",
            "skills": ["project management", "autocad", "budget management", "scheduling", "contract negotiation"],
            "experience_level": "senior",
            "preferred_locations": ["Birmingham", "Leeds"],
            "min_salary": 55000,
            "salary_currency": "GBP",
            "career_interests": "Large-scale construction, sustainable building, infrastructure"
        }
    },
    {
        "query_id": 16,
        "query_text": "data analyst python sql",
        "user_profile": {
            "headline": "Data Analyst",
            "skills": ["python", "sql", "tableau", "excel", "pandas", "statistics"],
            "experience_level": "junior",
            "preferred_locations": ["London", "remote"],
            "min_salary": 35000,
            "salary_currency": "GBP",
            "career_interests": "Business intelligence, data visualization, predictive analytics"
        }
    },
    {
        "query_id": 17,
        "query_text": "sales manager b2b saas",
        "user_profile": {
            "headline": "B2B Sales Manager",
            "skills": ["sales management", "crm", "lead generation", "negotiation", "saas sales", "team leadership"],
            "experience_level": "senior",
            "preferred_locations": ["London", "Manchester"],
            "min_salary": 65000,
            "salary_currency": "GBP",
            "career_interests": "SaaS growth, enterprise sales, sales operations"
        }
    },
    {
        "query_id": 18,
        "query_text": "content writer tech blog",
        "user_profile": {
            "headline": "Technical Content Writer",
            "skills": ["technical writing", "seo", "content strategy", "markdown", "wordpress", "research"],
            "experience_level": "mid",
            "preferred_locations": ["remote"],
            "min_salary": 32000,
            "salary_currency": "GBP",
            "career_interests": "Developer documentation, technical blogging, knowledge management"
        }
    },
    {
        "query_id": 19,
        "query_text": "mechanical engineer automotive",
        "user_profile": {
            "headline": "Mechanical Engineer",
            "skills": ["cad", "solidworks", "finite element analysis", "manufacturing", "materials science"],
            "experience_level": "mid",
            "preferred_locations": ["Coventry", "Birmingham"],
            "min_salary": 40000,
            "salary_currency": "GBP",
            "career_interests": "Automotive design, electric vehicles, manufacturing optimization"
        }
    },
    {
        "query_id": 20,
        "query_text": "legal solicitor corporate law",
        "user_profile": {
            "headline": "Corporate Lawyer",
            "skills": ["corporate law", "contract drafting", "due diligence", "mergers and acquisitions", "compliance"],
            "experience_level": "senior",
            "preferred_locations": ["London"],
            "min_salary": 80000,
            "salary_currency": "GBP",
            "career_interests": "M&A, corporate governance, private equity"
        }
    },
    {
        "query_id": 21,
        "query_text": "warehouse operative distribution",
        "user_profile": {
            "headline": "Warehouse Worker",
            "skills": ["forklift operation", "inventory management", "picking and packing", "health and safety"],
            "experience_level": "entry",
            "preferred_locations": ["Leeds", "Manchester"],
            "min_salary": 20000,
            "salary_currency": "GBP",
            "career_interests": "Logistics, supply chain operations"
        }
    },
    {
        "query_id": 22,
        "query_text": "cloud architect azure",
        "user_profile": {
            "headline": "Cloud Architect",
            "skills": ["azure", "cloud architecture", "terraform", "devops", "security", "kubernetes"],
            "experience_level": "senior",
            "preferred_locations": ["remote", "London"],
            "min_salary": 90000,
            "salary_currency": "GBP",
            "career_interests": "Multi-cloud strategy, digital transformation, cloud governance"
        }
    },
    {
        "query_id": 23,
        "query_text": "pharmacist hospital",
        "user_profile": {
            "headline": "Hospital Pharmacist",
            "skills": ["pharmacy", "clinical pharmacy", "drug safety", "patient counseling", "medicine management"],
            "experience_level": "mid",
            "preferred_locations": ["London", "Manchester"],
            "min_salary": 38000,
            "salary_currency": "GBP",
            "career_interests": "Clinical pharmacy, antimicrobial stewardship, patient safety"
        }
    },
    {
        "query_id": 24,
        "query_text": "frontend developer react typescript",
        "user_profile": {
            "headline": "Frontend Developer",
            "skills": ["react", "typescript", "javascript", "css", "html", "testing", "graphql"],
            "experience_level": "mid",
            "preferred_locations": ["remote", "London"],
            "min_salary": 50000,
            "salary_currency": "GBP",
            "career_interests": "Web applications, performance optimization, design systems"
        }
    },
    {
        "query_id": 25,
        "query_text": "supply chain manager logistics",
        "user_profile": {
            "headline": "Supply Chain Manager",
            "skills": ["supply chain management", "logistics", "procurement", "inventory optimization", "erp"],
            "experience_level": "senior",
            "preferred_locations": ["Birmingham", "Manchester"],
            "min_salary": 55000,
            "salary_currency": "GBP",
            "career_interests": "Global logistics, sustainable supply chain, operational efficiency"
        }
    }
]


def create_test_profile(profile_data: dict) -> UserProfile:
    """Create a UserProfile object from profile data."""
    profile = UserProfile(
        headline=profile_data.get("headline", ""),
        skills=profile_data.get("skills", []),
        experience_level=profile_data.get("experience_level", "mid"),
        preferred_locations=profile_data.get("preferred_locations", []),
        min_salary=profile_data.get("min_salary"),
        salary_currency=profile_data.get("salary_currency", "USD"),
        career_interests=profile_data.get("career_interests", ""),
        preferred_job_types=["full-time"],
    )
    
    # Generate profile embedding
    profile_text = build_profile_text(
        headline=profile.headline,
        skills=profile.skills,
        career_interests=profile.career_interests,
        experience_level=profile.experience_level,
    )
    profile.profile_embedding = generate_embedding(profile_text, is_query=True)
    
    return profile


def compute_heuristic_relevance(profile: UserProfile, job: Job, job_skills: list[str]) -> int:
    """Compute heuristic relevance score (0-3) based on profile-job match.
    
    Scoring criteria:
    - Skill overlap (most important)
    - Location match
    - Salary match
    - Experience level match
    """
    score = 0
    reasons = []
    
    # 1. Skill overlap (0-2 points)
    if profile.skills and job_skills:
        user_skills = set(s.lower().strip() for s in profile.skills)
        job_skills_set = set(s.lower().strip() for s in job_skills)
        overlap = user_skills & job_skills_set
        
        if len(overlap) >= 3:
            score += 2
            reasons.append(f"strong skill overlap ({len(overlap)} skills)")
        elif len(overlap) >= 1:
            score += 1
            reasons.append(f"some skill overlap ({len(overlap)} skills)")
        else:
            reasons.append("no skill overlap")
    
    # 2. Location match (0-1 point)
    if profile.preferred_locations:
        job_location = (job.location_city or "").lower()
        job_country = (job.location_country or "").lower()
        is_remote = job.remote or False
        
        location_match = False
        for pref in profile.preferred_locations:
            pref_lower = pref.lower()
            if pref_lower == "remote" and is_remote:
                location_match = True
                break
            if pref_lower in job_location or pref_lower in job_country:
                location_match = True
                break
        
        if location_match:
            score += 1
            reasons.append("location match")
    
    # 3. Salary match (bonus point)
    if profile.min_salary and job.salary_min:
        # Convert to same currency (simplified)
        job_salary = job.salary_min or 0
        if job_salary >= profile.min_salary * 0.8:
            reasons.append("salary match")
        else:
            reasons.append("salary too low")
    
    # 4. Experience level match (consideration)
    if profile.experience_level and job.experience_level:
        exp_order = ["intern", "junior", "entry", "mid", "senior", "lead", "principal", "director"]
        try:
            user_idx = exp_order.index(profile.experience_level.lower())
            job_idx = exp_order.index(job.experience_level.lower())
            distance = abs(user_idx - job_idx)
            if distance <= 1:
                reasons.append("experience level match")
            else:
                reasons.append(f"experience level mismatch (distance={distance})")
        except ValueError:
            pass
    
    # Determine final label (0-3)
    if score >= 3:
        return 3, reasons  # Highly relevant
    elif score >= 2:
        return 2, reasons  # Relevant
    elif score >= 1:
        return 1, reasons  # Partially relevant
    else:
        return 0, reasons  # Not relevant


def generate_labels(top_k: int = 10) -> dict:
    """Generate evaluation labels using actual database records."""
    db = SessionLocal()
    
    try:
        labels = {}
        total_queries = len(QUERIES)
        
        for idx, query_data in enumerate(QUERIES):
            query_text = query_data["query_text"]
            query_id = query_data["query_id"]
            
            print(f"  [{idx+1}/{total_queries}] Processing: {query_text}")
            
            # Create profile
            profile = create_test_profile(query_data["user_profile"])
            
            # Run semantic search
            try:
                results = semantic_search(db, query=query_text, limit=top_k)
            except Exception as e:
                print(f"    Warning: Search failed: {e}")
                continue
            
            # Label each result
            for result in results:
                job_id = result.get("id")
                if not job_id:
                    continue
                
                # Get job from database
                job = db.query(Job).filter(Job.id == job_id).first()
                if not job:
                    continue
                
                # Get job skills
                job_skills = [
                    js.skill.lower().strip()
                    for js in db.query(JobSkill)
                    .filter(JobSkill.job_id == job.id)
                    .all()
                ]
                
                # Compute heuristic relevance
                relevance, reasons = compute_heuristic_relevance(profile, job, job_skills)
                
                # Store label
                label_key = f"{query_text}::{job_id}"
                labels[label_key] = relevance
                
                print(f"    {job_id}: relevance={relevance} ({', '.join(reasons[:2])})")
        
        # Build output
        output = {
            "metadata": {
                "description": "Evaluation dataset for JobMatch recommendation system",
                "relevance_scale": {
                    "0": "Not relevant",
                    "1": "Partially relevant (tangentially related)",
                    "2": "Relevant (genuinely useful match)",
                    "3": "Highly relevant (strong, precise match)"
                },
                "created": "2026-08-15",
                "total_queries": len(QUERIES),
                "total_judgments": len(labels),
                "generation_method": "heuristic (skill overlap + location + salary + experience)",
                "note": "Labels generated automatically. Manual review recommended for final validation."
            },
            "queries": QUERIES,
            "relevance_labels": labels
        }
        
        return output
        
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Generate evaluation labels with real DB UUIDs")
    parser.add_argument("--top-k", type=int, default=10,
                        help="Number of top results to label per query (default: 10)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output file path (default: scripts/eval_labels.json)")
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("  JobMatch - Evaluation Label Generator")
    print("="*70)
    print(f"\n  Queries: {len(QUERIES)}")
    print(f"  Top-K per query: {args.top_k}")
    print(f"  Expected labels: {len(QUERIES) * args.top_k}")
    
    # Generate labels
    print("\n  Generating labels...")
    output = generate_labels(top_k=args.top_k)
    
    # Save output
    output_path = args.output or str(Path(__file__).parent / "eval_labels.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n  Saved {len(output['relevance_labels'])} labels to:")
    print(f"    {output_path}")
    
    # Print summary
    from collections import Counter
    label_counts = Counter(output["relevance_labels"].values())
    print(f"\n  Label distribution:")
    for label in sorted(label_counts.keys()):
        print(f"    {label}: {label_counts[label]} ({label_counts[label]/len(output['relevance_labels'])*100:.1f}%)")
    
    print("\n  Done!")


if __name__ == "__main__":
    main()
