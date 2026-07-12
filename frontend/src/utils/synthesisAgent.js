/**
 * Calculates the composite score for a submission based on agent evaluations.
 * Enforces that code_quality, functionality, and originality are REQUIRED dimensions.
 * Treats innovation as an OPTIONAL dimension.
 * 
 * @param {Object} submission - The submission object to evaluate.
 * @returns {number|null} - Composite score out of 100 (rounded to 1 decimal place) or null if incomplete.
 */
export function calculateSynthesisScore(submission) {
	if (!submission) return null;

	// Base weights for each dimension
	const weights = {
		code_quality: 40,
		functionality: 40,
		originality: 20,
		innovation: 10, // Optional
	};

	// Helper to extract a valid numerical score
	const getValidScore = (dimension) => {
		const dim = submission[dimension];
		if (dim && dim.status === "complete" && typeof dim.score === "number") {
			return dim.score;
		}
		return null;
	};

	// Required dimensions
	const requiredDimensions = ["code_quality", "functionality", "originality"];
	
	// Check if all required dimensions are complete and have numerical scores
	const requiredScores = {};
	for (const dim of requiredDimensions) {
		const score = getValidScore(dim);
		if (score === null) {
			// One or more required dimensions are not complete yet
			return null;
		}
		requiredScores[dim] = score;
	}

	// Start with required dimensions
	let totalWeightedScore = 
		requiredScores.code_quality * weights.code_quality +
		requiredScores.functionality * weights.functionality +
		requiredScores.originality * weights.originality;
		
	let totalActiveWeight = 
		weights.code_quality + 
		weights.functionality + 
		weights.originality;

	// Check optional innovation score
	const innovationScore = getValidScore("innovation");
	if (innovationScore !== null) {
		totalWeightedScore += innovationScore * weights.innovation;
		totalActiveWeight += weights.innovation;
	}

	// Calculate and normalize to a 100-point scale
	const finalScore = totalWeightedScore / totalActiveWeight;

	// Round to one decimal place
	return Math.round(finalScore * 10) / 10;
}
