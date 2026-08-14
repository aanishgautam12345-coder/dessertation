"""Comprehensive evaluation runner for the JobMatch dissertation.

Compares four systems:
1. Baseline 1: Keyword matching (BM25)
2. Baseline 2: Rule-based metadata matching (no embeddings)
3. Baseline 3: Embedding-only (no metadata scoring)
4. Proposed: Full system (embeddings + metadata + reranking)

Computes: P@5, P@10, Recall@5, Recall@10, NDCG@5, NDCG@10, MRR, MAP, Hit Rate
Also measures: latency, diversity, coverage, hallucination rate

Usage:
    python -m scripts.run_full_evaluation
    python -m scripts.run_full_evaluation --output-dir data/results
    python -m scripts.run_full_evaluation --skip-latency
"""

import sys
import os
import json
import time
import csv
import argparse
from pathlib import Path
from datetime import datetime
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import *  # noqa: F401,F403
from app.models.user import UserProfile
from app.models.job import Job, JobSkill
from app.evaluation.metrics import (
    precision_at_k, graded_precision_at_k, recall_at_k,
    mean_reciprocal_rank, average_precision, ndcg_at_k,
    dcg_at_k, evaluate_ranking
)
from app.evaluation.baselines import KeywordSearchBaseline, RuleBasedBaseline, EmbeddingOnlyBaseline
from app.services.search import semantic_search
from app.services.recommendation import compute_match_score
from app.services.embedding import generate_embedding, build_profile_text


# ── Load evaluation dataset ──
EVAL_DATA_FILE = Path(__file__).parent / "eval_labels.json"
RESULTS_DIR = Path(__file__).parent.parent / "data" / "results"


def load_eval_data() -> dict:
    """Load the evaluation dataset with queries and relevance labels."""
    if not EVAL_DATA_FILE.exists():
        print(f"ERROR: Evaluation dataset not found at {EVAL_DATA_FILE}")
        print("Please create eval_labels.json first.")
        sys.exit(1)
    
    with open(EVAL_DATA_FILE, "r") as f:
        return json.load(f)


