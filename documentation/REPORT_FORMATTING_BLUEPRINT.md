# Report Formatting & Evaluation Matrix Blueprint

This blueprint describes the evaluation matrix aggregation formulas and report formatting utilities implemented on Day 21 of the engineering sprint.

## Score Aggregation Formula
The Composite Originality Score $S_{\text{composite}}$ is computed as:
$$S_{\text{composite}} = (1.0 - S_{\text{similarity}}) \times W_{\text{sim}} + \bar{S}_{\text{arch}} \times W_{\text{arch}}$$

Where:
- $S_{\text{similarity}}$: Maximum code similarity ratio detected ($[0.0, 1.0]$).
- $\bar{S}_{\text{arch}}$: Average of Design Integrity, Structural Novelty, and README Consistency scores ($[0.0, 1.0]$).
- $W_{\text{sim}} = 0.4$, $W_{\text{arch}} = 0.6$: Weight allocation parameters.

## Verdict Decision Thresholds
- **PASSED**: $S_{\text{composite}} \ge 0.70$
- **NEEDS_REVIEW**: $0.45 \le S_{\text{composite}} < 0.70$
- **FLAGGED**: $S_{\text{composite}} < 0.45$

The implementation files reside in:
- `agents/originality/report_formatter.py`
- `agents/originality/test_report_formatter.py`