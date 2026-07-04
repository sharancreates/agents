import { useSubmissions } from "../hooks/useSubmissions";
import SubmissionList from "../components/submissions/SubmissionList";

export default function Dashboard() {
	const { submissions, isLoading, error } = useSubmissions();

	return (
		<div style={{ maxWidth: "1200px", margin: "0 auto", width: "100%" }}>
			<header
				style={{
					display: "flex",
					justifyContent: "space-between",
					alignItems: "flex-end",
					marginBottom: "2rem",
				}}
			>
				<div>
					<h1 style={{ marginBottom: "0.5rem" }}>Evaluation Queue</h1>
					<p style={{ color: "var(--text-secondary)" }}>
						Monitor automated agent analysis in real-time.
					</p>
				</div>
				<div
					style={{
						fontFamily: "var(--font-mono)",
						color: "var(--accent-cyan)",
					}}
				>
					Total Submissions: {submissions.length}
				</div>
			</header>

			{/* Handle Loading State */}
			{isLoading && (
				<div
					style={{
						textAlign: "center",
						padding: "4rem",
						color: "var(--text-secondary)",
						fontFamily: "var(--font-mono)",
					}}
				>
					<div
						style={{
							display: "inline-block",
							width: "20px",
							height: "20px",
							border: "2px solid var(--accent-cyan)",
							borderTopColor: "transparent",
							borderRadius: "50%",
							animation: "spin 1s linear infinite",
							marginBottom: "1rem",
						}}
					></div>
					<p>Fetching queue data...</p>
					<style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
				</div>
			)}

			{/* Handle Error State */}
			{error && (
				<div
					className="glass-panel"
					style={{
						border: "1px solid var(--accent-red)",
						padding: "2rem",
						textAlign: "center",
						color: "var(--accent-red)",
					}}
				>
					<p>SYSTEM ERROR: {error}</p>
				</div>
			)}

			{/* Render Data */}
			{!isLoading && !error && (
				<SubmissionList submissions={submissions} />
			)}
		</div>
	);
}
