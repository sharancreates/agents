import { useState, useEffect } from 'react';
import { fetchSubmissions } from '../services/api';

export function useSubmissions(pollingIntervalMs = 3000) {
  const [submissions, setSubmissions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    let timerId = null;

    const loadData = async () => {
      try {
        const data = await fetchSubmissions();
        
        if (isMounted) {
          setSubmissions(data);
          setError(null);
          setIsLoading(false);

          // Check if any submission is still being processed
          const needsPolling = data.some(
            (sub) => sub.pipeline_status === 'pending' || sub.pipeline_status === 'running'
          );

          // If agents are still running, schedule the next fetch
          if (needsPolling) {
            timerId = setTimeout(loadData, pollingIntervalMs);
          }
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || "Failed to connect to orchestrator");
          setIsLoading(false);
          // Optional: Retry after a delay even if it fails, in case P1's server is restarting
          timerId = setTimeout(loadData, pollingIntervalMs * 2);
        }
      }
    };

    // Kick off the initial fetch
    loadData();

    // Cleanup function: kill the timer if the user navigates away from the page
    return () => {
      isMounted = false;
      if (timerId) {
        clearTimeout(timerId);
      }
    };
  }, [pollingIntervalMs]);

  return { submissions, isLoading, error };
}