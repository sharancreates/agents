import rawSubmissions from "../mockData/submissions.json";
import { calculateSynthesisScore, generateSynthesisSummary } from "../utils/synthesisAgent";
import { generateParticipantFeedback } from "../utils/feedbackAgent";

// The base URL for the FastAPI orchestrator and B2B API endpoints
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

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
			sub.participant_feedback = generateParticipantFeedback(sub);
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

export const fetchParticipantFeedback = async (submissionId) => {
	try {
		const response = await fetch(`${API_BASE_URL}/submissions/${submissionId}/feedback`);
		if (!response.ok) {
			throw new Error(`API Error: ${response.status} ${response.statusText}`);
		}
		const data = await response.json();
		return data;
	} catch (err) {
		console.warn(`FastAPI backend feedback call failed for ${submissionId}, computing locally.`, err.message);
		const sub = await fetchSubmissionById(submissionId);
		return generateParticipantFeedback(sub);
	}
};

// ==========================================
// Phase 5 Enterprise Portal & Observability APIs
// ==========================================

const V1_BASE_URL = API_BASE_URL.replace("/api", "/v1");

/**
 * Retrieves the stored API key from local storage or environment.
 */
export const getStoredApiKey = () => {
	const directKey = localStorage.getItem("autojudge_api_key");
	if (directKey) return directKey;

	try {
		const saved = localStorage.getItem("autojudge_api_keys");
		if (saved) {
			const list = JSON.parse(saved);
			if (Array.isArray(list) && list.length > 0 && list[0].api_key) {
				return list[0].api_key;
			}
		}
	} catch (e) {
		// ignore JSON error
	}

	return import.meta.env.VITE_AUTOJUDGE_API_KEY || "";
};

/**
 * Sets or removes the stored active API key.
 */
export const setStoredApiKey = (key) => {
	if (key) {
		localStorage.setItem("autojudge_api_key", key);
	} else {
		localStorage.removeItem("autojudge_api_key");
	}
};

/**
 * Constructs request headers including Authorization Bearer token when available.
 */
export const getAuthHeaders = (extraHeaders = {}) => {
	const key = getStoredApiKey();
	const headers = { ...extraHeaders };
	if (key) {
		headers["Authorization"] = `Bearer ${key}`;
	}
	return headers;
};

/**
 * Connects to live Server-Sent Events (SSE) stream for real-time agent thought observation.
 * Falls back gracefully to interval polling if SSE is unsupported or disconnected.
 */
export const streamEvaluationTraces = (submissionId, onEvent, onError) => {
	const apiKey = getStoredApiKey();
	const tokenQuery = apiKey ? `?token=${encodeURIComponent(apiKey)}` : "";
	const streamUrl = `${V1_BASE_URL}/evaluations/${submissionId}/stream${tokenQuery}`;
	let eventSource = null;
	let pollInterval = null;

	const startPolling = () => {
		if (pollInterval) return;
		pollInterval = setInterval(async () => {
			try {
				const res = await fetch(`${V1_BASE_URL}/evaluations/${submissionId}/traces`, {
					headers: getAuthHeaders()
				});
				if (res.ok) {
					const data = await res.json();
					(data.traces || []).forEach(tr => {
						onEvent({ event: "agent.trace", trace: tr });
					});
				}
			} catch (e) {
				if (onError) onError(e);
			}
		}, 3000);
	};

	try {
		if (typeof EventSource !== "undefined") {
			eventSource = new EventSource(streamUrl);
			eventSource.onmessage = (e) => {
				try {
					const parsed = JSON.parse(e.data);
					onEvent(parsed);
					if (parsed.event === "pipeline.complete") {
						eventSource.close();
					}
				} catch (err) {
					console.warn("Failed to parse SSE payload:", err);
				}
			};
			eventSource.onerror = (err) => {
				console.warn("SSE connection interrupted, falling back to polling", err);
				if (eventSource) {
					eventSource.close();
					eventSource = null;
				}
				startPolling();
			};
		} else {
			startPolling();
		}
	} catch (err) {
		startPolling();
	}

	return () => {
		if (eventSource) eventSource.close();
		if (pollInterval) clearInterval(pollInterval);
	};
};

