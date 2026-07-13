export default function StatusIndicator({ status }) {
	const getBadgeClass = (currentStatus) => {
		switch (currentStatus) {
			case "complete":
				return "badge badge-complete";
			case "running":
				return "badge badge-running";
			case "failed":
				return "badge badge-failed";
			case "pending":
			default:
				return "badge badge-pending";
		}
	};

	const getLabel = (currentStatus) => {
		switch (currentStatus) {
			case "complete":
				return "Complete";
			case "running":
				return "Running";
			case "failed":
				return "Failed";
			case "pending":
			default:
				return "Pending";
		}
	};

	return (
		<span className={getBadgeClass(status)}>
			{status === "running" && (
				<span
					className="animate-pulse"
					style={{
						width: "5px",
						height: "5px",
						backgroundColor: "var(--status-running)",
						borderRadius: "50%",
						display: "inline-block",
					}}
				></span>
			)}
			{getLabel(status)}
		</span>
	);
}
