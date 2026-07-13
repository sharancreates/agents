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
			className="card card-interactive"
			style={{
				textDecoration: "none",
				color: "inherit",
				display: "grid",
				gridTemplateColumns: "1.5fr 2fr 1.2fr 1fr",
				alignItems: "center",
				gap: "1.5rem",
				padding: "1rem 1.25rem",
			}}
		>
			{/* Left Column: Team info & Time */}
			<div>
				<h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)" }}>
					{submission.team_name}
				</h3>
				<div
					style={{
						display: "flex",
						alignItems: "center",
						gap: "0.5rem",
						marginTop: "0.25rem",
					}}
				>
					<span
						style={{
							color: "var(--text-tertiary)",
							fontSize: "0.75rem",
							fontFamily: "var(--mono)",
						}}
					>
						{submission.submission_id}
					</span>
					<span style={{ color: "var(--text-tertiary)", fontSize: "0.75rem" }}>•</span>
					<span style={{ color: "var(--text-secondary)", fontSize: "0.75rem" }}>
						{formattedTime}
					</span>
				</div>
			</div>

			{/* Center-Left Column: Repository Link */}
			<div
				style={{
					color: "var(--text-secondary)",
					fontSize: "0.85rem",
					fontFamily: "var(--mono)",
					overflow: "hidden",
					textOverflow: "ellipsis",
					whiteSpace: "nowrap",
				}}
			>
				{submission.repo_url.replace("https://github.com/", "")}
			</div>

			{/* Center-Right Column: Status */}
			<div>
				<StatusIndicator status={submission.pipeline_status} />
			</div>

			{/* Right Column: Score */}
			<div style={{ textAlign: "right" }}>
				<div
					style={{
						fontFamily: "var(--mono)",
						fontSize: "1.1rem",
						fontWeight: 600,
					}}
				>
					{liveScore !== null ? (
						<span style={{ color: "var(--text-primary)" }}>
							{liveScore}
							<span style={{ fontSize: "0.8rem", color: "var(--text-tertiary)", fontWeight: 400 }}>
								/100
							</span>
						</span>
					) : (
						<span style={{ color: "var(--text-tertiary)", fontSize: "0.85rem", fontWeight: 400 }}>
							PENDING
						</span>
					)}
				</div>
			</div>
		</Link>
	);
}
