/**
 * Client-Side Feedback Agent Utility
 * Generates participant-facing commentary (deliberately decoupled from judge-facing numeric scoring).
 * Focuses on constructive commentary, strengths, and actionable growth areas.
 */

export function generateParticipantFeedback(submission) {
	if (!submission) {
		return {
			status: "pending",
			commentary: "Submission data is currently unavailable.",
			strengths: [],
			improvements: []
		};
	}

	const teamName = submission.team_name || "Participant Team";
	const cq = submission.code_quality || {};
	const fn = submission.functionality || {};
	const orig = submission.originality || {};
	const innov = submission.innovation || {};

	const cqScore = cq.score;
	const fnScore = fn.score;
	const origScore = orig.score;
	const innovScore = innov.score;

	if (cqScore == null || fnScore == null || origScore == null) {
		return {
			status: "pending",
			commentary: "Evaluation pipeline is currently processing. Participant feedback will unlock once evaluations finish.",
			strengths: [],
			improvements: []
		};
	}

	const strengths = [];
	const improvements = [];

	// Code Quality Feedback
	if (cqScore >= 85) {
		strengths.append ? strengths.push("Clean AST code structure with high maintainability.") : strengths.push("Clean AST code structure with high maintainability.");
		if (cq.summary) {
			strengths.push(`Static analysis highlight: ${cq.summary}`);
		}
	} else if (cqScore < 75) {
		improvements.push("Refactor deeply nested functions and address lint warnings to improve code clarity.");
		if (cq.summary) {
			improvements.push(`Code quality area: ${cq.summary}`);
		}
	}

	// Functionality Feedback
	if (fnScore >= 90) {
		strengths.push("Excellent test suite execution with low latency and stable memory usage.");
	} else if (fnScore < 75) {
		improvements.push("Ensure edge cases are validated and async resources are cleaned up to prevent timeout exceptions.");
	}

	// Originality Feedback
	if (origScore >= 85) {
		strengths.push("High codebase novelty with low AST fingerprint similarity across prior submissions.");
	} else if (origScore < 75) {
		improvements.push("Reduce reliance on external starter template code; build custom domain logic.");
	}

	// Innovation Feedback
	if (innovScore && innovScore >= 80) {
		strengths.push("Creative architectural design and novel feature implementation.");
		if (innov.raw_metrics && innov.raw_metrics.techniques) {
			strengths.push(`Standout techniques: ${innov.raw_metrics.techniques.join(", ")}`);
		}
	} else if (innovScore && innovScore < 75) {
		improvements.push("Explore innovative UX patterns or advanced performance optimization techniques.");
	}

	if (strengths.length === 0) {
		strengths.push("Successfully submitted a functioning project satisfying the hackathon criteria.");
	}
	if (improvements.length === 0) {
		improvements.push("Add inline documentation and expand unit test assertion coverage.");
	}

	const commentary = `Kudos to **${teamName}** for completing the hackathon challenge! Your team built a solid foundation. Use the constructive items below to further enhance project quality for production deployment.`;

	return {
		status: "complete",
		team_name: teamName,
		commentary,
		strengths,
		improvements,
		visibility: "participant_visible"
	};
}
