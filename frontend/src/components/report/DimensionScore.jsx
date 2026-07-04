import StatusIndicator from "../submissions/StatusIndicator";

export default function DimensionScore({ title, dimensionData }) {
	// Handle the pending/running state
	if (
		!dimensionData ||
		dimensionData.status === "pending" ||
		dimensionData.status === "running"
	) {
		return (
			<div
				className="glass-panel"
				style={{
					padding: "1.5rem",
					display: "flex",
					justifyContent: "space-between",
					alignItems: "center",
				}}
			>
				<h3 style={{ margin: 0, color: "var(--text-secondary)" }}>
					{title}
				</h3>
				<StatusIndicator
					status={dimensionData ? dimensionData.status : "pending"}
				/>
			</div>
		);
	}

	// Handle the catastrophic failure state (using the error_message we fought for in the schema sync!)
	if (dimensionData.status === "failed" || dimensionData.error_message) {
		return (
			<div
				className="glass-panel"
				style={{
					padding: "1.5rem",
					borderLeft: "4px solid var(--accent-red)",
				}}
			>
				<div
					style={{
						display: "flex",
						justifyContent: "space-between",
						marginBottom: "1rem",
					}}
				>
					<h3 style={{ margin: 0, color: "var(--accent-red)" }}>
						{title} - Failed
					</h3>
					<StatusIndicator status="failed" />
				</div>
				<p
					style={{
						color: "var(--text-secondary)",
						fontFamily: "var(--font-mono)",
						fontSize: "0.9rem",
					}}
				>
					{dimensionData.error_message ||
						"Agent execution failed unexpectedly."}
				</p>
			</div>
		);
	}

	// Handle the complete/successful state
	return (
		<div className="glass-panel" style={{ padding: "1.5rem" }}>
			<div
				style={{
					display: "flex",
					justifyContent: "space-between",
					borderBottom: "1px solid var(--glass-border)",
					paddingBottom: "1rem",
					marginBottom: "1rem",
				}}
			>
				<h3 style={{ margin: 0 }}>{title}</h3>
				<div
					style={{
						fontFamily: "var(--font-mono)",
						fontSize: "1.5rem",
						fontWeight: 700,
						color: "var(--accent-cyan)",
					}}
				>
					{dimensionData.score !== null ? dimensionData.score : "--"}{" "}
					<span
						style={{
							fontSize: "0.85rem",
							color: "var(--text-secondary)",
						}}
					>
						/ 100
					</span>
				</div>
			</div>

			<p
				style={{
					color: "var(--text-primary)",
					marginBottom: "1.5rem",
					lineHeight: "1.5",
				}}
			>
				{dimensionData.summary}
			</p>

			{/* Render Flags (if any) */}
			{dimensionData.flags && dimensionData.flags.length > 0 && (
				<div style={{ marginBottom: "1.5rem" }}>
					<h4
						style={{
							color: "var(--accent-yellow)",
							marginBottom: "0.5rem",
							fontSize: "0.85rem",
							textTransform: "uppercase",
						}}
					>
						⚠ Flags Detected
					</h4>
					<ul
						style={{
							listStyle: "none",
							padding: 0,
							margin: 0,
							display: "flex",
							flexDirection: "column",
							gap: "0.5rem",
						}}
					>
						{dimensionData.flags.map((flag, idx) => (
							<li
								key={idx}
								style={{
									background: "rgba(255, 234, 0, 0.1)",
									border: "1px solid var(--accent-yellow)",
									padding: "0.75rem",
									borderRadius: "4px",
									fontSize: "0.85rem",
								}}
							>
								<strong
									style={{
										display: "block",
										marginBottom: "0.25rem",
									}}
								>
									{flag.type}
								</strong>
								{flag.message}
								{flag.reference_id && (
									<a
										href={`/submission/${flag.reference_id}`}
										style={{
											display: "block",
											marginTop: "0.5rem",
											color: "var(--accent-cyan)",
											textDecoration: "none",
										}}
									>
										View Referenced Submission ➔
									</a>
								)}
							</li>
						))}
					</ul>
				</div>
			)}

			{/* Render Raw Metrics Grid */}
			{dimensionData.raw_metrics &&
				Object.keys(dimensionData.raw_metrics).length > 0 && (
					<div>
						<h4
							style={{
								color: "var(--text-secondary)",
								marginBottom: "0.5rem",
								fontSize: "0.85rem",
								textTransform: "uppercase",
							}}
						>
							Raw Metrics
						</h4>
						<div
							style={{
								display: "grid",
								gridTemplateColumns:
									"repeat(auto-fill, minmax(150px, 1fr))",
								gap: "1rem",
							}}
						>
							{Object.entries(dimensionData.raw_metrics).map(
								([key, value]) => (
									<div
										key={key}
										style={{
											background: "rgba(0,0,0,0.3)",
											padding: "0.75rem",
											borderRadius: "4px",
										}}
									>
										<div
											style={{
												fontSize: "0.7rem",
												color: "var(--text-secondary)",
												marginBottom: "0.25rem",
												wordBreak: "break-all",
											}}
										>
											{key
												.toUpperCase()
												.replace(/_/g, " ")}
										</div>
										<div
											style={{
												fontFamily: "var(--font-mono)",
												fontSize: "1rem",
												color: "var(--text-primary)",
											}}
										>
											{Array.isArray(value)
												? value.join(", ")
												: String(value)}
										</div>
									</div>
								),
							)}
						</div>
					</div>
				)}
		</div>
	);
}
