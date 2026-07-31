/**
 * Retrieves the current rubric weights from localStorage or returns defaults
 */
export function getStoredWeights() {
	const saved = localStorage.getItem("autojudge_rubric_weights");
	if (saved) {
		try {
			const parsed = JSON.parse(saved);
			if (
				typeof parsed.code_quality === "number" &&
				typeof parsed.functionality === "number" &&
				typeof parsed.originality === "number" &&
				typeof parsed.innovation === "number"
			) {
				return parsed;
			}
		} catch (e) {
			console.error("Failed to parse stored rubric weights:", e);
		}
	}
	// Default weights: 30% CQ, 30% Fn, 20% Or, 20% In
	return {
		code_quality: 30,
		functionality: 30,
		originality: 20,
		innovation: 20,
	};
}

/**
 * Calculates the composite score for a submission based on agent evaluations.
 * Enforces all 4 dimensions (code_quality, functionality, originality, innovation).
 * 
 * @param {Object} submission - The submission object to evaluate.
 * @param {Object} [customWeights] - Optional custom weights override.
 * @returns {number|null} - Composite score out of 100 (rounded to 1 decimal place) or null if incomplete.
 */
export function calculateSynthesisScore(submission, customWeights) {
	if (!submission) return null;

	const weights = customWeights || getStoredWeights();
	const dimensions = ["code_quality", "functionality", "originality", "innovation"];

	// Helper to extract a valid numerical score
	const getValidScore = (dimension) => {
		const dim = submission[dimension];
		if (dim && dim.status === "complete" && typeof dim.score === "number") {
			return dim.score;
		}
		return null;
	};

	let totalWeightedScore = 0;
	let totalActiveWeight = 0;

	for (const dim of dimensions) {
		const score = getValidScore(dim);
		// If any dimension is not complete, we cannot calculate the final overall score
		if (score === null) {
			return null;
		}
		totalWeightedScore += score * weights[dim];
		totalActiveWeight += weights[dim];
	}

	if (totalActiveWeight === 0) return 0;

	const finalScore = totalWeightedScore / totalActiveWeight;
	return Math.round(finalScore * 10) / 10;
}

/**
 * Generates a detailed, professional human-readable synthesis summary for a submission
 * 
 * @param {Object} submission - The submission object
 * @param {Object} [customWeights] - Optional custom weights override
 * @returns {string} - The synthesis summary text
 */
