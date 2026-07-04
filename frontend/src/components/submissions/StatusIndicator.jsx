export default function StatusIndicator({ status }) {
	const getStatusConfig = (currentStatus) => {
		switch (currentStatus) {
			case "complete":
				return {
					color: "var(--accent-green)",
					label: "Complete",
					bg: "rgba(57, 255, 20, 0.1)",
				};
			case "running":
				return {
					color: "var(--accent-cyan)",
					label: "Running",
					bg: "rgba(0, 229, 255, 0.1)",
				};
			case "failed":
				return {
					color: "var(--accent-red)",
					label: "Failed",
					bg: "rgba(255, 0, 85, 0.1)",
				};
			case "pending":
			default:
				return {
					color: "var(--text-secondary)",
					label: "Pending",
					bg: "rgba(138, 143, 152, 0.1)",
				};
		}
	};

	const config = getStatusConfig(status);

	return (
		<span
			style={{
				backgroundColor: config.bg,
				color: config.color,
				border: `1px solid ${config.color}`,
				padding: "0.25rem 0.75rem",
				borderRadius: "20px",
				fontSize: "0.75rem",
				fontWeight: 600,
				fontFamily: "var(--font-mono)",
				textTransform: "uppercase",
				display: "inline-flex",
				alignItems: "center",
				gap: "0.5rem",
			}}
		>
			{/* Optional: Add a pulsing dot for the 'running' state */}
			{status === "running" && (
				<span
					style={{
						width: "6px",
						height: "6px",
						backgroundColor: config.color,
						borderRadius: "50%",
						boxShadow: `0 0 5px ${config.color}`,
					}}
				></span>
			)}
			{config.label}
		</span>
	);
}
