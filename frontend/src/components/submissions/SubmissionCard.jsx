import { Link } from "react-router-dom";
import StatusIndicator from "./StatusIndicator";
import { calculateSynthesisScore } from "../../utils/synthesisAgent";

export default function SubmissionCard({ submission }) {
	const liveScore = calculateSynthesisScore(submission);
	
	const formattedTime = new Date(submission.submitted_at).toLocaleString([], {
		month: "short",
		day: "numeric",
		hour: "2-digit",
		minute: "2-digit",
	});

	return (
		<Link
			to={`/submission/${submission.submission_id}`}
			className="glass-panel"
			style={{
				padding: "1.5rem 2rem",
				textDecoration: "none",
				color: "inherit",
				display: "grid",
				gridTemplateColumns: "1.5fr 2fr 1.2fr 1fr",
				alignItems: "center",
				gap: "1.5rem",
				transition: "transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.25s, box-shadow 0.25s",
				cursor: "pointer",
				border: "1px solid var(--glass-border)",
				position: "relative",
				overflow: "hidden",
			}}
			onMouseEnter={(e) => {
				e.currentTarget.style.transform = "translateY(-3px)";
				e.currentTarget.style.borderColor = "rgba(0, 229, 255, 0.25)";
				e.currentTarget.style.boxShadow = "0 10px 25px rgba(0, 0, 0, 0.4), 0 0 15px rgba(0, 229, 255, 0.05)";
				e.currentTarget.style.backgroundColor = "rgba(25, 25, 30, 0.85)";
			}}
			onMouseLeave={(e) => {
				e.currentTarget.style.transform = "translateY(0)";
				e.currentTarget.style.borderColor = "var(--glass-border)";
				e.currentTarget.style.boxShadow = "none";
				e.currentTarget.style.backgroundColor = "var(--glass-panel)";
			}}
		>
			{/* Left Column: Team info & Time */}
			<div>
				<h3 style={{ margin: "0 0 0.4rem 0", fontSize: "1.1rem", fontWeight: 700 }}>
					{submission.team_name}
				</h3>
				<div
					style={{
						display: "flex",
						flexDirection: "column",
						gap: "0.2rem",
					}}
				>
					<span
						style={{
							color: "var(--text-secondary)",
							fontSize: "0.75rem",
							fontFamily: "var(--font-mono)",
						}}
					>
						ID: {submission.submission_id}
					</span>
					<span style={{ color: "var(--text-secondary)", fontSize: "0.75rem" }}>
						{formattedTime}
					</span>
				</div>
			</div>

			{/* Center-Left Column: Repository Link */}
			<div
				style={{
					color: "#82B3C9",
					fontSize: "0.85rem",
					fontFamily: "var(--font-mono)",
					overflow: "hidden",
					textOverflow: "ellipsis",
					whiteSpace: "nowrap",
				}}
			>
				{submission.repo_url}
			</div>

			{/* Center-Right Column: Status */}
			<div>
				<StatusIndicator status={submission.pipeline_status} />
			</div>

			{/* Right Column: Score */}
			<div style={{ textAlign: "right" }}>
				<div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.15rem", textTransform: "uppercase", letterSpacing: "1px", fontFamily: "var(--font-mono)" }}>
					Composite
				</div>
				<div
					style={{
						fontFamily: "var(--font-mono)",
						fontSize: "1.4rem",
						fontWeight: 800,
					}}
				>
					{liveScore !== null ? (
						<span style={{ color: "var(--accent-cyan)" }}>
							{liveScore}
							<span style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontWeight: 400 }}>
								/100
							</span>
						</span>
					) : (
						<span style={{ color: "var(--text-secondary)", fontSize: "1.1rem" }}>
							PENDING
						</span>
					)}
				</div>
			</div>
		</Link>
	);
}
