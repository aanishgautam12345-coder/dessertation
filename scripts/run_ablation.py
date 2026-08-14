"""Ablation study for JobMatch recommendation system.

Tests the contribution of each scoring component by:
1. Retrieving candidates via semantic search (same for all configs)
2. Re-scoring candidates with different weight configurations
3. Re-ranking and evaluating

Configs tested:
- Full: Default weights (semantic=0.25, skills=0.25, location=0.15, salary=0.15, experience=0.10, job_type=0.05, recency=0.05)
- No semantic: semantic=0, others unchanged
- No skills: skills=0, others unchanged
- No location: location=0, others unchanged
- No salary: salary=0, others unchanged
- No experience: experience=0, others unchanged
- Semantic only: Only semantic scoring (semantic=1.0)
- Metadata only: No semantic (semantic=0), only metadata scoring

Usage:
    python -m scripts.run_ablation
    python -m scripts.run_ablation --config Full,No semantic,No skills
"""

import sys
import os
import json
import csv
import time
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import *  # noqa: F401,F403
from app.models.user import UserProfile
from app.models.job import Job, JobSkill
from app.services.search import semantic_search
from app.services.recommendation import compute_match_score
from app.services.embedding import generate_embedding, build_profile_text
from app.services.scoring_config import ScoringWeights
from app.evaluation.metrics import evaluate_ranking


LABELS_FILE = Path(__file__).parent / "eval_labels.json"
RESULTS_DIR = Path(__file__).parent.parent / "data" / "results"


# All 25 queries from evaluation dataset
QUERIES = [
    "remote python developer",
    "senior data scientist machine learning",
    "HR generalist with payroll experience",
    "entry level marketing no experience",
    "backend engineer with cloud experience",
    "junior software developer",
    "customer support representative remote",
    "finance analyst with excel skills",
    "devops engineer kubernetes",
    "product manager fintech",
    "ux designer mobile apps",
    "cybersecurity analyst",
    "nurse registered",
    "graphic designer creative agency",
    "project manager construction",
    "data analyst python sql",
    "sales manager b2b saas",
    "content writer tech blog",
    "mechanical engineer automotive",
    "legal solicitor corporate law",
    "warehouse operative distribution",
    "cloud architect azure",
    "pharmacist hospital",
    "frontend developer react typescript",
    "supply chain manager logistics",
]

