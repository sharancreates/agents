import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchSubmissionById } from "../services/api";
import ReportContainer from "../components/report/ReportContainer";
import StatusIndicator from "../components/submissions/StatusIndicator";

export default function SubmissionDetail() {
	const { id } = useParams();
	const [submission, setSubmission] = useState(null);
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState(null);

	useEffect(() => {
		let isMounted = true;
		const loadData = async () => {
			try {
				setIsLoading(true);
				const data = await fetchSubmissionById(id);
				if (isMounted) {
					setSubmission(data);
					setError(null);
				}
			} catch (err) {
				if (isMounted) setError(err.message);
			} finally {
				if (isMounted) setIsLoading(false);
			}
		};
		loadData();
		return () => {
			isMounted = false;
		};
	}, [id]);

	if (isLoading)
		return (
			<div
				style={{
					color: "var(--accent-cyan)",
					fontFamily: "var(--font-mono)",
					textAlign: "center",
					padding: "4rem",
				}}
			>
				Compiling report data...
			</div>
		);
	if (error)
		return (
			<div
				style={{
					color: "var(--accent-red)",
					textAlign: "center",
					padding: "4rem",
				}}
			>
				Error: {error}
			</div>
		);
	if (!submission) return null;

	return (
		<div style={{ maxWidth: "1200px", margin: "0 auto", width: "100%" }}>
			<Link
				to="/"
				style={{
					color: "var(--text-secondary)",
					textDecoration: "none",
					display: "inline-block",
					marginBottom: "2rem",
				}}
			>
				← Back to Queue
			</Link>

			<header
				className="glass-panel"
				style={{
					padding: "2rem",
					display: "flex",
					justifyContent: "space-between",
					alignItems: "center",
				}}
			>
				<div>
					<div
						style={{
							display: "flex",
							gap: "1rem",
							alignItems: "center",
							marginBottom: "0.5rem",
						}}
					>
						<h1 style={{ margin: 0 }}>{submission.team_name}</h1>
						<StatusIndicator status={submission.pipeline_status} />
					</div>
					<div
						style={{
							color: "var(--text-secondary)",
							fontFamily: "var(--font-mono)",
						}}
					>
						ID: {submission.submission_id} |{" "}
						<a
							href={submission.repo_url}
							target="_blank"
							rel="noreferrer"
							style={{ color: "var(--accent-cyan)" }}
						>
							View Repository
						</a>
					</div>
				</div>

				<div style={{ textAlign: "right" }}>
					<div
						style={{
							fontSize: "0.85rem",
							color: "var(--text-secondary)",
							textTransform: "uppercase",
							letterSpacing: "1px",
							marginBottom: "0.25rem",
						}}
					>
						Overall Synthesis Score
					</div>
					<div
						style={{
							fontFamily: "var(--font-mono)",
							fontSize: "2.5rem",
							fontWeight: 800,
							color: "var(--accent-green)",
						}}
					>
						{submission.overall_score !== null
							? submission.overall_score
							: "--"}
					</div>
				</div>
			</header>

			<ReportContainer submission={submission} />
		</div>
	);
}
