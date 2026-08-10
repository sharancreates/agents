import { useState } from "react";

export default function RawJsonDebugger({ data }) {
	const [isOpen, setIsOpen] = useState(true);
	const [copied, setCopied] = useState(false);

	const handleCopy = async () => {
		try {
			await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
			setCopied(true);
			setTimeout(() => setCopied(false), 2000);
		} catch (err) {
			console.error("Failed to copy JSON to clipboard", err);
		}
	};

	return (
		<div
			className="card"
			style={{
				marginTop: "2rem",
				padding: 0,
				overflow: "hidden",
			}}
		>
			{/* Panel Header */}
			<div
				style={{
					display: "flex",
					justifyContent: "space-between",
					alignItems: "center",
					padding: "0.85rem 1.25rem",
					background: "rgba(255, 255, 255, 0.01)",
					borderBottom: isOpen ? "1px solid var(--border-subtle)" : "none",
					cursor: "pointer",
					userSelect: "none",
				}}
				onClick={() => setIsOpen(!isOpen)}
			>
				<div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
					<span
						style={{
							color: "var(--text-tertiary)",
							fontFamily: "var(--mono)",
							fontSize: "0.8rem",
							fontWeight: 600,
						}}
					>
						[DEBUG]
					</span>
					<span style={{ fontWeight: 500, fontSize: "0.875rem", color: "var(--text-secondary)" }}>
						Raw Agent Output Schema
					</span>
				</div>

				<div
					style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}
					onClick={(e) => e.stopPropagation()} // Prevent collapse when clicking buttons
				>
					<button
						onClick={handleCopy}
						className="btn btn-secondary"
						style={{
							padding: "0.25rem 0.6rem",
							fontSize: "0.75rem",
							fontWeight: 500,
							color: copied ? "var(--status-complete)" : "var(--text-secondary)",
							borderColor: copied ? "var(--status-complete-border)" : "var(--border-subtle)",
							backgroundColor: copied ? "var(--status-complete-bg)" : "transparent",
						}}
					>
						{copied ? "✓ Copied" : "Copy JSON"}
					</button>

					<span
						style={{
							color: "var(--text-tertiary)",
							fontSize: "0.75rem",
							transform: isOpen ? "rotate(0deg)" : "rotate(180deg)",
							transition: "transform var(--transition)",
							cursor: "pointer",
							padding: "0.25rem",
						}}
						onClick={() => setIsOpen(!isOpen)}
					>
						▼
					</span>
				</div>
			</div>

			{/* JSON Preformatted Block */}
			{isOpen && (
				<div style={{ padding: "1.25rem", background: "var(--bg-page)" }}>
					<pre
						style={{
							margin: 0,
							whiteSpace: "pre-wrap",
							wordBreak: "break-all",
							fontFamily: "var(--mono)",
							fontSize: "0.8125rem",
							lineHeight: "1.5",
							color: "var(--text-secondary)",
							maxHeight: "350px",
							overflowY: "auto",
							textAlign: "left",
						}}
					>
						{JSON.stringify(data, null, 2)}
					</pre>
				</div>
			)}
		</div>
	);
}