/**
 * Developer Console API Keys
 */
export const fetchApiKeys = async () => {
	try {
		const res = await fetch(`${V1_BASE_URL}/api-keys`, {
			headers: getAuthHeaders()
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		return await res.json();
	} catch (e) {
		const saved = localStorage.getItem("autojudge_api_keys");
		return saved ? JSON.parse(saved) : [
			{ id: 1, name: "Default Hackathon Key", key_prefix: "ak_live_a1b2c3d4", scopes: ["eval:read", "eval:write"], is_active: true, created_at: new Date().toISOString() }
		];
	}
};

export const createApiKey = async (payload) => {
	try {
		const res = await fetch(`${V1_BASE_URL}/api-keys`, {
			method: "POST",
			headers: getAuthHeaders({ "Content-Type": "application/json" }),
			body: JSON.stringify(payload)
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		return await res.json();
	} catch (e) {
		const prefix = "ak_live_" + Math.random().toString(36).substring(2, 10);
		const secret = Array.from({length: 32}, () => Math.floor(Math.random()*16).toString(16)).join("");
		const mockKey = {
			id: Date.now(),
			name: payload.name || "Custom API Key",
			api_key: `${prefix}_${secret}`,
			key_prefix: prefix,
			scopes: payload.scopes || ["eval:read", "eval:write"],
			is_active: true,
			created_at: new Date().toISOString(),
			warning: "Store this key in a secure location. It will never be displayed again."
		};
		const saved = await fetchApiKeys();
		localStorage.setItem("autojudge_api_keys", JSON.stringify([mockKey, ...saved]));
		return mockKey;
	}
};

/**
 * Developer Console Webhooks
 */
export const fetchWebhooks = async () => {
	try {
		const res = await fetch(`${V1_BASE_URL}/webhooks`, {
			headers: getAuthHeaders()
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		return await res.json();
	} catch (e) {
		const saved = localStorage.getItem("autojudge_webhooks");
		return saved ? JSON.parse(saved) : [];
	}
};

export const registerWebhook = async (payload) => {
	try {
		const res = await fetch(`${V1_BASE_URL}/webhooks`, {
			method: "POST",
			headers: getAuthHeaders({ "Content-Type": "application/json" }),
			body: JSON.stringify(payload)
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		return await res.json();
	} catch (e) {
		const mockWh = {
			id: Date.now(),
			url: payload.url,
			events: payload.events || ["evaluation.completed"],
			is_active: true,
			created_at: new Date().toISOString()
		};
		const existing = await fetchWebhooks();
		localStorage.setItem("autojudge_webhooks", JSON.stringify([mockWh, ...existing]));
		return mockWh;
	}
};

/**
 * Credits & Razorpay Monetization
 */
export const fetchBillingBalance = async () => {
	try {
		const res = await fetch(`${V1_BASE_URL}/billing/balance`, {
			headers: getAuthHeaders()
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		return await res.json();
	} catch (e) {
		const saved = localStorage.getItem("autojudge_billing_balance");
		return saved ? JSON.parse(saved) : {
			organization_id: 1,
			tier: "pro",
			balance: 25.0,
			total_purchased: 100.0,
			total_consumed: 75.0,
			packages_available: [
				{ id: "starter_100", name: "Team / Bootcamp Pack", credits: 100, amount_paise: 49900, currency: "INR", description: "100 evaluation credits (₹4.99/eval)" },
				{ id: "pro_500", name: "Organizer Pro Pack", credits: 500, amount_paise: 199900, currency: "INR", description: "500 evaluation credits (₹3.99/eval)" },
				{ id: "enterprise_2000", name: "Enterprise Hackathon Pass", credits: 2000, amount_paise: 599900, currency: "INR", description: "2,000 evaluation credits (₹2.99/eval)" }
			]
		};
	}
};

export const createBillingOrder = async (packageId) => {
	try {
		const res = await fetch(`${V1_BASE_URL}/billing/orders`, {
			method: "POST",
			headers: getAuthHeaders({ "Content-Type": "application/json" }),
			body: JSON.stringify({ package_id: packageId })
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		return await res.json();
	} catch (e) {
		const packages = {
			starter_100: { amount_paise: 49900, credits: 100, name: "Team / Bootcamp Pack" },
			pro_500: { amount_paise: 199900, credits: 500, name: "Organizer Pro Pack" },
			enterprise_2000: { amount_paise: 599900, credits: 2000, name: "Enterprise Hackathon Pass" }
		};
		const pkg = packages[packageId] || packages.starter_100;
		return {
			order_id: `order_sim_${Math.random().toString(36).substring(2, 12)}`,
			amount_paise: pkg.amount_paise,
			amount_inr: pkg.amount_paise / 100.0,
			currency: "INR",
			credits_to_grant: pkg.credits,
			package_name: pkg.name,
			key_id: "rzp_test_simulated_key"
		};
	}
};

export const verifyPayment = async (orderId, paymentId, signature) => {
	const res = await fetch(`${V1_BASE_URL}/billing/verify-payment`, {
		method: "POST",
		headers: getAuthHeaders({ "Content-Type": "application/json" }),
		body: JSON.stringify({ order_id: orderId, payment_id: paymentId, signature })
	});
	if (!res.ok) {
		const errData = await res.json().catch(() => ({}));
		throw new Error(errData.detail || `Payment verification failed with HTTP ${res.status}`);
	}
	return await res.json();
};

export const fetchBillingUsage = async () => {
	try {
		const res = await fetch(`${V1_BASE_URL}/billing/usage`, {
			headers: getAuthHeaders()
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		return await res.json();
	} catch (e) {
		return [
			{ id: 1, submission_id: "sub_001", credits_deducted: 1.0, balance_after: 24.0, reason: "submission_evaluation", created_at: new Date().toISOString() }
		];
	}
};

/**
 * Judge Copilot Chat & Sponsor Compliance
 */
export const askJudgeCopilot = async (submissionId, question, topK = 3) => {
	try {
		const res = await fetch(`${V1_BASE_URL}/evaluations/${submissionId}/chat`, {
			method: "POST",
			headers: getAuthHeaders({ "Content-Type": "application/json" }),
			body: JSON.stringify({ question, top_k: topK })
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		return await res.json();
	} catch (e) {
		return {
			submission_id: submissionId,
			question,
			answer: `Based on automated analysis of submission ${submissionId}:\n\nThe requested feature or logic is implemented in the primary service modules with standard error handling. Code citations indicate proper validation routines.\n\nConfidence: 87.5% match against repository index.`,
			citations: [
				{ citation: "person_2/functionality/runner.py:45-80", file_path: "person_2/functionality/runner.py", lines: "45-80", symbol_name: "run_sandboxed_tests", similarity_score: 0.88, snippet: "def run_sandboxed_tests(): ... execution bounded by memory and time caps" }
			]
		};
	}
};

export const fetchSponsorCompliance = async (submissionId) => {
	try {
		const res = await fetch(`${V1_BASE_URL}/evaluations/${submissionId}/compliance`, {
			headers: getAuthHeaders()
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		return await res.json();
	} catch (e) {
		return {
			submission_id: submissionId,
			total_tracks_evaluated: 3,
			compliant_tracks_count: 2,
			reports: [
				{ track_name: "Google Gemini API Integration", is_compliant: true, confidence_score: 0.91, evidence: [{ citation: "services/gemini.py:12-35", snippet: "from google.genai import Client" }] },
				{ track_name: "Razorpay Payment & Monetization", is_compliant: true, confidence_score: 0.89, evidence: [{ citation: "api/billing_service.py:15-50", snippet: "verify_payment_signature(order_id, payment_id, sig)" }] },
				{ track_name: "Redis Distributed Cache & Broker", is_compliant: false, confidence_score: 0.32, evidence: [] }
			]
		};
	}
};
