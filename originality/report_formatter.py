"""
Report Formatter & Evaluation Matrix Aggregator Module.
Combines code similarity, architectural scoring, boilerplate filtering,
and comment neutralization signals into a finalized evaluation matrix.
"""

import json
from typing import Dict, Any

class ReportFormatter:
    def __init__(self, weight_similarity: float = 0.4, weight_architecture: float = 0.6):
        self.weight_similarity = weight_similarity
        self.weight_architecture = weight_architecture

    def calculate_composite_score(self, similarity_score: float, arch_scores: Dict[str, float]) -> float:
        """
        Calculates a composite originality score (0.0 to 1.0).
        High code similarity lowers the score; high architectural novelty raises it.
        """
        code_originality = max(0.0, 1.0 - similarity_score)
        
        design_integrity = arch_scores.get("design_integrity", 0.5)
        structural_novelty = arch_scores.get("structural_novelty", 0.5)
        readme_consistency = arch_scores.get("readme_consistency", 0.5)
        
        avg_arch_score = (design_integrity + structural_novelty + readme_consistency) / 3.0
        
        composite = (code_originality * self.weight_similarity) + (avg_arch_score * self.weight_architecture)
        return round(composite, 3)

    def generate_evaluation_matrix(
        self,
        submission_id: str,
        similarity_metrics: Dict[str, Any],
        architecture_metrics: Dict[str, Any],
        filtering_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Aggregates all evaluation streams into a single structured dictionary matrix."""
        sim_score = similarity_metrics.get("max_similarity", 0.0)
        arch_scores = architecture_metrics.get("scores", {})
        
        composite = self.calculate_composite_score(sim_score, arch_scores)

        matrix = {
            "submission_id": submission_id,
            "composite_originality_score": composite,
            "verdict": "FLAGGED" if composite < 0.45 else ("NEEDS_REVIEW" if composite < 0.70 else "PASSED"),
            "breakdown": {
                "code_similarity": {
                    "max_similarity_ratio": sim_score,
                    "matched_blocks_count": similarity_metrics.get("matched_blocks", 0)
                },
                "architecture_scoring": architecture_metrics,
                "pre_processing_filters": filtering_summary
            }
        }
        return matrix

    def export_markdown_report(self, matrix: Dict[str, Any]) -> str:
        """Formats the evaluation matrix into a Markdown report for reviewers."""
        sub_id = matrix["submission_id"]
        score = matrix["composite_originality_score"]
        verdict = matrix["verdict"]
        breakdown = matrix["breakdown"]

        md = f"""# Originality & Architecture Evaluation Report

**Submission ID:** `{sub_id}`  
**Verdict:** `{verdict}`  
**Composite Score:** `{score} / 1.0`

---

## 1. Summary Breakdown
- **Code Originality Rating:** `{round(1.0 - breakdown['code_similarity']['max_similarity_ratio'], 2)}`
- **Max Code Similarity Detected:** `{breakdown['code_similarity']['max_similarity_ratio'] * 100}%`
- **Matched Function Blocks:** `{breakdown['code_similarity']['matched_blocks_count']}`

## 2. Architectural Evaluation
- **Design Integrity:** `{breakdown['architecture_scoring'].get('scores', {}).get('design_integrity', 'N/A')}`
- **Structural Novelty:** `{breakdown['architecture_scoring'].get('scores', {}).get('structural_novelty', 'N/A')}`
- **README Consistency:** `{breakdown['architecture_scoring'].get('scores', {}).get('readme_consistency', 'N/A')}`

## 3. Pre-Processing Filters Applied
- **Boilerplate Files Bypassed:** `{breakdown['pre_processing_filters'].get('boilerplate_files_count', 0)}`
- **Non-ASCII Comments Neutralized:** `{breakdown['pre_processing_filters'].get('neutralized_comments_count', 0)}`

---
*Report generated automatically by Originality Agent Engine.*
"""
        return md


if __name__ == "__main__":
    formatter = ReportFormatter()
    dummy_matrix = formatter.generate_evaluation_matrix(
        submission_id="SUBM_10293",
        similarity_metrics={"max_similarity": 0.15, "matched_blocks": 1},
        architecture_metrics={"scores": {"design_integrity": 0.85, "structural_novelty": 0.90, "readme_consistency": 0.80}},
        filtering_summary={"boilerplate_files_count": 3, "neutralized_comments_count": 12}
    )
    print("Generated JSON Matrix:\n", json.dumps(dummy_matrix, indent=2))
    print("\nGenerated Markdown Report:\n", formatter.export_markdown_report(dummy_matrix))