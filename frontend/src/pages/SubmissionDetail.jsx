import { useParams, Link } from "react-router-dom";
import { useSubmissionDetail } from "../hooks/useSubmissionDetail";
import StatusIndicator from "../components/submissions/StatusIndicator";
import RawJsonDebugger from "../components/report/RawJsonDebugger";
import ReportContainer from "../components/report/ReportContainer";
import { calculateSynthesisScore } from "../utils/synthesisAgent";

export default function SubmissionDetail() {
	const { id } = useParams();

	// Using the live-polling hook
	const { submission, isLoading, error } = useSubmissionDetail(id);
	const liveScore = calculateSynthesisScore(submission);

	if (isLoading && !submission) {
		return (
			<div
				style={{
					display: "flex",
					flexDirection: "column",
					alignItems: "center",
					justifyContent: "center",
					padding: "8rem 2rem",
					color: "var(--text-secondary)",
				}}
			>
				<div
					className="animate-spin"
					style={{
						width: "24px",
						height: "24px",
						border: "2px solid var(--border-muted)",
						borderTopColor: "var(--accent)",
						borderRadius: "50%",
						marginBottom: "1rem",
					}}
				></div>
				<p style={{ fontFamily: "var(--mono)", fontSize: "0.85rem" }}>
					Establishing secure connection...
				</p>
			</div>
		);
	}

	if (error) {
		return (
			<div
				className="card"
				style={{
					borderLeft: "4px solid var(--status-failed)",
					padding: "1.5rem",
					color: "var(--status-failed)",
					background: "var(--status-failed-bg)",
					marginTop: "2rem",
				}}
			>
				<p style={{ fontFamily: "var(--mono)", fontWeight: 500 }}>
					ERROR: {error}
				</p>
				<Link to="/" style={{ display: "inline-block", marginTop: "1rem", color: "var(--accent)" }}>
					← Return to Queue
				</Link>
			</div>
		);
	}

	if (!submission) return null;

	return (
		<div style={{ width: "100%" }}>
			<Link
				to="/"
				style={{
					display: "inline-flex",
					alignItems: "center",
					gap: "0.35rem",
					color: "var(--text-secondary)",
					fontSize: "0.85rem",
					fontWeight: 500,
					marginBottom: "1.5rem",
					transition: "color var(--transition)",
				}}
				onMouseEnter={(e) => (e.target.style.color = "var(--text-primary)")}
				onMouseLeave={(e) => (e.target.style.color = "var(--text-secondary)")}
			>
				<span>←</span> Back to Queue
			</Link>

			<header
				className="card"
				style={{
					display: "flex",
					justifyContent: "space-between",
					alignItems: "center",
					padding: "1.5rem",
					marginBottom: "2.0rem",
				}}
			>
				<div>
					<div
						style={{
							display: "flex",
							gap: "1rem",
							alignItems: "center",
						}}
					>
						<h1 style={{ margin: 0, fontSize: "1.5rem" }}>{submission.team_name}</h1>
						<StatusIndicator status={submission.pipeline_status} />
					</div>
					<div
						style={{
							color: "var(--text-secondary)",
							fontSize: "0.85rem",
							marginTop: "0.5rem",
							fontFamily: "var(--mono)",
						}}
					>
						ID: <span style={{ color: "var(--text-primary)" }}>{submission.submission_id}</span>
						<span style={{ margin: "0 0.75rem", color: "var(--border-muted)" }}>|</span>
						<a
							href={submission.repo_url}
							target="_blank"
							rel="noreferrer"
							style={{ color: "var(--accent)" }}
						>
							{submission.repo_url.replace("https://github.com/", "")}
						</a>
					</div>
				</div>

				<div style={{ textAlign: "right" }}>
					<div
						style={{
							fontSize: "0.75rem",
							color: "var(--text-tertiary)",
							textTransform: "uppercase",
							letterSpacing: "0.05em",
							marginBottom: "0.25rem",
						}}
					>
						Composite Score
					</div>
					<div
						style={{
							fontFamily: "var(--mono)",
							fontSize: "1.75rem",
							fontWeight: 600,
						}}
					>
						{liveScore !== null ? (
							<span style={{ color: "var(--text-primary)" }}>
								{liveScore}
								<span style={{ fontSize: "1rem", color: "var(--text-tertiary)", fontWeight: 400 }}>
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
			</header>

			{/* The structured evaluation report */}
			<ReportContainer submission={submission} />

			{/* The raw data view for P2 and P3 to debug their agents */}
			<RawJsonDebugger data={submission} />
		</div>
	);
}
