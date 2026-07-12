import { useState, useEffect } from "react";
import { fetchSubmissionById } from "../services/api";

export function useSubmissionDetail(id, pollingIntervalMs = 3000) {
	const [submission, setSubmission] = useState(null);
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState(null);

	useEffect(() => {
		if (!id) return;

		let isMounted = true;
		let timerId = null;

		const loadData = async () => {
			try {
				const data = await fetchSubmissionById(id);

				if (isMounted) {
					setSubmission(data);
					setError(null);
					setIsLoading(false);

					// Keep polling if this specific submission is not yet finished
					if (
						data.pipeline_status === "pending" ||
						data.pipeline_status === "running"
					) {
						timerId = setTimeout(loadData, pollingIntervalMs);
					}
				}
			} catch (err) {
				if (isMounted) {
					setError(
						err.message || "Failed to fetch submission details",
					);
					setIsLoading(false);
					timerId = setTimeout(loadData, pollingIntervalMs * 2);
				}
			}
		};

		loadData();

		return () => {
			isMounted = false;
			if (timerId) clearTimeout(timerId);
		};
	}, [id, pollingIntervalMs]);

	return { submission, isLoading, error };
}