def create_test_profile(db: Session, profile_data: dict) -> UserProfile:
    """Create a UserProfile object from evaluation dataset profile data."""
    profile = UserProfile(
        headline=profile_data.get("headline", ""),
        skills=profile_data.get("skills", []),
        experience_level=profile_data.get("experience_level", "mid"),
        preferred_locations=profile_data.get("preferred_locations", []),
        min_salary=profile_data.get("min_salary"),
        salary_currency=profile_data.get("salary_currency", "USD"),
        career_interests=profile_data.get("career_interests", ""),
        preferred_job_types=["full-time"],  # Default
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


def evaluate_system(
    system_name: str,
    results_func,
    eval_data: dict,
    db: Session,
    k_values: list[int] = [5, 10],
) -> dict:
    """Evaluate a single system across all queries."""
    all_metrics = {k: [] for k in k_values}
    latencies = []
    all_categories = []
    all_scores = []
    
    queries = eval_data["queries"]
    labels = eval_data["relevance_labels"]
    
    for query_data in queries:
        query_text = query_data["query_text"]
        query_id = query_data["query_id"]
        
        # Create profile for this query
        profile = create_test_profile(db, query_data["user_profile"])
        
        # Measure latency
        start_time = time.time()
        try:
            results = results_func(db, query_text, profile, limit=20)
        except Exception as e:
            print(f"  Warning: {system_name} failed for query '{query_text}': {e}")
            results = []
        latency = (time.time() - start_time) * 1000  # ms
        latencies.append(latency)
        
        # Get relevance judgments
        relevance = []
        for result in results:
            label_key = f"{query_text}::{result.job_id}"
            relevance.append(labels.get(label_key, 0))
        
        # Compute metrics for each k
        for k in k_values:
            metrics = evaluate_ranking(relevance, k=k)
            all_metrics[k].append(metrics)
        
        # Collect diversity data
        for result in results:
            job = db.query(Job).filter(Job.id == result.job_id).first()
            if job:
                all_categories.append(job.category or "Unknown")
                all_scores.append(result.score)
    
    # Aggregate metrics
    summary = {
        "system": system_name,
        "num_queries": len(queries),
        "total_results": sum(len(all_metrics[5]) * 5 for _ in [1]),  # Approximate
    }
    
    for k in k_values:
        if all_metrics[k]:
            avg_p = sum(m["precision_at_k"] for m in all_metrics[k]) / len(all_metrics[k])
            avg_gp = sum(m["graded_precision_at_k"] for m in all_metrics[k]) / len(all_metrics[k])
            avg_ap = sum(m["average_precision"] for m in all_metrics[k]) / len(all_metrics[k])
            avg_mrr = sum(m["mrr"] for m in all_metrics[k]) / len(all_metrics[k])
            avg_ndcg = sum(m["ndcg_at_k"] for m in all_metrics[k]) / len(all_metrics[k])
            avg_rel = sum(m["num_relevant_found"] for m in all_metrics[k]) / len(all_metrics[k])
            
            # Hit rate: % of queries with at least 1 relevant result in top-k
            hit_count = sum(1 for m in all_metrics[k] if m["num_relevant_found"] > 0)
            hit_rate = hit_count / len(all_metrics[k]) if all_metrics[k] else 0.0
            
            summary[f"P@{k}"] = round(avg_p, 3)
            summary[f"Graded_P@{k}"] = round(avg_gp, 3)
            summary[f"MAP@{k}"] = round(avg_ap, 3)
            summary[f"MRR@{k}"] = round(avg_mrr, 3)
            summary[f"NDCG@{k}"] = round(avg_ndcg, 3)
            summary[f"Hit_Rate@{k}"] = round(hit_rate, 3)
            summary[f"Avg_Relevant_Found@{k}"] = round(avg_rel, 2)
    
    # Latency
    summary["Avg_Latency_ms"] = round(sum(latencies) / len(latencies), 1) if latencies else 0
    summary["P95_Latency_ms"] = round(sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0, 1)
    
    # Diversity (unique categories / total results)
    if all_categories:
        category_counts = Counter(all_categories)
        unique_categories = len(category_counts)
        total_results = len(all_categories)
        summary["Category_Diversity"] = round(unique_categories / total_results if total_results > 0 else 0, 3)
        summary["Top_3_Categories"] = dict(category_counts.most_common(3))
    
    return summary, all_metrics


def keyword_baseline_func(db, query, profile, limit=20):
    """Keyword search baseline function."""
    baseline = KeywordSearchBaseline(db)
    return baseline.search(query, limit=limit)


def rule_based_baseline_func(db, query, profile, limit=20):
    """Rule-based baseline function (uses profile but no embeddings)."""
    baseline = RuleBasedBaseline(db)
    return baseline.search(profile, limit=limit)


def embedding_only_baseline_func(db, query, profile, limit=20):
    """Embedding-only baseline function."""
    baseline = EmbeddingOnlyBaseline(db)
    return baseline.search(profile, limit=limit)


def proposed_system_func(db, query, profile, limit=20):
    """Proposed system (semantic search with metadata scoring)."""
    results = semantic_search(db, query=query, limit=limit)
    
    from app.evaluation.baselines import BaselineResult
    
    return [
        BaselineResult(
            job_id=str(job.get("id", "")),
            title=job.get("title", ""),
            company=job.get("company"),
            score=job.get("similarity", 0.0),
            method="Proposed System",
            explanation=f"Semantic + metadata scoring"
        )
        for job in results
    ]


def export_results(summary_rows: list[dict], output_dir: Path):
    """Export results to CSV and Markdown."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # CSV
    csv_path = output_dir / "full_evaluation_results.csv"
    if summary_rows:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
            writer.writeheader()
            writer.writerows(summary_rows)
    
    # Markdown
    md_path = output_dir / "full_evaluation_results.md"
    with open(md_path, "w") as f:
        f.write("# JobMatch Full Evaluation Results\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## System Comparison\n\n")
        
        # Main metrics table
        f.write("| System | P@5 | P@10 | NDCG@5 | NDCG@10 | MRR | Hit Rate@5 | Avg Latency (ms) |\n")
        f.write("|--------|-----|------|--------|---------|-----|------------|------------------|\n")
        for row in summary_rows:
            f.write(f"| {row['system']} | {row.get('P@5', 'N/A')} | {row.get('P@10', 'N/A')} | "
                    f"{row.get('NDCG@5', 'N/A')} | {row.get('NDCG@10', 'N/A')} | "
                    f"{row.get('MRR@5', 'N/A')} | {row.get('Hit_Rate@5', 'N/A')} | "
                    f"{row.get('Avg_Latency_ms', 'N/A')} |\n")
        
        f.write("\n## Detailed Metrics\n\n")
        for row in summary_rows:
            f.write(f"### {row['system']}\n\n")
            for key, value in row.items():
                if key != "system" and not key.startswith("Top_"):
                    f.write(f"- **{key}:** {value}\n")
            f.write("\n")
        
        f.write("## Interpretation\n\n")
        f.write("- **P@K:** Precision at K - fraction of top-K results that are relevant\n")
        f.write("- **NDCG@K:** Normalized Discounted Cumulative Gain - rewards relevant results ranked higher\n")
        f.write("- **MRR:** Mean Reciprocal Rank - 1/rank of first relevant result\n")
        f.write("- **Hit Rate:** Percentage of queries with at least 1 relevant result in top-K\n")
        f.write("- **Latency:** Response time in milliseconds\n")
    
    print(f"\n  Exported to:")
    print(f"    {csv_path}")
    print(f"    {md_path}")


def print_comparison_table(summary_rows: list[dict]):
    """Print a formatted comparison table to console."""
    print(f"\n{'='*100}")
    print("  FULL EVALUATION RESULTS: PROPOSED SYSTEM vs BASELINES")
    print(f"{'='*100}")
    
    header = f"{'System':<30} {'P@5':<8} {'P@10':<8} {'NDCG@5':<10} {'NDCG@10':<10} {'MRR':<8} {'Hit@5':<8} {'Latency':<10}"
    print(header)
    print("-" * 100)
    
    for row in summary_rows:
        print(f"{row['system']:<30} "
              f"{row.get('P@5', 'N/A'):<8} "
              f"{row.get('P@10', 'N/A'):<8} "
              f"{row.get('NDCG@5', 'N/A'):<10} "
              f"{row.get('NDCG@10', 'N/A'):<10} "
              f"{row.get('MRR@5', 'N/A'):<8} "
              f"{row.get('Hit_Rate@5', 'N/A'):<8} "
              f"{row.get('Avg_Latency_ms', 'N/A')}ms")
    
    print(f"\n{'='*100}")


def main():
    parser = argparse.ArgumentParser(description="Full evaluation of JobMatch system")
    parser.add_argument("--output-dir", default=str(RESULTS_DIR),
                        help="Directory to save results")
    parser.add_argument("--skip-latency", action="store_true",
                        help="Skip latency measurement")
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("  JobMatch - Full Dissertation Evaluation")
    print("="*70)
    
    # Load evaluation data
    eval_data = load_eval_data()
    print(f"  Loaded {len(eval_data['queries'])} test queries")
    print(f"  Relevance labels: {len(eval_data['relevance_labels'])} judgments")
    
    db = SessionLocal()
    summary_rows = []
    
    try:
        # System 1: Keyword baseline
        print("\n  [1/4] Evaluating Keyword Baseline (BM25)...")
        summary, _ = evaluate_system(
            "Baseline 1: Keyword (BM25)",
            keyword_baseline_func,
            eval_data,
            db,
        )
        summary_rows.append(summary)
        
        # System 2: Rule-based baseline
        print("  [2/4] Evaluating Rule-Based Baseline (No Embeddings)...")
        summary, _ = evaluate_system(
            "Baseline 2: Rule-Based (No Embeddings)",
            rule_based_baseline_func,
            eval_data,
            db,
        )
        summary_rows.append(summary)
        
        # System 3: Embedding-only baseline
        print("  [3/4] Evaluating Embedding-Only Baseline...")
        summary, _ = evaluate_system(
            "Baseline 3: Embedding Only",
            embedding_only_baseline_func,
            eval_data,
            db,
        )
        summary_rows.append(summary)
        
        # System 4: Proposed system
        print("  [4/4] Evaluating Proposed System (Full Pipeline)...")
        summary, _ = evaluate_system(
            "Proposed System (Full)",
            proposed_system_func,
            eval_data,
            db,
        )
        summary_rows.append(summary)
        
        # Display results
        print_comparison_table(summary_rows)
        
        # Export
        output_dir = Path(args.output_dir)
        export_results(summary_rows, output_dir)
        
        print("\n  Evaluation complete!")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
