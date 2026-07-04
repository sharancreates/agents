import DimensionScore from "./DimensionScore";

export default function ReportContainer({ submission }) {
	return (
		<div
			style={{
				display: "grid",
				gridTemplateColumns: "1fr 1fr",
				gap: "2rem",
				marginTop: "2rem",
			}}
		>
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
						fontSize: "1.2rem",
						color: "var(--text-secondary)",
						borderBottom: "1px solid var(--glass-border)",
						paddingBottom: "0.5rem",
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
						fontSize: "1.2rem",
						color: "var(--text-secondary)",
						borderBottom: "1px solid var(--glass-border)",
						paddingBottom: "0.5rem",
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
