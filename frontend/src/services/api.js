import mockSubmissions from "../mockData/submissions.json";

export const fetchSubmissions = async () => {
	// Simulate an 800ms network delay to mimic the real FastAPI backend
	return new Promise((resolve) => {
		setTimeout(() => {
			resolve(mockSubmissions);
		}, 800);
	});
};

export const fetchSubmissionById = async (id) => {
	return new Promise((resolve, reject) => {
		setTimeout(() => {
			const submission = mockSubmissions.find(
				(sub) => sub.submission_id === id,
			);
			if (submission) {
				resolve(submission);
			} else {
				reject(new Error("Submission not found"));
			}
		}, 500);
	});
};

// The base URL for Person 1's FastAPI orchestrator
const API_BASE_URL = "http://localhost:8000/api";

export const fetchSubmissions = async () => {
	const response = await fetch(`${API_BASE_URL}/submissions`);
	if (!response.ok) {
		throw new Error(`API Error: ${response.status} ${response.statusText}`);
	}
	return response.json();
};

export const fetchSubmissionById = async (id) => {
	// Assuming P1 built the specific endpoint for the detail view
	const response = await fetch(`${API_BASE_URL}/submissions/${id}/status`);
	if (!response.ok) {
		throw new Error(`API Error: ${response.status} ${response.statusText}`);
	}
	return response.json();
};
