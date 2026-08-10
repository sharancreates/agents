import React, { useState } from "react";

export default function ParticipantFeedback({ feedbackData, teamName }) {
	const [isExposed, setIsExposed] = useState(true);

	if (!feedbackData || feedbackData.status === "pending") {
		return (
			<div
				className="glass-panel"
				style={{ padding: "1.5rem", marginBottom: "1.5rem", borderRadius: "12px" }}
				role="region"
				aria-label="Participant Feedback Pending"
			>
				<h3 style={{ fontSize: "1.1rem", color: "var(--text-primary)", marginBottom: "0.5rem" }}>
					💬 Participant-Facing Commentary (Feedback Agent)
				</h3>
				<p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
					Feedback commentary is currently generating. It will unlock once all agent evaluation reports are completed.
				</p>
			</div>
		);
	}

	const { commentary, strengths = [], improvements = [] } = feedbackData;

	return (
		<div
			className="glass-panel"
			style={{
				padding: "1.75rem",
				marginBottom: "1.75rem",
				borderRadius: "14px",
				borderLeft: isExposed ? "4px solid #10b981" : "4px solid #f59e0b",
			}}
			role="region"
			aria-label="Participant Feedback Commentary"
		>
			<div
				style={{
					display: "flex",
					justifyContent: "space-between",
					alignItems: "center",
					marginBottom: "1.25rem",
					flexWrap: "wrap",
					gap: "0.75rem",
				}}
			>
				<div>
					<div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
						<h3
							style={{
								fontSize: "1.15rem",
								fontWeight: 700,
								color: "var(--text-primary)",
								margin: 0,
							}}
						>
							💬 Participant-Facing Commentary
						</h3>
						<span
							style={{
								fontSize: "0.75rem",
								padding: "0.2rem 0.55rem",
								borderRadius: "20px",
								background: isExposed ? "rgba(16, 185, 129, 0.15)" : "rgba(245, 158, 11, 0.15)",
								color: isExposed ? "#10b981" : "#f59e0b",
								fontWeight: 600,
							}}
						>
							{isExposed ? "Participant Visible" : "Judge-Only Mode"}
						</span>
					</div>
					<p style={{ color: "var(--text-muted)", fontSize: "0.825rem", marginTop: "0.25rem", margin: 0 }}>
						Lighter-weight feedback pass generated specifically for participant growth (decoupled from internal scoring rules).
					</p>
				</div>

				{/* Admin Platform Visibility Toggle */}
				<button
					onClick={() => setIsExposed(!isExposed)}
					aria-label={isExposed ? "Hide feedback from participants" : "Expose feedback to participants"}
					aria-pressed={isExposed}
					style={{
						background: isExposed ? "var(--surface-hover)" : "var(--primary-color)",
						color: isExposed ? "var(--text-primary)" : "#ffffff",
						border: "1px solid var(--border-color)",
						borderRadius: "8px",
						padding: "0.45rem 0.9rem",
						fontSize: "0.825rem",
						fontWeight: 600,
						cursor: "pointer",
						transition: "all 0.2s ease",
					}}
				>
					{isExposed ? "🔒 Switch to Judge-Only" : "👁️ Expose to Participants"}
				</button>
			</div>

			{isExposed ? (
				<div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
					{/* Main Commentary Statement */}
					<div
						style={{
							background: "rgba(255, 255, 255, 0.03)",
							border: "1px solid var(--border-color)",
							borderRadius: "10px",
							padding: "1rem 1.25rem",
							color: "var(--text-primary)",
							fontSize: "0.925rem",
							lineHeight: "1.5",
						}}
					>
						{commentary.replace(/\*\*/g, "")}
					</div>

					<div
						style={{
							display: "grid",
							gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
							gap: "1.25rem",
						}}
					>
						{/* Strengths Card */}
						<div
							style={{
								background: "rgba(16, 185, 129, 0.05)",
								border: "1px solid rgba(16, 185, 129, 0.2)",
								borderRadius: "10px",
								padding: "1rem 1.15rem",
							}}
						>
							<h4
								style={{
									fontSize: "0.9rem",
									color: "#10b981",
									fontWeight: 700,
									marginBottom: "0.6rem",
									display: "flex",
									alignItems: "center",
									gap: "0.4rem",
								}}
							>
								🌟 Key Accomplishments
							</h4>
							<ul style={{ margin: 0, paddingLeft: "1.2rem", color: "var(--text-primary)", fontSize: "0.875rem" }}>
								{strengths.map((item, idx) => (
									<li key={idx} style={{ marginBottom: "0.35rem" }}>
										{item}
									</li>
								))}
							</ul>
						</div>

						{/* Improvements Card */}
						<div
							style={{
								background: "rgba(99, 102, 241, 0.05)",
								border: "1px solid rgba(99, 102, 241, 0.2)",
								borderRadius: "10px",
								padding: "1rem 1.15rem",
							}}
						>
							<h4
								style={{
									fontSize: "0.9rem",
									color: "#6366f1",
									fontWeight: 700,
									marginBottom: "0.6rem",
									display: "flex",
									alignItems: "center",
									gap: "0.4rem",
								}}
							>
								🚀 Growth Opportunities
							</h4>
							<ul style={{ margin: 0, paddingLeft: "1.2rem", color: "var(--text-primary)", fontSize: "0.875rem" }}>
								{improvements.map((item, idx) => (
									<li key={idx} style={{ marginBottom: "0.35rem" }}>
										{item}
									</li>
								))}
							</ul>
						</div>
					</div>
				</div>
			) : (
				<div
					style={{
						padding: "1rem",
						background: "rgba(245, 158, 11, 0.08)",
						borderRadius: "8px",
						color: "#f59e0b",
						fontSize: "0.875rem",
					}}
				>
					🔒 <strong>Participant Feedback Hidden:</strong> Platform visibility is set to Judge-Only. Participants viewing this report will not see these commentary cards until enabled by an admin.
				</div>
			)}
		</div>
	);
}
