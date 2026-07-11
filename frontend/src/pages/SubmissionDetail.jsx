import { useParams, Link } from "react-router-dom";
import { useSubmissionDetail } from "../hooks/useSubmissionDetail";
import StatusIndicator from "../components/submissions/StatusIndicator";
import RawJsonDebugger from "../components/report/RawJsonDebugger";
import ReportContainer from "../components/report/ReportContainer";

export default function SubmissionDetail() {
	const { id } = useParams();

	// Using the new live-polling hook!
	const { submission, isLoading, error } = useSubmissionDetail(id);

	if (isLoading && !submission) {
		return (
			<div
				style={{
					color: "#82B3C9",
					fontFamily: "var(--font-mono)",
					textAlign: "center",
					padding: "4rem",
				}}
			>
				Establishing secure connection...
			</div>
		);
	}

	if (error) {
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
	}

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
							style={{ color: "#82B3C9" }}
						>
							View Repository
						</a>
					</div>
				</div>
			</header>

			{/* The structured evaluation report */}
			<ReportContainer submission={submission} />

			{/* The raw data view for P2 and P3 to debug their agents */}
			<RawJsonDebugger data={submission} />
		</div>
	);
}
