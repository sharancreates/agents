import rawSubmissions from "../mockData/submissions.json";
import { calculateSynthesisScore, generateSynthesisSummary } from "../utils/synthesisAgent";

// The base URL for Person 1's FastAPI orchestrator
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

/**
 * Helper to simulate a network delay when returning mock data
 */
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Retrieves the submissions list from LocalStorage, falling back to mock JSON
 */
const getLocalSubmissions = () => {
	const saved = localStorage.getItem("autojudge_submissions");
	if (!saved || saved === "[]") {
		localStorage.setItem("autojudge_submissions", JSON.stringify(rawSubmissions));
		return rawSubmissions;
	}
	try {
		return JSON.parse(saved);
	} catch (err) {
		console.warn("Failed to parse submissions from local storage, falling back", err);
		return rawSubmissions;
	}
};

/**
 * Saves submissions to LocalStorage
 */
const saveLocalSubmissions = (data) => {
	localStorage.setItem("autojudge_submissions", JSON.stringify(data));
};

/**
 * Helper to update a single submission in local storage
 */
const updateLocalSubmission = (id, updateFn) => {
	const subs = getLocalSubmissions();
	const idx = subs.findIndex((sub) => sub.submission_id === id);
	if (idx !== -1) {
		subs[idx] = updateFn(subs[idx]);
		saveLocalSubmissions(subs);
	}
};

/**
 * Simulates the background evaluation runner when offline
 */
const simulatePipelineRun = (id) => {
	// Stage 1: Switch to running status
	setTimeout(() => {
		updateLocalSubmission(id, (sub) => {
			sub.pipeline_status = "running";
			sub.code_quality.status = "running";
			return sub;
		});
	}, 2000);

	// Stage 2: Code Quality completes, Functionality starts running
	setTimeout(() => {
		updateLocalSubmission(id, (sub) => {
			sub.code_quality = {
				status: "complete",
				score: Math.floor(78 + Math.random() * 20),
				summary: "AST syntax trees analyzed successfully. Modular structure satisfies codebase constraints.",
				flags: [],
				raw_metrics: {
					complexity_score: Math.floor(8 + Math.random() * 12),
					lint_warnings: Math.floor(Math.random() * 6),
					lint_severity: "low",
				},
				error_message: null
			};
			sub.functionality.status = "running";
			return sub;
		});
	}, 5000);

	// Stage 3: Functionality completes, Originality starts running
	setTimeout(() => {
		updateLocalSubmission(id, (sub) => {
			sub.functionality = {
				status: "complete",
				score: Math.floor(82 + Math.random() * 18),
				summary: "Sandbox test cases executed successfully. Average response latency satisfies Service Level Objectives.",
				flags: [],
				raw_metrics: {
					tests_passed: 15,
					total_tests: 15,
					avg_runtime_ms: Math.floor(110 + Math.random() * 90),
					peak_memory_mb: Math.floor(220 + Math.random() * 180) / 10,
				},
				error_message: null
			};
			sub.originality.status = "running";
			return sub;
		});
	}, 8000);

	// Stage 4: Originality completes, Innovation starts running
	setTimeout(() => {
		updateLocalSubmission(id, (sub) => {
			sub.originality = {
				status: "complete",
				score: Math.floor(85 + Math.random() * 15),
				summary: "Checked against public directories and prior hackathon entries. Zero high-matching similarity detected.",
				flags: [],
				raw_metrics: {
					similarity_confidence: Math.floor(2 + Math.random() * 8) / 100,
				},
				error_message: null
			};
			sub.innovation.status = "running";
			return sub;
		});
	}, 11000);

	// Stage 5: Innovation completes, Pipeline Marks Complete
	setTimeout(() => {
		updateLocalSubmission(id, (sub) => {
			sub.innovation = {
				status: "complete",
				score: Math.floor(75 + Math.random() * 22),
				summary: "Excellent UI aesthetics and implementation of safety barrier clamping algorithms.",
				flags: [],
				raw_metrics: {
					architecture_novelty: Math.floor(6 + Math.random() * 4),
					techniques: ["CBF Safety Clamp", "Dynamic Redux Store caching"],
				},
				error_message: null
			};
			sub.pipeline_status = "complete";
			sub.overall_score = calculateSynthesisScore(sub);
			sub.synthesis_summary = generateSynthesisSummary(sub);
			return sub;
		});
	}, 14000);
};

