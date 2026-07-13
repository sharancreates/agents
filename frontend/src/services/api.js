import mockSubmissions from "../mockData/submissions.json";

// The base URL for Person 1's FastAPI orchestrator
const API_BASE_URL = "http://localhost:8000/api";

/**
 * Helper to simulate a network delay when returning mock data
 */
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

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
			"FastAPI backend connection failed. Falling back to local mock data.",
			err.message,
		);
		// Simulate network latency for mock data to keep the loading states visible
		await delay(800);
		return mockSubmissions;
	}
};

export const fetchSubmissionById = async (id) => {
	try {
		// Attempting P1's status detail endpoint
		const response = await fetch(`${API_BASE_URL}/submissions/${id}/status`);
		if (!response.ok) {
			throw new Error(`API Error: ${response.status} ${response.statusText}`);
		}
		const data = await response.json();
		console.log(`Successfully fetched details for ${id} from live API`);
		return data;
	} catch (err) {
		console.warn(
			`FastAPI backend connection failed for submission ${id}. Falling back to local mock data.`,
			err.message,
		);
		await delay(500);
		const submission = mockSubmissions.find((sub) => sub.submission_id === id);
		if (submission) {
			return submission;
		} else {
			throw new Error("Submission not found", { cause: err });
		}
	}
};
