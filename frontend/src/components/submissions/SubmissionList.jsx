import { Link } from "react-router-dom";
import StatusIndicator from "./StatusIndicator";

export default function SubmissionList({ submissions }) {
	if (!submissions || submissions.length === 0) {
		return (
			<p style={{ color: "var(--text-secondary)" }}>
				No submissions found.
			</p>
		);
	}

	return (
		<div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
			{submissions.map((sub) => (
				<Link
					to={`/submission/${sub.submission_id}`}
					key={sub.submission_id}
					className="glass-panel"
					style={{
						padding: "1.5rem",
						textDecoration: "none",
						color: "inherit",
						display: "grid",
						gridTemplateColumns: "1fr 2fr 1fr 1fr",
						alignItems: "center",
						transition: "transform 0.2s, background-color 0.2s",
						cursor: "pointer",
					}}
					onMouseEnter={(e) =>
						(e.currentTarget.style.backgroundColor =
							"rgba(25, 25, 30, 0.9)")
					}
					onMouseLeave={(e) =>
						(e.currentTarget.style.backgroundColor =
							"var(--glass-panel)")
					}
				>
					<div>
						<h3 style={{ margin: "0 0 0.25rem 0" }}>
							{sub.team_name}
						</h3>
						<span
							style={{
								color: "var(--text-secondary)",
								fontSize: "0.85rem",
								fontFamily: "var(--font-mono)",
							}}
						>
							{sub.submission_id}
						</span>
					</div>

					<div
						style={{
							color: "var(--text-secondary)",
							fontSize: "0.9rem",
						}}
					>
						{sub.repo_url}
					</div>

					<div>
						<StatusIndicator status={sub.pipeline_status} />
					</div>

					<div
						style={{
							textAlign: "right",
							fontFamily: "var(--font-mono)",
							fontSize: "1.25rem",
							fontWeight: 700,
						}}
					>
						{sub.overall_score !== null ? (
							<span style={{ color: "var(--accent-cyan)" }}>
								{sub.overall_score}{" "}
								<span
									style={{
										fontSize: "0.85rem",
										color: "var(--text-secondary)",
									}}
								>
									/ 100
								</span>
							</span>
						) : (
							<span style={{ color: "var(--text-secondary)" }}>
								--
							</span>
						)}
					</div>
				</Link>
			))}
		</div>
	);
}