export const fetchSubmissions = async () => {
	try {
		const response = await fetch(`${API_BASE_URL}/submissions`);
		if (!response.ok) {
			throw new Error(`API Error: ${response.status} ${response.statusText}`);
		}
		const data = await response.json();
		console.log("Successfully fetched submissions from live API");
		return data;
	} catch (err) {
		console.warn(
			"FastAPI backend connection failed. Falling back to local storage.",
			err.message,
		);
		// Simulate network latency for mock data to keep the loading states visible
		await delay(600);
		return getLocalSubmissions();
	}
};

export const fetchSubmissionById = async (id) => {
	try {
		// Attempting P1's status detail endpoint
		const response = await fetch(`${API_BASE_URL}/submissions/${id}`);
		if (!response.ok) {
			throw new Error(`API Error: ${response.status} ${response.statusText}`);
		}
		const data = await response.json();
		console.log(`Successfully fetched details for ${id} from live API`);
		return data;
	} catch (err) {
		console.warn(
			`FastAPI backend connection failed for submission ${id}. Falling back to local storage.`,
			err.message,
		);
		await delay(300);
		const localSubmissions = getLocalSubmissions();
		const submission = localSubmissions.find((sub) => sub.submission_id === id);
		if (submission) {
			return submission;
		} else {
			throw new Error("Submission not found", { cause: err });
		}
	}
};

export const updateWeightsOnBackend = async (weights) => {
	try {
		const response = await fetch(`${API_BASE_URL}/submissions/recalculate-all-synthesis`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(weights),
		});
		if (!response.ok) {
			throw new Error(`API Error: ${response.status} ${response.statusText}`);
		}
		const data = await response.json();
		console.log("Successfully recalculated all synthesis scores on backend", data);
		return data;
	} catch (err) {
		console.warn("FastAPI backend connection failed. Rubric weights saved locally only.", err.message);
		return null;
	}
};

export const submitRepository = async (payload) => {
	try {
		const response = await fetch(`${API_BASE_URL}/submissions`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(payload),
		});
		if (!response.ok) {
			throw new Error(`API Error: ${response.status} ${response.statusText}`);
		}
		const data = await response.json();
		console.log("Successfully submitted repository to live API", data);
		return data;
	} catch (err) {
		console.warn(
			"FastAPI backend connection failed. Saving submission to local storage and starting mock pipeline.",
			err.message,
		);
		await delay(600);

		const localSubmissions = getLocalSubmissions();

		// Generate random 40 character SHA if empty
		const commitSha = payload.commit_sha
			? payload.commit_sha
			: Array.from({ length: 40 }, () => Math.floor(Math.random() * 16).toString(16)).join("");

		const newSub = {
			submission_id: `sub_${String(localSubmissions.length + 1).padStart(3, "0")}`,
			team_name: payload.team_name,
			repo_url: payload.repo_url,
			commit_sha: commitSha,
			pipeline_status: "pending",
			submitted_at: new Date().toISOString(),
			overall_score: null,
			code_quality: {
				status: "pending",
				score: null,
				summary: null,
				flags: [],
				raw_metrics: {},
				error_message: null
			},
			functionality: {
				status: "pending",
				score: null,
				summary: null,
				flags: [],
				raw_metrics: {},
				error_message: null
			},
			originality: {
				status: "pending",
				score: null,
				summary: null,
				flags: [],
				raw_metrics: {},
				error_message: null
			},
			innovation: {
				status: "pending",
				score: null,
				summary: null,
				flags: [],
				raw_metrics: {},
				error_message: null
			}
		};

		// Prepend to display latest submissions first
		const updated = [newSub, ...localSubmissions];
		saveLocalSubmissions(updated);

		// Trigger background evaluation simulation
		simulatePipelineRun(newSub.submission_id);

		return newSub;
	}
};
