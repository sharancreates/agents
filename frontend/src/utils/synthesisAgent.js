export function calculateSynthesisScore(submission) {
	// Define base weights (these will become configurable via the UI in Week 3)
	const baseWeights = {
		code_quality: 40,
		functionality: 40,
		originality: 20,
		innovation: 10, // Treated as optional for now
	};

	let totalWeightedScore = 0;
	let activeTotalWeight = 0;

	// Helper to safely extract a score if the agent has completed its run
	const getScore = (dimension) => {
		if (
			submission[dimension] &&
			typeof submission[dimension].score === "number"
		) {
			return submission[dimension].score;
		}
		return null;
	};

	const scores = {
		code_quality: getScore("code_quality"),
		functionality: getScore("functionality"),
		originality: getScore("originality"),
		innovation: getScore("innovation"),
	};

	// Calculate the weighted total based ONLY on available scores
	for (const [dimension, score] of Object.entries(scores)) {
		if (score !== null) {
			totalWeightedScore += score * baseWeights[dimension];
			activeTotalWeight += baseWeights[dimension];
		}
	}

	// If no agents have successfully returned a score yet, return null
	if (activeTotalWeight === 0) return null;

	// Normalize back to a 100-point scale based on the active weights
	const finalScore = totalWeightedScore / activeTotalWeight;

	// Round to one decimal place for a clean UI presentation
	return Math.round(finalScore * 10) / 10;
}