# User profiles for each query (from eval_labels.json)
PROFILES = {
    "remote python developer": {
        "headline": "Senior Python Developer",
        "skills": ["python", "django", "postgresql", "rest apis", "docker"],
        "experience_level": "senior",
        "preferred_locations": ["remote"],
        "min_salary": 60000,
        "salary_currency": "USD",
        "career_interests": "Backend development, API design, cloud infrastructure"
    },
    "senior data scientist machine learning": {
        "headline": "Data Scientist with ML Expertise",
        "skills": ["python", "tensorflow", "pytorch", "machine learning", "sql", "pandas"],
        "experience_level": "senior",
        "preferred_locations": ["London", "remote"],
        "min_salary": 75000,
        "salary_currency": "GBP",
        "career_interests": "Machine learning, deep learning, NLP, computer vision"
    },
    "HR generalist with payroll experience": {
        "headline": "HR Professional",
        "skills": ["human resources", "payroll", "employee relations", "recruitment", "compliance"],
        "experience_level": "mid",
        "preferred_locations": ["Manchester", "Birmingham"],
        "min_salary": 35000,
        "salary_currency": "GBP",
        "career_interests": "Employee engagement, talent acquisition, organizational development"
    },
    "entry level marketing no experience": {
        "headline": "Marketing Graduate",
        "skills": ["social media", "content writing", "google analytics", "canva"],
        "experience_level": "junior",
        "preferred_locations": ["London", "Manchester"],
        "min_salary": 22000,
        "salary_currency": "GBP",
        "career_interests": "Digital marketing, brand management, social media marketing"
    },
    "backend engineer with cloud experience": {
        "headline": "Backend Engineer",
        "skills": ["java", "spring boot", "aws", "kubernetes", "postgresql", "microservices"],
        "experience_level": "senior",
        "preferred_locations": ["remote", "London"],
        "min_salary": 70000,
        "salary_currency": "GBP",
        "career_interests": "Cloud architecture, distributed systems, DevOps"
    },
    "junior software developer": {
        "headline": "Computer Science Graduate",
        "skills": ["javascript", "react", "node.js", "html", "css", "git"],
        "experience_level": "junior",
        "preferred_locations": ["London", "Bristol"],
        "min_salary": 25000,
        "salary_currency": "GBP",
        "career_interests": "Full-stack web development, user interfaces"
    },
    "customer support representative remote": {
        "headline": "Customer Service Professional",
        "skills": ["customer service", "communication", "problem solving", "crm", "zendesk"],
        "experience_level": "mid",
        "preferred_locations": ["remote"],
        "min_salary": 28000,
        "salary_currency": "GBP",
        "career_interests": "Customer success, team leadership"
    },
    "finance analyst with excel skills": {
        "headline": "Financial Analyst",
        "skills": ["excel", "financial modeling", "sql", "power bi", "accounting", "forecasting"],
        "experience_level": "mid",
        "preferred_locations": ["London", "Edinburgh"],
        "min_salary": 45000,
        "salary_currency": "GBP",
        "career_interests": "Corporate finance, investment analysis, financial planning"
    },
    "devops engineer kubernetes": {
        "headline": "DevOps Engineer",
        "skills": ["kubernetes", "docker", "terraform", "aws", "jenkins", "linux", "python"],
        "experience_level": "senior",
        "preferred_locations": ["remote"],
        "min_salary": 75000,
        "salary_currency": "GBP",
        "career_interests": "Infrastructure automation, cloud native, site reliability"
    },
    "product manager fintech": {
        "headline": "Product Manager",
        "skills": ["product management", "agile", "user research", "data analysis", "stakeholder management"],
        "experience_level": "senior",
        "preferred_locations": ["London"],
        "min_salary": 80000,
        "salary_currency": "GBP",
        "career_interests": "Fintech products, digital payments, banking innovation"
    },
    "ux designer mobile apps": {
        "headline": "UX/UI Designer",
        "skills": ["figma", "sketch", "user research", "wireframing", "prototyping", "mobile design"],
        "experience_level": "mid",
        "preferred_locations": ["London", "Manchester"],
        "min_salary": 45000,
        "salary_currency": "GBP",
        "career_interests": "Mobile app design, design systems, accessibility"
    },
    "cybersecurity analyst": {
        "headline": "Security Analyst",
        "skills": ["information security", "penetration testing", "siem", "incident response", "compliance"],
        "experience_level": "mid",
        "preferred_locations": ["London", "remote"],
        "min_salary": 55000,
        "salary_currency": "GBP",
        "career_interests": "Threat detection, security operations, vulnerability management"
    },
    "nurse registered": {
        "headline": "Registered Nurse",
        "skills": ["patient care", "medication administration", "clinical assessment", "emr", "bls certified"],
        "experience_level": "mid",
        "preferred_locations": ["Manchester", "Liverpool"],
        "min_salary": 30000,
        "salary_currency": "GBP",
        "career_interests": "Acute care, patient education, clinical research"
    },
    "graphic designer creative agency": {
        "headline": "Graphic Designer",
        "skills": ["adobe photoshop", "illustrator", "indesign", "branding", "typography", "layout design"],
        "experience_level": "mid",
        "preferred_locations": ["London", "Bristol"],
        "min_salary": 35000,
        "salary_currency": "GBP",
        "career_interests": "Brand identity, creative campaigns, visual storytelling"
    },
    "project manager construction": {
        "headline": "Construction Project Manager",
        "skills": ["project management", "autocad", "budget management", "scheduling", "contract negotiation"],
        "experience_level": "senior",
        "preferred_locations": ["Birmingham", "Leeds"],
        "min_salary": 55000,
        "salary_currency": "GBP",
        "career_interests": "Large-scale construction, sustainable building, infrastructure"
    },
    "data analyst python sql": {
        "headline": "Data Analyst",
        "skills": ["python", "sql", "tableau", "excel", "pandas", "statistics"],
        "experience_level": "junior",
        "preferred_locations": ["London", "remote"],
        "min_salary": 35000,
        "salary_currency": "GBP",
        "career_interests": "Business intelligence, data visualization, predictive analytics"
    },
    "sales manager b2b saas": {
        "headline": "B2B Sales Manager",
        "skills": ["sales management", "crm", "lead generation", "negotiation", "saas sales", "team leadership"],
        "experience_level": "senior",
        "preferred_locations": ["London", "Manchester"],
        "min_salary": 65000,
        "salary_currency": "GBP",
        "career_interests": "SaaS growth, enterprise sales, sales operations"
    },
    "content writer tech blog": {
        "headline": "Technical Content Writer",
        "skills": ["technical writing", "seo", "content strategy", "markdown", "wordpress", "research"],
        "experience_level": "mid",
        "preferred_locations": ["remote"],
        "min_salary": 32000,
        "salary_currency": "GBP",
        "career_interests": "Developer documentation, technical blogging, knowledge management"
    },
    "mechanical engineer automotive": {
        "headline": "Mechanical Engineer",
        "skills": ["cad", "solidworks", "finite element analysis", "manufacturing", "materials science"],
        "experience_level": "mid",
        "preferred_locations": ["Coventry", "Birmingham"],
        "min_salary": 40000,
        "salary_currency": "GBP",
        "career_interests": "Automotive design, electric vehicles, manufacturing optimization"
    },
    "legal solicitor corporate law": {
        "headline": "Corporate Lawyer",
        "skills": ["corporate law", "contract drafting", "due diligence", "mergers and acquisitions", "compliance"],
        "experience_level": "senior",
        "preferred_locations": ["London"],
        "min_salary": 80000,
        "salary_currency": "GBP",
        "career_interests": "M&A, corporate governance, private equity"
    },
    "warehouse operative distribution": {
        "headline": "Warehouse Worker",
        "skills": ["forklift operation", "inventory management", "picking and packing", "health and safety"],
        "experience_level": "entry",
        "preferred_locations": ["Leeds", "Manchester"],
        "min_salary": 20000,
        "salary_currency": "GBP",
        "career_interests": "Logistics, supply chain operations"
    },
    "cloud architect azure": {
        "headline": "Cloud Architect",
        "skills": ["azure", "cloud architecture", "terraform", "devops", "security", "kubernetes"],
        "experience_level": "senior",
        "preferred_locations": ["remote", "London"],
        "min_salary": 90000,
        "salary_currency": "GBP",
        "career_interests": "Multi-cloud strategy, digital transformation, cloud governance"
    },
    "pharmacist hospital": {
        "headline": "Hospital Pharmacist",
        "skills": ["pharmacy", "clinical pharmacy", "drug safety", "patient counseling", "medicine management"],
        "experience_level": "mid",
        "preferred_locations": ["London", "Manchester"],
        "min_salary": 38000,
        "salary_currency": "GBP",
        "career_interests": "Clinical pharmacy, antimicrobial stewardship, patient safety"
    },
    "frontend developer react typescript": {
        "headline": "Frontend Developer",
        "skills": ["react", "typescript", "javascript", "css", "html", "testing", "graphql"],
        "experience_level": "mid",
        "preferred_locations": ["remote", "London"],
        "min_salary": 50000,
        "salary_currency": "GBP",
        "career_interests": "Web applications, performance optimization, design systems"
    },
    "supply chain manager logistics": {
        "headline": "Supply Chain Manager",
        "skills": ["supply chain management", "logistics", "procurement", "inventory optimization", "erp"],
        "experience_level": "senior",
        "preferred_locations": ["Birmingham", "Manchester"],
        "min_salary": 55000,
        "salary_currency": "GBP",
        "career_interests": "Global logistics, sustainable supply chain, operational efficiency"
    },
}


