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
				className="card"
				style={{
					display: "flex",
					justifyContent: "space-between",
					alignItems: "center",
					padding: "1.25rem 1.5rem",
				}}
			>
				<h3 style={{ margin: 0, color: "var(--text-secondary)", fontSize: "0.95rem", fontWeight: 500 }}>
					{title}
				</h3>
				<StatusIndicator
					status={dimensionData ? dimensionData.status : "pending"}
				/>
			</div>
		);
	}

	// Handle the failed state
	if (dimensionData.status === "failed" || dimensionData.error_message) {
		return (
			<div
				className="card"
				style={{
					borderLeft: "3px solid var(--status-failed)",
					background: "var(--status-failed-bg)",
					padding: "1.25rem 1.5rem",
				}}
			>
				<div
					style={{
						display: "flex",
						justifyContent: "space-between",
						alignItems: "center",
						marginBottom: "0.75rem",
					}}
				>
					<h3 style={{ margin: 0, color: "var(--status-failed)", fontSize: "0.95rem", fontWeight: 600 }}>
						{title} - Failed
					</h3>
					<StatusIndicator status="failed" />
				</div>
				<p
					style={{
						color: "var(--text-secondary)",
						fontFamily: "var(--mono)",
						fontSize: "0.8125rem",
						lineHeight: "1.5",
					}}
				>
					{dimensionData.error_message || "Agent execution failed unexpectedly."}
				</p>
			</div>
		);
	}

	// Handle the complete/successful state
	return (
		<div className="card" style={{ padding: "1.5rem" }}>
			<div
				style={{
					display: "flex",
					justifyContent: "space-between",
					alignItems: "center",
					borderBottom: "1px solid var(--border-subtle)",
					paddingBottom: "1rem",
					marginBottom: "1rem",
				}}
			>
				<h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 600 }}>{title}</h3>
				<div
					style={{
						fontFamily: "var(--mono)",
						fontSize: "1.25rem",
						fontWeight: 600,
						color: "var(--text-primary)",
					}}
				>
					{dimensionData.score !== null ? dimensionData.score : "--"}{" "}
					<span
						style={{
							fontSize: "0.8rem",
							color: "var(--text-tertiary)",
							fontWeight: 400,
						}}
					>
						/ 100
					</span>
				</div>
			</div>

			<p
				style={{
					color: "var(--text-secondary)",
					marginBottom: "1.5rem",
					lineHeight: "1.5",
					fontSize: "0.875rem",
				}}
			>
				{dimensionData.summary}
			</p>

			{/* Render Flags (if any) */}
			{dimensionData.flags && dimensionData.flags.length > 0 && (
				<div style={{ marginBottom: "1.5rem" }}>
					<h4
						style={{
							color: "var(--status-running)",
							marginBottom: "0.5rem",
							fontSize: "0.75rem",
							fontWeight: 600,
							letterSpacing: "0.05em",
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
									background: "var(--status-running-bg)",
									border: "1px solid var(--status-running-border)",
									padding: "0.75rem 1rem",
									borderRadius: "var(--radius-sm)",
									fontSize: "0.8125rem",
									color: "var(--text-secondary)",
								}}
							>
								<strong
									style={{
										display: "block",
										marginBottom: "0.25rem",
										color: "var(--status-running)",
										fontSize: "0.8125rem",
									}}
								>
									{flag.type.replace(/_/g, " ").toUpperCase()}
								</strong>
								{flag.message}
								{flag.reference_id && (
									<a
										href={`/submission/${flag.reference_id}`}
										style={{
											display: "inline-flex",
											alignItems: "center",
											marginTop: "0.5rem",
											color: "var(--accent)",
											fontWeight: 500,
											fontSize: "0.75rem",
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
								color: "var(--text-tertiary)",
								marginBottom: "0.5rem",
								fontSize: "0.75rem",
								fontWeight: 600,
								letterSpacing: "0.05em",
							}}
						>
							Raw Metrics
						</h4>
						<div
							style={{
								display: "grid",
								gridTemplateColumns: "repeat(auto-fill, minmax(130px, 1fr))",
								gap: "0.75rem",
							}}
						>
							{Object.entries(dimensionData.raw_metrics).map(
								([key, value]) => (
									<div
										key={key}
										style={{
											background: "var(--bg-page)",
											border: "1px solid var(--border-subtle)",
											padding: "0.6rem 0.85rem",
											borderRadius: "var(--radius-sm)",
										}}
									>
										<div
											style={{
												fontSize: "0.6875rem",
												color: "var(--text-tertiary)",
												textTransform: "uppercase",
												letterSpacing: "0.05em",
												marginBottom: "0.25rem",
												wordBreak: "break-all",
											}}
										>
											{key.replace(/_/g, " ")}
										</div>
										<div
											style={{
												fontFamily: "var(--mono)",
												fontSize: "0.875rem",
												color: "var(--text-primary)",
												fontWeight: 500,
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
