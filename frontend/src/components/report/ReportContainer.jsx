import DimensionScore from "./DimensionScore";

export default function ReportContainer({ submission }) {
	return (
		<div className="details-grid">
			{/* Left Column: Code Analysis */}
			<div
				style={{
					display: "flex",
					flexDirection: "column",
					gap: "1.5rem",
				}}
			>
				<h2
					style={{
						fontSize: "1.1rem",
						fontWeight: 600,
						color: "var(--text-primary)",
						borderBottom: "1px solid var(--border-subtle)",
						paddingBottom: "0.75rem",
						marginBottom: "0.25rem",
					}}
				>
					Static & Dynamic Analysis
				</h2>
				<DimensionScore
					title="Code Quality"
					dimensionData={submission.code_quality}
				/>
				<DimensionScore
					title="Functionality Sandbox"
					dimensionData={submission.functionality}
				/>
			</div>

			{/* Right Column: AI & Heuristics */}
			<div
				style={{
					display: "flex",
					flexDirection: "column",
					gap: "1.5rem",
				}}
			>
				<h2
					style={{
						fontSize: "1.1rem",
						fontWeight: 600,
						color: "var(--text-primary)",
						borderBottom: "1px solid var(--border-subtle)",
						paddingBottom: "0.75rem",
						marginBottom: "0.25rem",
					}}
				>
					Originality & Innovation
				</h2>
				<DimensionScore
					title="Originality Check"
					dimensionData={submission.originality}
				/>
				<DimensionScore
					title="Innovation Agent"
					dimensionData={submission.innovation}
				/>
			</div>
		</div>
	);
}
