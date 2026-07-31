import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSubmissions } from "../hooks/useSubmissions";
import RubricConfig from "../components/submissions/RubricConfig";
import StatusIndicator from "../components/submissions/StatusIndicator";
import { calculateSynthesisScore } from "../utils/synthesisAgent";

export default function Leaderboard() {
	const { submissions, isLoading, error } = useSubmissions();
	const [activeWeights, setActiveWeights] = useState(null);
	const [searchQuery, setSearchQuery] = useState("");
	const [statusFilter, setStatusFilter] = useState("all"); // 'all', 'complete', 'running', 'failed'
	const [sortBy, setSortBy] = useState("composite"); // 'composite', 'code_quality', 'functionality', 'originality', 'innovation'
	const [sortOrder, setSortOrder] = useState("desc"); // 'asc', 'desc'
	const navigate = useNavigate();

	const handleRowClick = (id) => {
		navigate(`/submission/${id}`);
	};

	const handleSort = (field) => {
		if (sortBy === field) {
			setSortOrder(sortOrder === "asc" ? "desc" : "asc");
		} else {
			setSortBy(field);
			setSortOrder("desc");
		}
	};

	if (isLoading) {
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
					Compiling leaderboard standing...
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
					LEADERBOARD ERROR: {error}
				</p>
			</div>
		);
	}

	// Calculate overall score for each submission dynamically based on active weights
	const processedSubmissions = submissions.map((sub) => {
		const score = calculateSynthesisScore(sub, activeWeights);
		return {
			...sub,
			computedOverallScore: score,
		};
	});

	// Filter submissions
	const filteredSubmissions = processedSubmissions.filter((sub) => {
		// Search query filter
		const matchesSearch =
			sub.team_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
			sub.submission_id.toLowerCase().includes(searchQuery.toLowerCase());

		// Status filter
		let matchesStatus = true;
		if (statusFilter === "complete") {
			matchesStatus = sub.pipeline_status === "complete";
		} else if (statusFilter === "running") {
			matchesStatus =
				sub.pipeline_status === "running" || sub.pipeline_status === "pending";
		} else if (statusFilter === "failed") {
			matchesStatus = sub.pipeline_status === "failed";
		}

		return matchesSearch && matchesStatus;
	});

	// Sort submissions
	const sortedSubmissions = [...filteredSubmissions].sort((a, b) => {
		let valA = null;
		let valB = null;

		if (sortBy === "composite") {
			valA = a.computedOverallScore;
			valB = b.computedOverallScore;
		} else {
			// Sorting by dimension scores
			valA = a[sortBy] && a[sortBy].status === "complete" ? a[sortBy].score : null;
			valB = b[sortBy] && b[sortBy].status === "complete" ? b[sortBy].score : null;
		}

		// Handle null values (place them at the end)
		if (valA === null && valB === null) return 0;
		if (valA === null) return 1;
		if (valB === null) return -1;

		if (sortOrder === "asc") {
			return valA - valB;
		} else {
			return valB - valA;
		}
	});

	// Determine rank number based on overall complete submissions sorting
	const completeRanked = processedSubmissions
		.filter((sub) => sub.pipeline_status === "complete")
		.sort((a, b) => (b.computedOverallScore || 0) - (a.computedOverallScore || 0));

	const getRank = (sub) => {
		if (sub.pipeline_status !== "complete") return "--";
		const index = completeRanked.findIndex((item) => item.submission_id === sub.submission_id);
		return index !== -1 ? index + 1 : "--";
	};

	const getRankBadgeStyle = (rank) => {
		if (rank === 1) {
			return {
				backgroundColor: "rgba(251, 191, 36, 0.15)",
				color: "#fbbf24",
				border: "1px solid rgba(251, 191, 36, 0.3)",
				boxShadow: "0 0 10px rgba(251, 191, 36, 0.2)",
			};
		}
		if (rank === 2) {
			return {
				backgroundColor: "rgba(156, 163, 175, 0.15)",
				color: "#d1d5db",
				border: "1px solid rgba(156, 163, 175, 0.3)",
			};
		}
		if (rank === 3) {
			return {
				backgroundColor: "rgba(180, 83, 9, 0.15)",
				color: "#f59e0b",
				border: "1px solid rgba(180, 83, 9, 0.3)",
			};
		}
		return {
			backgroundColor: "var(--bg-element)",
			color: "var(--text-secondary)",
			border: "1px solid var(--border-subtle)",
		};
	};

	const getSortIndicator = (field) => {
		if (sortBy !== field) return "↕";
		return sortOrder === "asc" ? "▲" : "▼";
	};

	return (
		<div style={{ width: "100%" }}>
			<header
				style={{
					display: "flex",
					justifyContent: "space-between",
					alignItems: "center",
					marginBottom: "2rem",
					borderBottom: "1px solid var(--border-subtle)",
					paddingBottom: "1.25rem",
				}}
			>
				<div>
					<h1>Team Leaderboard</h1>
					<p style={{ marginTop: "0.25rem" }}>
						Real-time standings based on composite auto-judge synthesis weights.
					</p>
				</div>
				<div
					style={{
						fontSize: "0.875rem",
						color: "var(--text-secondary)",
						backgroundColor: "var(--bg-element)",
						padding: "0.35rem 0.75rem",
						borderRadius: "var(--radius-sm)",
						border: "1px solid var(--border-subtle)",
					}}
				>
					<span style={{ color: "var(--text-tertiary)" }}>Ranked Teams: </span>
					<span style={{ fontFamily: "var(--mono)", fontWeight: 500, color: "var(--text-primary)" }}>
						{completeRanked.length}
					</span>
				</div>
			</header>

			{/* Rubric Weight Configurator */}
			<RubricConfig submissions={submissions} onWeightsChange={setActiveWeights} />

			{/* Search and Filters Card */}
			<div
				className="card"
				style={{
					display: "flex",
					flexWrap: "wrap",
					gap: "1rem",
					justifyContent: "space-between",
					alignItems: "center",
					padding: "1rem",
					marginBottom: "1.5rem",
					background: "var(--bg-card)",
				}}
			>
				{/* Search Bar */}
				<div style={{ display: "flex", flex: "1 1 300px", position: "relative" }}>
					<input
						type="text"
						className="form-input"
						placeholder="Search by team or submission ID..."
						value={searchQuery}
						onChange={(e) => setSearchQuery(e.target.value)}
						style={{ width: "100%", paddingLeft: "2.25rem" }}
					/>
					<span
						style={{
							position: "absolute",
							left: "0.75rem",
							top: "50%",
							transform: "translateY(-50%)",
							color: "var(--text-tertiary)",
							fontSize: "0.9rem",
						}}
					>
						🔍
					</span>
					{searchQuery && (
						<button
							onClick={() => setSearchQuery("")}
							style={{
								position: "absolute",
								right: "0.75rem",
								top: "50%",
								transform: "translateY(-50%)",
								background: "none",
								border: "none",
								color: "var(--text-secondary)",
								cursor: "pointer",
								fontSize: "0.8rem",
							}}
						>
							✕
						</button>
					)}
				</div>

				{/* Filters */}
				<div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
					{[
						{ label: "All Standings", value: "all" },
						{ label: "Completed", value: "complete" },
						{ label: "Active Pipelines", value: "running" },
						{ label: "Failed", value: "failed" },
					].map((filter) => (
						<button
							key={filter.value}
							onClick={() => setStatusFilter(filter.value)}
							style={{
								padding: "0.4rem 0.8rem",
								fontSize: "0.75rem",
								borderRadius: "999px",
								border: "1px solid",
								cursor: "pointer",
								fontWeight: 500,
								backgroundColor:
									statusFilter === filter.value
										? "var(--accent)"
										: "var(--bg-element)",
								borderColor:
									statusFilter === filter.value
										? "var(--accent)"
										: "var(--border-subtle)",
								color:
									statusFilter === filter.value
										? "#ffffff"
										: "var(--text-secondary)",
								transition: "all var(--transition)",
							}}
						>
							{filter.label}
						</button>
					))}
				</div>
			</div>

			{/* Table Card */}
			<div className="card" style={{ padding: 0, overflowX: "auto" }}>
				{sortedSubmissions.length === 0 ? (
					<div
						style={{
							padding: "4rem 2rem",
							textAlign: "center",
							color: "var(--text-secondary)",
						}}
					>
						<p>No submissions matches the filter criteria.</p>
					</div>
				) : (
					<table
						style={{
							width: "100%",
							borderCollapse: "collapse",
							textAlign: "left",
						}}
					>
						<thead>
							<tr
								style={{
									borderBottom: "1px solid var(--border-subtle)",
									backgroundColor: "rgba(24, 24, 27, 0.3)",
								}}
							>
								<th style={{ padding: "1rem 1.25rem", color: "var(--text-tertiary)", fontSize: "0.75rem", textTransform: "uppercase", width: "80px" }}>
									Rank
								</th>
								<th style={{ padding: "1rem 1.25rem", color: "var(--text-tertiary)", fontSize: "0.75rem", textTransform: "uppercase" }}>
									Team Name
								</th>
								<th style={{ padding: "1rem 1.25rem", color: "var(--text-tertiary)", fontSize: "0.75rem", textTransform: "uppercase", width: "120px" }}>
									Status
								</th>
								<th
									onClick={() => handleSort("composite")}
									style={{
										padding: "1rem 1.25rem",
										color: "var(--text-primary)",
										fontSize: "0.75rem",
										textTransform: "uppercase",
										cursor: "pointer",
										fontWeight: 600,
										width: "120px",
									}}
								>
									Composite {getSortIndicator("composite")}
								</th>
								<th
									onClick={() => handleSort("code_quality")}
									style={{
										padding: "1rem 1.25rem",
										color: "var(--text-secondary)",
										fontSize: "0.75rem",
										textTransform: "uppercase",
										cursor: "pointer",
										width: "110px",
									}}
								>
									Code Q. {getSortIndicator("code_quality")}
								</th>
								<th
									onClick={() => handleSort("functionality")}
									style={{
										padding: "1rem 1.25rem",
										color: "var(--text-secondary)",
										fontSize: "0.75rem",
										textTransform: "uppercase",
										cursor: "pointer",
										width: "110px",
									}}
								>
									Func. {getSortIndicator("functionality")}
								</th>
								<th
									onClick={() => handleSort("originality")}
									style={{
										padding: "1rem 1.25rem",
										color: "var(--text-secondary)",
										fontSize: "0.75rem",
										textTransform: "uppercase",
										cursor: "pointer",
										width: "110px",
									}}
								>
									Orig. {getSortIndicator("originality")}
								</th>
								<th
									onClick={() => handleSort("innovation")}
									style={{
										padding: "1rem 1.25rem",
										color: "var(--text-secondary)",
										fontSize: "0.75rem",
										textTransform: "uppercase",
										cursor: "pointer",
										width: "110px",
									}}
								>
									Innov. {getSortIndicator("innovation")}
								</th>
							</tr>
						</thead>
						<tbody>
							{sortedSubmissions.map((sub) => {
								const rank = getRank(sub);
								return (
									<tr
										key={sub.submission_id}
										onClick={() => handleRowClick(sub.submission_id)}
										style={{
											borderBottom: "1px solid var(--border-subtle)",
											cursor: "pointer",
											transition: "background var(--transition)",
										}}
										onMouseEnter={(e) => {
											e.currentTarget.style.backgroundColor = "var(--bg-element)";
										}}
										onMouseLeave={(e) => {
											e.currentTarget.style.backgroundColor = "transparent";
										}}
									>
										{/* Rank Row */}
										<td style={{ padding: "1rem 1.25rem" }}>
											<div
												style={{
													display: "inline-flex",
													alignItems: "center",
													justifyContent: "center",
													width: "24px",
													height: "24px",
													borderRadius: "50%",
													fontSize: "0.75rem",
													fontFamily: "var(--mono)",
													fontWeight: 600,
													...getRankBadgeStyle(rank),
												}}
											>
												{rank}
											</div>
										</td>

										{/* Team Name */}
										<td style={{ padding: "1rem 1.25rem" }}>
											<strong style={{ fontSize: "0.9rem", color: "var(--text-primary)" }}>
												{sub.team_name}
											</strong>
											<div style={{ fontSize: "0.7rem", color: "var(--text-tertiary)", fontFamily: "var(--mono)", marginTop: "0.15rem" }}>
												ID: {sub.submission_id}
											</div>
										</td>

										{/* Status Indicator */}
										<td style={{ padding: "1rem 1.25rem" }}>
											<StatusIndicator status={sub.pipeline_status} />
										</td>

										{/* Composite score */}
										<td style={{ padding: "1rem 1.25rem", fontFamily: "var(--mono)", fontSize: "0.95rem", fontWeight: 600 }}>
											{sub.computedOverallScore !== null ? (
												<span style={{ color: "var(--accent)" }}>
													{sub.computedOverallScore.toFixed(1)}
												</span>
											) : (
												<span style={{ color: "var(--text-tertiary)" }}>--</span>
											)}
										</td>

										{/* Code Quality score */}
										<td style={{ padding: "1rem 1.25rem", fontFamily: "var(--mono)", fontSize: "0.85rem" }}>
											{sub.code_quality && sub.code_quality.status === "complete" ? (
												<span style={{ color: "var(--text-secondary)" }}>
													{sub.code_quality.score}
												</span>
											) : (
												<span style={{ color: "var(--text-tertiary)" }}>--</span>
											)}
										</td>

										{/* Functionality score */}
										<td style={{ padding: "1rem 1.25rem", fontFamily: "var(--mono)", fontSize: "0.85rem" }}>
											{sub.functionality && sub.functionality.status === "complete" ? (
												<span style={{ color: "var(--text-secondary)" }}>
													{sub.functionality.score}
												</span>
											) : (
												<span style={{ color: "var(--text-tertiary)" }}>--</span>
											)}
										</td>

										{/* Originality score */}
										<td style={{ padding: "1rem 1.25rem", fontFamily: "var(--mono)", fontSize: "0.85rem" }}>
											{sub.originality && sub.originality.status === "complete" ? (
												<span style={{ color: "var(--text-secondary)" }}>
													{sub.originality.score}
												</span>
											) : (
												<span style={{ color: "var(--text-tertiary)" }}>--</span>
											)}
										</td>

										{/* Innovation score */}
										<td style={{ padding: "1rem 1.25rem", fontFamily: "var(--mono)", fontSize: "0.85rem" }}>
											{sub.innovation && sub.innovation.status === "complete" ? (
												<span style={{ color: "var(--text-secondary)" }}>
													{sub.innovation.score}
												</span>
											) : (
												<span style={{ color: "var(--text-tertiary)" }}>--</span>
											)}
										</td>
									</tr>
								);
							})}
						</tbody>
					</table>
				)}
			</div>
		</div>
	);
}