# Ablation configurations - test contribution of each component
DEFAULT = ScoringWeights(
    semantic=0.25, skills=0.25, location=0.15, salary=0.15,
    experience=0.10, job_type=0.05, recency=0.05, version="default"
)

ABLATION_CONFIGS = {
    "Full system": DEFAULT,
    "No semantic": ScoringWeights(
        semantic=0.0, skills=0.33, location=0.22, salary=0.22,
        experience=0.13, job_type=0.05, recency=0.05, version="no_semantic"
    ),
    "No skills": ScoringWeights(
        semantic=0.33, skills=0.0, location=0.22, salary=0.22,
        experience=0.13, job_type=0.05, recency=0.05, version="no_skills"
    ),
    "No location": ScoringWeights(
        semantic=0.29, skills=0.29, location=0.0, salary=0.17,
        experience=0.12, job_type=0.06, recency=0.07, version="no_location"
    ),
    "No salary": ScoringWeights(
        semantic=0.29, skills=0.29, location=0.18, salary=0.0,
        experience=0.12, job_type=0.06, recency=0.06, version="no_salary"
    ),
    "No experience": ScoringWeights(
        semantic=0.28, skills=0.28, location=0.17, salary=0.17,
        experience=0.0, job_type=0.05, recency=0.05, version="no_experience"
    ),
    "Semantic only": ScoringWeights(
        semantic=1.0, skills=0.0, location=0.0, salary=0.0,
        experience=0.0, job_type=0.0, recency=0.0, version="semantic_only"
    ),
    "Metadata only": ScoringWeights(
        semantic=0.0, skills=0.35, location=0.20, salary=0.20,
        experience=0.15, job_type=0.05, recency=0.05, version="metadata_only"
    ),
}


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
    
    profile_text = build_profile_text(
        headline=profile.headline,
        skills=profile.skills,
        career_interests=profile.career_interests,
        experience_level=profile.experience_level,
    )
    profile.profile_embedding = generate_embedding(profile_text, is_query=True)
    
    return profile


