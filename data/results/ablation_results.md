# JobMatch Ablation Study Results

**Date:** 2026-08-15 03:10:20

## Component Contribution Analysis

| Config | P@10 | MAP | MRR | NDCG@10 | Hit Rate |
|--------|------|-----|-----|---------|----------|
| Full system | 0.344 | 0.533 | 0.571 | 0.635 | 0.880 |
| No semantic | 0.352 | 0.511 | 0.549 | 0.623 | 0.880 |
| No skills | 0.348 | 0.561 | 0.610 | 0.646 | 0.880 |
| No location | 0.356 | 0.524 | 0.589 | 0.649 | 0.960 |
| No salary | 0.336 | 0.535 | 0.590 | 0.629 | 0.880 |
| No experience | 0.356 | 0.529 | 0.576 | 0.635 | 0.880 |
| Semantic only | 0.508 | 0.709 | 0.709 | 0.735 | 0.960 |
| Metadata only | 0.352 | 0.507 | 0.551 | 0.622 | 0.880 |

## Interpretation

- **Full vs No semantic:** Contribution of semantic embeddings to scoring
- **Full vs No skills:** Contribution of skill matching
- **Full vs No location:** Contribution of location matching
- **Full vs No salary:** Contribution of salary matching
- **Full vs No experience:** Contribution of experience matching
- **Semantic only:** Performance using only semantic similarity
- **Metadata only:** Performance using only metadata (no semantic)
