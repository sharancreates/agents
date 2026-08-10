import SubmissionCard from "./SubmissionCard";

export default function SubmissionList({ submissions }) {
	if (!submissions || submissions.length === 0) {
		return (
			<div
				className="card"
				style={{
					padding: "4rem 2rem",
					textAlign: "center",
					color: "var(--text-secondary)",
				}}
			>
				<p style={{ fontFamily: "var(--mono)", fontSize: "0.85rem" }}>
					NO SUBMISSIONS FOUND IN THE EVALUATION QUEUE
				</p>
			</div>
		);
	}

	return (
		<div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
			{/* Alignment headers that match the columns in SubmissionCard */}
			<div
				style={{
					display: "grid",
					gridTemplateColumns: "1.5fr 2fr 1.2fr 1fr",
					alignItems: "center",
					gap: "1.5rem",
					padding: "0.5rem 1.25rem",
					fontSize: "0.75rem",
					fontWeight: 500,
					color: "var(--text-tertiary)",
					textTransform: "uppercase",
					letterSpacing: "0.05em",
				}}
			>
				<div>Team & ID</div>
				<div>Repository</div>
				<div>Pipeline Status</div>
				<div style={{ textAlign: "right" }}>Composite Score</div>
			</div>

			<div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
				{submissions.map((sub) => (
					<SubmissionCard key={sub.submission_id} submission={sub} />
				))}
			</div>
		</div>
	);
}