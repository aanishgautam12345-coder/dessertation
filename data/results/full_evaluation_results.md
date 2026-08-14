# JobMatch Full Evaluation Results

**Date:** 2026-08-15 03:06:11

## System Comparison

| System | P@5 | P@10 | NDCG@5 | NDCG@10 | MRR | Hit Rate@5 | Avg Latency (ms) |
|--------|-----|------|--------|---------|-----|------------|------------------|
| Baseline 1: Keyword (BM25) | 0.0 | 0.004 | 0.0 | 0.014 | 0.011 | 0.12 | 32.6 |
| Baseline 2: Rule-Based (No Embeddings) | 0.008 | 0.004 | 0.04 | 0.04 | 0.04 | 0.04 | 4941.7 |
| Baseline 3: Embedding Only | 0.36 | 0.236 | 0.541 | 0.59 | 0.664 | 0.96 | 2339.5 |
| Proposed System (Full) | 0.592 | 0.508 | 0.597 | 0.735 | 0.709 | 0.96 | 50.9 |

## Detailed Metrics

### Baseline 1: Keyword (BM25)

- **num_queries:** 25
- **total_results:** 125
- **P@5:** 0.0
- **Graded_P@5:** 0.0
- **MAP@5:** 0.011
- **MRR@5:** 0.011
- **NDCG@5:** 0.0
- **Hit_Rate@5:** 0.12
- **Avg_Relevant_Found@5:** 0.12
- **P@10:** 0.004
- **Graded_P@10:** 0.001
- **MAP@10:** 0.011
- **MRR@10:** 0.011
- **NDCG@10:** 0.014
- **Hit_Rate@10:** 0.12
- **Avg_Relevant_Found@10:** 0.12
- **Avg_Latency_ms:** 32.6
- **P95_Latency_ms:** 53.9
- **Category_Diversity:** 0.028

### Baseline 2: Rule-Based (No Embeddings)

- **num_queries:** 25
- **total_results:** 125
- **P@5:** 0.008
- **Graded_P@5:** 0.005
- **MAP@5:** 0.04
- **MRR@5:** 0.04
- **NDCG@5:** 0.04
- **Hit_Rate@5:** 0.04
- **Avg_Relevant_Found@5:** 0.04
- **P@10:** 0.004
- **Graded_P@10:** 0.003
- **MAP@10:** 0.04
- **MRR@10:** 0.04
- **NDCG@10:** 0.04
- **Hit_Rate@10:** 0.04
- **Avg_Relevant_Found@10:** 0.04
- **Avg_Latency_ms:** 4941.7
- **P95_Latency_ms:** 5293.7
- **Category_Diversity:** 0.02

### Baseline 3: Embedding Only

- **num_queries:** 25
- **total_results:** 125
- **P@5:** 0.36
- **Graded_P@5:** 0.16
- **MAP@5:** 0.532
- **MRR@5:** 0.664
- **NDCG@5:** 0.541
- **Hit_Rate@5:** 0.96
- **Avg_Relevant_Found@5:** 3.24
- **P@10:** 0.236
- **Graded_P@10:** 0.101
- **MAP@10:** 0.532
- **MRR@10:** 0.664
- **NDCG@10:** 0.59
- **Hit_Rate@10:** 0.96
- **Avg_Relevant_Found@10:** 3.24
- **Avg_Latency_ms:** 2339.5
- **P95_Latency_ms:** 2470.9
- **Category_Diversity:** 0.036

### Proposed System (Full)

- **num_queries:** 25
- **total_results:** 125
- **P@5:** 0.592
- **Graded_P@5:** 0.269
- **MAP@5:** 0.709
- **MRR@5:** 0.709
- **NDCG@5:** 0.597
- **Hit_Rate@5:** 0.96
- **Avg_Relevant_Found@5:** 5.08
- **P@10:** 0.508
- **Graded_P@10:** 0.227
- **MAP@10:** 0.709
- **MRR@10:** 0.709
- **NDCG@10:** 0.735
- **Hit_Rate@10:** 0.96
- **Avg_Relevant_Found@10:** 5.08
- **Avg_Latency_ms:** 50.9
- **P95_Latency_ms:** 53.2
- **Category_Diversity:** 0.044

## Interpretation

- **P@K:** Precision at K - fraction of top-K results that are relevant
- **NDCG@K:** Normalized Discounted Cumulative Gain - rewards relevant results ranked higher
- **MRR:** Mean Reciprocal Rank - 1/rank of first relevant result
- **Hit Rate:** Percentage of queries with at least 1 relevant result in top-K
- **Latency:** Response time in milliseconds
