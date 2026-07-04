import { useState, useEffect } from "react";
import { fetchSubmissions } from "../services/api";

export function useSubmissions() {
	const [submissions, setSubmissions] = useState([]);
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState(null);

	useEffect(() => {
		let isMounted = true;

		const loadData = async () => {
			try {
				setIsLoading(true);
				const data = await fetchSubmissions();
				if (isMounted) {
					setSubmissions(data);
					setError(null);
				}
			} catch (err) {
				if (isMounted) {
					setError(err.message || "Failed to fetch submissions");
				}
			} finally {
				if (isMounted) {
					setIsLoading(false);
				}
			}
		};

		loadData();

		// Cleanup function to prevent memory leaks if the component unmounts
		return () => {
			isMounted = false;
		};
	}, []);

	return { submissions, isLoading, error };
}
