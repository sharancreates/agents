import SubmissionCard from "./SubmissionCard";

export default function SubmissionList({ submissions }) {
	if (!submissions || submissions.length === 0) {
		return (
			<div
				className="glass-panel"
				style={{
					padding: "3rem 2rem",
					textAlign: "center",
					border: "1px solid var(--glass-border)",
				}}
			>
				<p style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}>
					NO SUBMISSIONS FOUND IN THE EVALUATION QUEUE
				</p>
			</div>
		);
	}

	return (
		<div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
			{submissions.map((sub) => (
				<SubmissionCard key={sub.submission_id} submission={sub} />
			))}
		</div>
	);
}