def run_ablation_for_config(
    db,
    config_name: str,
    weights: ScoringWeights,
    labels: dict,
    k: int = 10,
) -> dict:
    """Run evaluation with a specific weight configuration."""
    all_metrics = []
    latencies = []
    
    for query_text in QUERIES:
        profile_data = PROFILES.get(query_text)
        if not profile_data:
            continue
        
        profile = create_test_profile(profile_data)
        
        # Get candidates via semantic search
        start_time = time.time()
        results = semantic_search(db, query=query_text, limit=k * 2)
        latency = (time.time() - start_time) * 1000
        latencies.append(latency)
        
        # Re-score candidates with this config
        scored_results = []
        for job_data in results:
            job_id = job_data.get("id")
            if not job_id:
                continue
            
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                continue
            
            job_skills = [
                js.skill.lower().strip()
                for js in db.query(JobSkill)
                .filter(JobSkill.job_id == job.id)
                .all()
            ]
            
            similarity = job_data.get("similarity", 0.0)
            
            # Compute match score with this config
            breakdown = compute_match_score(
                profile, job, job_skills, similarity,
                profile.preferred_job_types,
                weights=weights
            )
            
            scored_results.append({
                "job_id": job_id,
                "score": breakdown.overall_score,
            })
        
        # Sort by score and take top-k
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        top_results = scored_results[:k]
        
        # Get relevance labels
        relevance = [
            labels.get(f"{query_text}::{r['job_id']}", 0)
            for r in top_results
        ]
        
        # Compute metrics
        metrics = evaluate_ranking(relevance, k=k)
        all_metrics.append(metrics)
    
    # Aggregate metrics
    if all_metrics:
        avg_p = sum(m["precision_at_k"] for m in all_metrics) / len(all_metrics)
        avg_gp = sum(m["graded_precision_at_k"] for m in all_metrics) / len(all_metrics)
        avg_ap = sum(m["average_precision"] for m in all_metrics) / len(all_metrics)
        avg_mrr = sum(m["mrr"] for m in all_metrics) / len(all_metrics)
        avg_ndcg = sum(m["ndcg_at_k"] for m in all_metrics) / len(all_metrics)
        avg_rel = sum(m["num_relevant_found"] for m in all_metrics) / len(all_metrics)
        
        hit_count = sum(1 for m in all_metrics if m["num_relevant_found"] > 0)
        hit_rate = hit_count / len(all_metrics)
        
        return {
            "config": config_name,
            "P@10": round(avg_p, 3),
            "Graded_P@10": round(avg_gp, 3),
            "MAP": round(avg_ap, 3),
            "MRR": round(avg_mrr, 3),
            "NDCG@10": round(avg_ndcg, 3),
            "Hit_Rate": round(hit_rate, 3),
            "Avg_Relevant": round(avg_rel, 2),
            "Avg_Latency_ms": round(sum(latencies) / len(latencies), 1),
        }
    
    return {"config": config_name, "P@10": 0, "MAP": 0, "MRR": 0, "NDCG@10": 0}


