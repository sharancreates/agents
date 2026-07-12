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
			className="glass-panel"
			style={{
				marginTop: "2rem",
				border: "1px solid var(--glass-border)",
				overflow: "hidden",
				transition: "max-height 0.3s ease-in-out",
			}}
		>
			{/* Panel Header */}
			<div
				style={{
					display: "flex",
					justifyContent: "space-between",
					alignItems: "center",
					padding: "1rem 1.5rem",
					background: "rgba(255, 255, 255, 0.03)",
					borderBottom: "1px solid var(--glass-border)",
					cursor: "pointer",
					userSelect: "none",
				}}
				onClick={() => setIsOpen(!isOpen)}
			>
				<div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
					<span
						style={{
							color: "var(--accent-cyan)",
							fontFamily: "var(--font-mono)",
							fontSize: "0.9rem",
							fontWeight: "bold",
						}}
					>
						[DEBUG]
					</span>
					<span style={{ fontWeight: 600, fontSize: "0.95rem" }}>
						Raw Agent Output Schema
					</span>
				</div>

				<div
					style={{ display: "flex", alignItems: "center", gap: "1rem" }}
					onClick={(e) => e.stopPropagation()} // Prevent collapse when clicking buttons
				>
					<button
						onClick={handleCopy}
						style={{
							background: "transparent",
							border: "1px solid var(--glass-border)",
							color: copied ? "var(--accent-green)" : "var(--text-secondary)",
							padding: "0.3rem 0.75rem",
							borderRadius: "4px",
							fontSize: "0.75rem",
							fontFamily: "var(--font-mono)",
							cursor: "pointer",
							transition: "all 0.2s",
						}}
						onMouseEnter={(e) => {
							e.target.style.borderColor = copied
								? "var(--accent-green)"
								: "var(--accent-cyan)";
							e.target.style.color = copied
								? "var(--accent-green)"
								: "var(--text-primary)";
						}}
						onMouseLeave={(e) => {
							e.target.style.borderColor = "var(--glass-border)";
							e.target.style.color = copied
								? "var(--accent-green)"
								: "var(--text-secondary)";
						}}
					>
						{copied ? "✓ COPIED" : "COPY JSON"}
					</button>

					<span
						style={{
							color: "var(--text-secondary)",
							fontSize: "0.8rem",
							transform: isOpen ? "rotate(0deg)" : "rotate(180deg)",
							transition: "transform 0.2s",
							cursor: "pointer",
						}}
						onClick={() => setIsOpen(!isOpen)}
					>
						▼
					</span>
				</div>
			</div>

			{/* JSON Preformatted Block */}
			{isOpen && (
				<div style={{ padding: "1.5rem", background: "rgba(0, 0, 0, 0.4)" }}>
					<pre
						style={{
							margin: 0,
							whiteSpace: "pre-wrap",
							wordBreak: "break-all",
							fontFamily: "var(--font-mono)",
							fontSize: "0.85rem",
							lineHeight: "1.5",
							color: "#a9b2c3",
							maxHeight: "450px",
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
