import { useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { jsPDF } from "jspdf";
import { useSubmissionDetail } from "../hooks/useSubmissionDetail";
import StatusIndicator from "../components/submissions/StatusIndicator";
import RawJsonDebugger from "../components/report/RawJsonDebugger";
import ReportContainer from "../components/report/ReportContainer";
import ParticipantFeedback from "../components/report/ParticipantFeedback";
import {
	calculateSynthesisScore,
	generateSynthesisSummary,
	getStoredWeights,
} from "../utils/synthesisAgent";
import { generateParticipantFeedback } from "../utils/feedbackAgent";

export default function SubmissionDetail() {
	const { id } = useParams();

	// Using the live-polling hook
	const { submission, isLoading, error } = useSubmissionDetail(id);
	
	const currentWeights = getStoredWeights();
	const liveScore = calculateSynthesisScore(submission, currentWeights);
	const liveSummary = generateSynthesisSummary(submission, currentWeights);

	useEffect(() => {
		const handleKeyDown = (e) => {
			if (e.altKey && (e.key === "p" || e.key === "P")) {
				e.preventDefault();
				handleExportPdf();
			} else if (e.altKey && (e.key === "j" || e.key === "J")) {
				e.preventDefault();
				handleExportJson();
			}
		};
		window.addEventListener("keydown", handleKeyDown);
		return () => window.removeEventListener("keydown", handleKeyDown);
	}, [submission, liveScore, liveSummary]);

	const handleExportJson = () => {
		if (!submission) return;
		const report = {
			submission_id: submission.submission_id,
			team_name: submission.team_name,
			repo_url: submission.repo_url,
			commit_sha: submission.commit_sha || "0000000000000000000000000000000000000000",
			pipeline_status: submission.pipeline_status,
			pipeline_started_at: submission.submitted_at || new Date().toISOString(),
			pipeline_completed_at: submission.pipeline_status === "complete" ? submission.submitted_at : null,
			overall_score: liveScore,
			synthesis_summary: liveSummary,
			requires_manual_review: !!(
				(submission.code_quality?.flags && submission.code_quality.flags.length > 0) ||
				(submission.originality?.flags && submission.originality.flags.length > 0)
			),
			review_status: "unreviewed",
			reviewed_by: null,
			rubric_weights: currentWeights,
			dimensions: {
				code_quality: submission.code_quality,
				functionality: submission.functionality,
				originality: submission.originality,
				innovation: submission.innovation,
			},
		};

		const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
		const downloadAnchor = document.createElement("a");
		downloadAnchor.setAttribute("href", dataStr);
		downloadAnchor.setAttribute("download", `autojudge_report_${submission.submission_id}.json`);
		document.body.appendChild(downloadAnchor);
		downloadAnchor.click();
		downloadAnchor.remove();
	};

	const handleExportPdf = () => {
		if (!submission) return;
		
		const doc = new jsPDF({
			orientation: "portrait",
			unit: "mm",
			format: "a4",
		});

		// Theme Styling
		const primaryColor = "#09090b";
		const secondaryTextColor = "#4b5563";
		const textColor = "#1f2937";

		// Draw dark background banner for the header
		doc.setFillColor(9, 9, 11);
		doc.rect(0, 0, 210, 45, "F");

		// Document Title
		doc.setFont("helvetica", "bold");
		doc.setFontSize(20);
		doc.setTextColor(255, 255, 255);
		doc.text("AutoJudge Evaluation Report", 15, 18);

		doc.setFont("helvetica", "normal");
		doc.setFontSize(9);
		doc.setTextColor(161, 161, 170);
		doc.text(`Generated: ${new Date().toLocaleString()} | AutoJudge Platform`, 15, 24);

		// Team Name
		doc.setFont("helvetica", "bold");
		doc.setFontSize(15);
		doc.setTextColor(255, 255, 255);
		doc.text(submission.team_name, 15, 36);

		// Composite Score Pill
		doc.setFillColor(99, 102, 241);
		doc.roundedRect(152, 10, 43, 25, 2, 2, "F");
		doc.setTextColor(255, 255, 255);
		doc.setFont("helvetica", "bold");
		doc.setFontSize(8);
		doc.text("COMPOSITE SCORE", 157, 16);
		doc.setFontSize(16);
		doc.text(`${liveScore !== null ? liveScore.toFixed(1) : "PENDING"}/100`, 157, 28);

		// Metadata Info
		doc.setTextColor(primaryColor);
		doc.setFont("helvetica", "bold");
		doc.setFontSize(11);
		doc.text("Submission Information", 15, 55);

		doc.setDrawColor(229, 231, 235);
		doc.line(15, 57, 195, 57);

		doc.setFont("helvetica", "normal");
		doc.setFontSize(9);
		doc.setTextColor(secondaryTextColor);
		doc.text("Submission ID:", 15, 64);
		doc.text("Repository URL:", 15, 70);
		doc.text("Commit SHA:", 15, 76);
		doc.text("Pipeline Status:", 15, 82);

		doc.setTextColor(textColor);
		doc.setFont("helvetica", "bold");
		doc.text(submission.submission_id, 45, 64);
		doc.text(submission.repo_url, 45, 70);
		doc.text(submission.commit_sha || "N/A", 45, 76);
		doc.text(submission.pipeline_status.toUpperCase(), 45, 82);

		// Rubric Weights Column
		doc.setTextColor(secondaryTextColor);
		doc.setFont("helvetica", "normal");
		doc.text("Rubric Weights:", 115, 64);
		doc.setTextColor(textColor);
		doc.setFont("helvetica", "bold");
		doc.text(`Code Quality: ${currentWeights.code_quality}%`, 115, 70);
		doc.text(`Functionality: ${currentWeights.functionality}%`, 115, 76);
		doc.text(`Originality: ${currentWeights.originality}%`, 115, 82);
		doc.text(`Innovation: ${currentWeights.innovation}%`, 115, 88);

		// Synthesis Summary Section
		doc.setFont("helvetica", "bold");
		doc.setFontSize(11);
		doc.setTextColor(primaryColor);
		doc.text("Synthesis Verdict Summary", 15, 98);
		doc.line(15, 100, 195, 100);

		doc.setFont("helvetica", "normal");
		doc.setFontSize(9.5);
		doc.setTextColor(textColor);

		// Remove Markdown tags from PDF export
		const cleanSummary = liveSummary
			.replace(/### (.*?)\n/g, "\n$1\n")
			.replace(/\*\*/g, "")
			.replace(/- /g, "• ")
			.trim();
			
		const splitText = doc.splitTextToSize(cleanSummary, 180);
		doc.text(splitText, 15, 106);

		// Dimension Breakdowns
		let y = 106 + (splitText.length * 4.5) + 12;

		if (y > 265) {
			doc.addPage();
			y = 20;
		}

		doc.setFont("helvetica", "bold");
		doc.setFontSize(11);
		doc.setTextColor(primaryColor);
		doc.text("Dimension Standings", 15, y);
		doc.line(15, y + 2, 195, y + 2);
		y += 8;

		const dims = [
			{ name: "Code Quality", data: submission.code_quality, color: [99, 102, 241] },
			{ name: "Functionality Sandbox", data: submission.functionality, color: [16, 185, 129] },
			{ name: "Originality Check", data: submission.originality, color: [245, 158, 11] },
			{ name: "Innovation Agent", data: submission.innovation, color: [236, 72, 153] },
		];

		dims.forEach((dim) => {
			if (y > 255) {
				doc.addPage();
				y = 20;
			}

			// Background Box
			doc.setFillColor(249, 250, 251);
			doc.roundedRect(15, y, 180, 24, 1.5, 1.5, "F");
			doc.setDrawColor(229, 231, 235);
			doc.roundedRect(15, y, 180, 24, 1.5, 1.5, "D");

			// Left Color Strip
			doc.setFillColor(dim.color[0], dim.color[1], dim.color[2]);
			doc.rect(15, y, 2.5, 24, "F");

			// Text Information
			doc.setTextColor(primaryColor);
			doc.setFont("helvetica", "bold");
			doc.setFontSize(10);
			doc.text(dim.name, 22, y + 7);

			doc.setFont("helvetica", "normal");
			doc.setFontSize(8.5);
			doc.setTextColor(secondaryTextColor);
			const dSummary = dim.data?.summary || "No analysis details generated.";
			const splitDSummary = doc.splitTextToSize(dSummary, 132);
			doc.text(splitDSummary, 22, y + 13);

			// Score Tag
			doc.setFillColor(dim.color[0], dim.color[1], dim.color[2]);
			doc.roundedRect(165, y + 6, 22, 12, 1, 1, "F");
			doc.setTextColor(255, 255, 255);
			doc.setFont("helvetica", "bold");
			doc.setFontSize(9.5);
			doc.text(`${dim.data?.score !== null ? dim.data.score : "--"}/100`, 169, y + 14);

			y += 28;
		});

		doc.save(`autojudge_report_${submission.submission_id}.pdf`);
	};

	// Custom parser to format generated summary markdown into React nodes
	const renderSummaryMarkdown = (text) => {
		if (!text) return null;
		return text.split("\n\n").map((para, i) => {
			if (para.startsWith("### ")) {
				return (
					<h3
						key={i}
						style={{
							color: "var(--text-primary)",
							marginTop: "1.25rem",
							marginBottom: "0.5rem",
							fontSize: "0.95rem",
							fontWeight: 600,
							display: "flex",
							alignItems: "center",
							gap: "0.4rem",
						}}
					>
						{para.includes("Flags") ? "⚠️ " : "✦ "}
						{para.replace("### ", "")}
					</h3>
				);
			}
			if (para.startsWith("- ")) {
				return (
					<ul
						key={i}
						style={{
							margin: "0.5rem 0 1rem 1.25rem",
							color: "var(--text-secondary)",
							paddingLeft: "0.5rem",
						}}
					>
						{para.split("\n").map((li, j) => {
							const cleanLi = li.replace("- ", "");
							const parts = cleanLi.split(/\*\*(.*?)\*\*/g);
							return (
								<li key={j} style={{ marginBottom: "0.4rem", fontSize: "0.875rem" }}>
									{parts.map((part, index) =>
										index % 2 === 1 ? (
											<strong key={index} style={{ color: "var(--text-primary)" }}>
												{part}
											</strong>
										) : (
											part
										)
									)}
								</li>
							);
						})}
					</ul>
				);
			}

			const parts = para.split(/\*\*(.*?)\*\*/g);
			return (
				<p
					key={i}
					style={{
						marginBottom: "0.85rem",
						lineHeight: "1.6",
						fontSize: "0.875rem",
						color: "var(--text-secondary)",
					}}
				>
					{parts.map((part, index) =>
						index % 2 === 1 ? (
							<strong key={index} style={{ color: "var(--text-primary)" }}>
								{part}
							</strong>
						) : (
							part
						)
					)}
				</p>
			);
		});
	};

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
			<div
				style={{
					display: "flex",
					justifyContent: "space-between",
					alignItems: "center",
					marginBottom: "1.5rem",
				}}
			>
				<Link
					to="/"
					style={{
						display: "inline-flex",
						alignItems: "center",
						gap: "0.35rem",
						color: "var(--text-secondary)",
						fontSize: "0.85rem",
						fontWeight: 500,
						transition: "color var(--transition)",
					}}
					onMouseEnter={(e) => (e.target.style.color = "var(--text-primary)")}
					onMouseLeave={(e) => (e.target.style.color = "var(--text-secondary)")}
				>
					<span>←</span> Back to Standings
				</Link>

				<div style={{ display: "flex", gap: "0.75rem" }}>
					<button
						className="btn btn-secondary"
						onClick={handleExportJson}
						disabled={submission.pipeline_status !== "complete"}
						style={{ display: "flex", alignItems: "center", gap: "0.4rem", padding: "0.4rem 0.8rem", fontSize: "0.8rem" }}
					>
						<span>📥</span> Export JSON
					</button>
					<button
						className="btn btn-primary"
						onClick={handleExportPdf}
						disabled={submission.pipeline_status !== "complete"}
						style={{ display: "flex", alignItems: "center", gap: "0.4rem", padding: "0.4rem 0.8rem", fontSize: "0.8rem" }}
					>
						<span>📄</span> Export PDF
					</button>
				</div>
			</div>

			<header
				className="card"
				style={{
					display: "flex",
					justifyContent: "space-between",
					alignItems: "center",
					padding: "1.5rem",
					marginBottom: "1.5rem",
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
								{liveScore.toFixed(1)}
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

			{/* Synthesis Summary Section */}
			<div
				className="card"
				style={{
					marginBottom: "2.0rem",
					borderLeft: "4px solid var(--accent)",
					background: "linear-gradient(90deg, rgba(99, 102, 241, 0.04) 0%, rgba(9, 9, 11, 0) 100%)",
				}}
			>
				<h2
					style={{
						fontSize: "1.1rem",
						fontWeight: 600,
						color: "var(--text-primary)",
						borderBottom: "1px solid var(--border-subtle)",
						paddingBottom: "0.75rem",
						marginBottom: "1rem",
					}}
				>
					Synthesis Agent Verdict Summary
				</h2>
				<div style={{ padding: "0.25rem 0" }}>
					{renderSummaryMarkdown(liveSummary)}
				</div>
			</div>

			{/* Participant-Facing Commentary generated by Feedback Agent */}
			<ParticipantFeedback
				feedbackData={submission?.participant_feedback || generateParticipantFeedback(submission)}
				teamName={submission?.team_name}
			/>

			{/* The structured evaluation report */}
			<ReportContainer submission={submission} />

			{/* The raw data view for P2 and P3 to debug their agents */}
			<RawJsonDebugger data={submission} />
		</div>
	);
}
