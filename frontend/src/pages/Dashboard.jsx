import { useSubmissions } from "../hooks/useSubmissions";
import SubmissionList from "../components/submissions/SubmissionList";

export default function Dashboard() {
	const { submissions, isLoading, error } = useSubmissions();

	return (
		<div style={{ width: "100%" }}>
			<header
				style={{
					display: "flex",
					justifyContent: "space-between",
					alignItems: "center",
					marginBottom: "2rem",
					borderBottom: "1px solid var(--border-subtle)",
					paddingBottom: "1.25rem",
				}}
			>
				<div>
					<h1>Evaluation Queue</h1>
					<p style={{ marginTop: "0.25rem" }}>
						Monitor automated agent analysis in real-time.
					</p>
				</div>
				<div
					style={{
						fontSize: "0.875rem",
						color: "var(--text-secondary)",
						backgroundColor: "var(--bg-element)",
						padding: "0.35rem 0.75rem",
						borderRadius: "var(--radius-sm)",
						border: "1px solid var(--border-subtle)",
					}}
				>
					<span style={{ color: "var(--text-tertiary)" }}>Total Submissions: </span>
					<span style={{ fontFamily: "var(--mono)", fontWeight: 500, color: "var(--text-primary)" }}>
						{submissions.length}
					</span>
				</div>
			</header>

			{/* Handle Loading State */}
			{isLoading && (
				<div
					style={{
						display: "flex",
						flexDirection: "column",
						alignItems: "center",
						justifyContent: "center",
						padding: "6rem 2rem",
						color: "var(--text-secondary)",
					}}
				>
					<div
						className="animate-spin"
						style={{
							width: "24px",
							height: "24px",
							border: "2px solid var(--border-muted)",
							borderTopColor: "var(--accent)",
							borderRadius: "50%",
							marginBottom: "1rem",
						}}
					></div>
					<p style={{ fontFamily: "var(--mono)", fontSize: "0.8rem" }}>
						Fetching queue data...
					</p>
				</div>
			)}

			{/* Handle Error State */}
			{error && (
				<div
					className="card"
					style={{
						borderLeft: "4px solid var(--status-failed)",
						padding: "1.5rem",
						color: "var(--status-failed)",
						background: "var(--status-failed-bg)",
					}}
				>
					<p style={{ fontFamily: "var(--mono)", fontWeight: 500 }}>
						SYSTEM ERROR: {error}
					</p>
				</div>
			)}

			{/* Render Data */}
			{!isLoading && !error && (
				<SubmissionList submissions={submissions} />
			)}
		</div>
	);
}