def main():
    parser = argparse.ArgumentParser(description="Ablation study for JobMatch")
    parser.add_argument("--config", default="all",
                        help="Comma-separated config names, or 'all'")
    parser.add_argument("--k", type=int, default=10,
                        help="Number of top results to evaluate (default: 10)")
    args = parser.parse_args()
    
    # Load labels
    with open(LABELS_FILE, "r") as f:
        eval_data = json.load(f)
    labels = eval_data.get("relevance_labels", {})
    
    print(f"\n{'='*80}")
    print("  JobMatch - Ablation Study")
    print(f"{'='*80}")
    print(f"  Queries: {len(QUERIES)}")
    print(f"  Labels: {len(labels)}")
    print(f"  Top-K: {args.k}")
    
    db = SessionLocal()
    results = []
    
    try:
        # Determine configs
        if args.config == "all":
            configs = ABLATION_CONFIGS
        else:
            configs = {k: v for k, v in ABLATION_CONFIGS.items()
                      if k in args.config.split(",")}
        
        for config_name, weights in configs.items():
            print(f"\n  Running: {config_name} ...")
            result = run_ablation_for_config(db, config_name, weights, labels, k=args.k)
            results.append(result)
            print(f"    P@10: {result['P@10']:.3f}  MAP: {result['MAP']:.3f}  "
                  f"MRR: {result['MRR']:.3f}  NDCG@10: {result['NDCG@10']:.3f}")
        
        # Print comparison table
        print(f"\n{'='*80}")
        print("  ABLATION STUDY RESULTS")
        print(f"{'='*80}")
        print(f"  {'Config':<20} {'P@10':<8} {'MAP':<8} {'MRR':<8} {'NDCG@10':<10} {'Hit':<8}")
        print(f"  {'-'*62}")
        
        for r in results:
            print(f"  {r['config']:<20} {r['P@10']:<8.3f} {r['MAP']:<8.3f} "
                  f"{r['MRR']:<8.3f} {r['NDCG@10']:<10.3f} {r['Hit_Rate']:<8.3f}")
        
        # Export
        output_dir = RESULTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        
        csv_path = output_dir / "ablation_results.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        
        md_path = output_dir / "ablation_results.md"
        with open(md_path, "w") as f:
            f.write("# JobMatch Ablation Study Results\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Component Contribution Analysis\n\n")
            f.write("| Config | P@10 | MAP | MRR | NDCG@10 | Hit Rate |\n")
            f.write("|--------|------|-----|-----|---------|----------|\n")
            for r in results:
                f.write(f"| {r['config']} | {r['P@10']:.3f} | {r['MAP']:.3f} | "
                        f"{r['MRR']:.3f} | {r['NDCG@10']:.3f} | {r['Hit_Rate']:.3f} |\n")
            f.write("\n## Interpretation\n\n")
            f.write("- **Full vs No semantic:** Contribution of semantic embeddings to scoring\n")
            f.write("- **Full vs No skills:** Contribution of skill matching\n")
            f.write("- **Full vs No location:** Contribution of location matching\n")
            f.write("- **Full vs No salary:** Contribution of salary matching\n")
            f.write("- **Full vs No experience:** Contribution of experience matching\n")
            f.write("- **Semantic only:** Performance using only semantic similarity\n")
            f.write("- **Metadata only:** Performance using only metadata (no semantic)\n")
        
        print(f"\n  Exported to:")
        print(f"    {csv_path}")
        print(f"    {md_path}")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