export function generateSynthesisSummary(submission, customWeights) {
	if (!submission) return "No submission data available.";
	
	const weights = customWeights || getStoredWeights();
	const score = calculateSynthesisScore(submission, weights);

	if (score === null) {
		return "Evaluation pipeline is currently active. The synthesis summary will be compiled once all agent reports are finalized.";
	}

	const cq = submission.code_quality;
	const fn = submission.functionality;
	const orig = submission.originality;
	const innov = submission.innovation;

	// Identify highest and lowest dimensions
	const scores = [
		{ name: "Code Quality", score: cq.score, weight: weights.code_quality, detail: cq },
		{ name: "Functionality", score: fn.score, weight: weights.functionality, detail: fn },
		{ name: "Originality", score: orig.score, weight: weights.originality, detail: orig },
		{ name: "Innovation", score: innov.score, weight: weights.innovation, detail: innov }
	];

	// Sort to find strengths/weaknesses
	const sortedScores = [...scores].sort((a, b) => b.score - a.score);
	const best = sortedScores[0];
	const worst = sortedScores[sortedScores.length - 1];

	// Check for any flags in all dimensions
	const allFlags = [];
	scores.forEach(dim => {
		if (dim.detail.flags && dim.detail.flags.length > 0) {
			dim.detail.flags.forEach(f => {
				allFlags.push({ dimension: dim.name, ...f });
			});
		}
	});

	// Build executive summary
	let verdict = "";
	if (score >= 90) {
		verdict = "exceptional, standing out as a high-tier implementation with excellent execution across all evaluated domains";
	} else if (score >= 75) {
		verdict = "strong and competent, demonstrating robust delivery with minor areas for refinement";
	} else if (score >= 50) {
		verdict = "satisfactory but showing notable gaps, requiring structural changes or feature corrections before production readiness";
	} else {
		verdict = "critical issues detected, failing to satisfy basic hackathon thresholds in multiple dimensions";
	}

	let summary = `This submission for team **${submission.team_name || "Unknown Team"}** achieved a composite score of ${score.toFixed(1)}/100, evaluated using custom weights (${weights.code_quality}% Code Quality, ${weights.functionality}% Functionality, ${weights.originality}% Originality, and ${weights.innovation}% Innovation). The evaluation team classifies this entry as ${verdict}.\n\n`;

	// Highlight strengths and details
	summary += `### Core Strengths & Technical Highlights\n`;
	summary += `The project's primary strength is **${best.name}**, where it scored **${best.score}/100**. `;
	if (best.name === "Code Quality") {
		summary += `Our static analysis noted: "${cq.summary || "Clean structural setup."}" `;
		if (cq.raw_metrics && cq.raw_metrics.complexity_score) {
			summary += `It maintained a low complexity rating of ${cq.raw_metrics.complexity_score} and only ${cq.raw_metrics.lint_warnings || 0} lint warnings.`;
		}
	} else if (best.name === "Functionality") {
		summary += `The execution sandbox reported: "${fn.summary || "All test cases passed."}" `;
		if (fn.raw_metrics && fn.raw_metrics.tests_passed) {
			summary += `It successfully passed ${fn.raw_metrics.tests_passed} out of ${fn.raw_metrics.total_tests || fn.raw_metrics.tests_passed} tests in the test suite.`;
		}
	} else if (best.name === "Originality") {
		summary += `The originality analysis concluded: "${orig.summary || "Highly unique code signature."}"`;
	} else if (best.name === "Innovation") {
		summary += `The innovation agent reported: "${innov.summary || "Highly innovative application features."}"`;
		if (innov.raw_metrics && innov.raw_metrics.techniques) {
			summary += ` It showcased cutting-edge techniques such as: ${innov.raw_metrics.techniques.join(", ")}.`;
		}
	}
	summary += `\n\n`;

	// Weaknesses / Refinements
	if (worst.score < 90 && worst.name !== best.name) {
		summary += `### Opportunities for Improvement\n`;
		summary += `Conversely, the lowest scoring dimension was **${worst.name}** at **${worst.score}/100**. `;
		if (worst.name === "Code Quality") {
			summary += `Code review comments highlight: "${cq.summary}" `;
			if (cq.raw_metrics && cq.raw_metrics.complexity_score > 25) {
				summary += `The code exhibits high cyclomatic complexity (score ${cq.raw_metrics.complexity_score}) and may be prone to maintainability challenges.`;
			}
		} else if (worst.name === "Functionality") {
			summary += `Sandbox feedback indicates: "${fn.summary}" `;
			if (fn.raw_metrics && fn.raw_metrics.tests_passed < fn.raw_metrics.total_tests) {
				summary += `It failed ${fn.raw_metrics.total_tests - fn.raw_metrics.tests_passed} test cases under edge load.`;
			}
		} else if (worst.name === "Originality") {
			summary += `Originality scans flagged matching content: "${orig.summary}"`;
		} else if (worst.name === "Innovation") {
			summary += `The solution followed standard design patterns: "${innov.summary}"`;
		}
		summary += `\n\n`;
	}

	// Flags section
	if (allFlags.length > 0) {
		summary += `### ⚠️ Critical Flags & Warnings\n`;
		allFlags.forEach(flag => {
			summary += `- **${flag.dimension} [${flag.type.replace(/_/g, " ").toUpperCase()}]:** ${flag.message}\n`;
		});
		summary += `\n`;
	}

	return summary;
}
