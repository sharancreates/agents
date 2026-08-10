import { useState, useEffect } from "react";
import { getStoredWeights, calculateSynthesisScore } from "../../utils/synthesisAgent";
import { updateWeightsOnBackend } from "../../services/api";

export default function RubricConfig({ submissions, onWeightsChange }) {
	const [weights, setWeights] = useState(getStoredWeights());
	const [isOpen, setIsOpen] = useState(false);

	// Propagate weights on mount and when modified
	useEffect(() => {
		onWeightsChange(weights);
	}, [weights, onWeightsChange]);

	const handleWeightChange = (dimension, newValue) => {
		newValue = Math.max(0, Math.min(100, Number(newValue)));
		const otherDimensions = Object.keys(weights).filter((d) => d !== dimension);
		const totalOther = otherDimensions.reduce((sum, d) => sum + weights[d], 0);
		const remaining = 100 - newValue;

		let newWeights = { ...weights, [dimension]: newValue };

		if (totalOther === 0) {
			// Distribute remaining equally if others were 0
			const share = Math.floor(remaining / 3);
			otherDimensions.forEach((d) => {
				newWeights[d] = share;
			});
		} else {
			// Distribute remaining proportionally
			otherDimensions.forEach((d) => {
				newWeights[d] = Math.round((weights[d] / totalOther) * remaining);
			});
		}

		// Correct rounding errors to guarantee sum is exactly 100
		let currentSum = Object.values(newWeights).reduce((a, b) => a + b, 0);
		if (currentSum !== 100) {
			const diff = 100 - currentSum;
			// Adjust the first other dimension with non-zero or just any
			newWeights[otherDimensions[0]] += diff;
		}

		// Ensure no negative values are generated
		for (const d of Object.keys(newWeights)) {
			if (newWeights[d] < 0) {
				// Fall back to equal weights if calculation breaks
				newWeights = {
					code_quality: 25,
					functionality: 25,
					originality: 25,
					innovation: 25,
				};
				break;
			}
		}

		setWeights(newWeights);
	};

	const handleReset = () => {
		const defaults = {
			code_quality: 30,
			functionality: 30,
			originality: 20,
			innovation: 20,
		};
		setWeights(defaults);
	};

	const saveToStorage = async () => {
		localStorage.setItem("autojudge_rubric_weights", JSON.stringify(weights));
		
		// Update weights and scores on the database backend
		await updateWeightsOnBackend(weights);
		
		alert("Rubric configuration updated and saved successfully!");
	};

	// Calculate live preview rankings of the completed submissions
	const getLivePreview = () => {
		const completed = submissions.filter((s) => s.pipeline_status === "complete");
		
		const previewList = completed.map((sub) => {
			const currentWeights = getStoredWeights();
			const currentScore = calculateSynthesisScore(sub, currentWeights);
			const newScore = calculateSynthesisScore(sub, weights);
			return {
				team_name: sub.team_name,
				currentScore,
				newScore,
			};
		});

		// Sort by new score
		return previewList.sort((a, b) => b.newScore - a.newScore).slice(0, 3);
	};

	const livePreview = getLivePreview();

	// Color mappings for dimensions
	const colors = {
		code_quality: "#6366f1", // Indigo
		functionality: "#10b981", // Emerald
		originality: "#f59e0b", // Amber
		innovation: "#ec4899", // Pink
	};

	const formatName = (str) => {
		return str.replace(/_/g, " ").toUpperCase();
	};

	return (
		<div
			className="card"
			style={{
				marginBottom: "1.5rem",
				border: "1px solid var(--border-muted)",
				background: "rgba(14, 14, 17, 0.6)",
				padding: "1rem 1.5rem",
			}}
		>
			<div
				style={{
					display: "flex",
					justifyContent: "space-between",
					alignItems: "center",
					cursor: "pointer",
				}}
				onClick={() => setIsOpen(!isOpen)}
			>
				<div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
					<span style={{ fontSize: "1.25rem", color: "var(--accent)" }}>⚙</span>
					<div>
						<h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 600 }}>
							Rubric Weight Settings (Admin Panel)
						</h3>
						<p style={{ margin: 0, fontSize: "0.8rem", color: "var(--text-secondary)" }}>
							Adjust how much each grading dimension impacts the final composite score.
						</p>
					</div>
				</div>
				<button
					className="btn btn-secondary"
					style={{ padding: "0.3rem 0.6rem", fontSize: "0.75rem" }}
				>
					{isOpen ? "Collapse Setting" : "Expand Weights"}
				</button>
			</div>

			{isOpen && (
				<div style={{ marginTop: "1.5rem", paddingTop: "1.5rem", borderTop: "1px solid var(--border-subtle)" }}>
					{/* Custom Stacked Progress Bar */}
					<div style={{ marginBottom: "2rem" }}>
						<div
							style={{
								display: "flex",
								height: "10px",
								borderRadius: "5px",
								overflow: "hidden",
								backgroundColor: "var(--bg-element)",
								marginBottom: "0.75rem",
							}}
						>
							{Object.entries(weights).map(([dim, val]) => (
								<div
									key={dim}
									style={{
										width: `${val}%`,
										backgroundColor: colors[dim],
										transition: "width 0.2s ease",
									}}
									title={`${formatName(dim)}: ${val}%`}
								/>
							))}
						</div>
						<div
							style={{
								display: "flex",
								flexWrap: "wrap",
								gap: "1.5rem",
								fontSize: "0.75rem",
								color: "var(--text-secondary)",
							}}
						>
							{Object.entries(weights).map(([dim, val]) => (
								<div key={dim} style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
									<div
										style={{
											width: "8px",
											height: "8px",
											borderRadius: "50%",
											backgroundColor: colors[dim],
										}}
									/>
									<span style={{ fontWeight: 500, color: "var(--text-primary)" }}>{val}%</span>
									<span>{formatName(dim)}</span>
								</div>
							))}
						</div>
					</div>

					{/* Sliders Grid */}
					<div
						style={{
							display: "grid",
							gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
							gap: "1.5rem",
							marginBottom: "2rem",
						}}
					>
						{Object.entries(weights).map(([dim, val]) => (
							<div
								key={dim}
								className="form-group"
								style={{
									background: "var(--bg-element)",
									padding: "1rem",
									borderRadius: "var(--radius-sm)",
									border: "1px solid var(--border-subtle)",
								}}
							>
								<div
									style={{
										display: "flex",
										justifyContent: "space-between",
										alignItems: "center",
										marginBottom: "0.5rem",
									}}
								>
									<span
										style={{
											fontSize: "0.75rem",
											fontWeight: 600,
											color: "var(--text-primary)",
											letterSpacing: "0.02em",
										}}
									>
										{formatName(dim)}
									</span>
									<span
										style={{
											fontFamily: "var(--mono)",
											fontSize: "0.85rem",
											fontWeight: 600,
											color: colors[dim],
										}}
									>
										{val}%
									</span>
								</div>
								<input
									type="range"
									min="0"
									max="100"
									value={val}
									onChange={(e) => handleWeightChange(dim, Number(e.target.value))}
									style={{
										width: "100%",
										accentColor: colors[dim],
										cursor: "pointer",
									}}
								/>
							</div>
						))}
					</div>

					{/* Bottom Actions and Preview */}
					<div
						style={{
							display: "flex",
							flexWrap: "wrap",
							justifyContent: "space-between",
							alignItems: "flex-start",
							gap: "1.5rem",
							paddingTop: "1rem",
							borderTop: "1px solid var(--border-subtle)",
						}}
					>
						{/* Live Rank Impact Preview */}
						<div style={{ flex: "1 1 300px" }}>
							<h4
								style={{
									fontSize: "0.75rem",
									color: "var(--text-tertiary)",
									marginBottom: "0.75rem",
								}}
							>
								Live Rank & Score Impact Preview (Top 3)
							</h4>
							{livePreview.length === 0 ? (
								<p style={{ fontSize: "0.8rem", color: "var(--text-tertiary)" }}>
									No completed submissions available to preview.
								</p>
							) : (
								<div
									style={{
										display: "flex",
										flexDirection: "column",
										gap: "0.5rem",
									}}
								>
									{livePreview.map((item, idx) => {
										const diff = item.newScore - item.currentScore;
										const isDiffZero = Math.abs(diff) < 0.01;
										return (
											<div
												key={item.team_name}
												style={{
													display: "flex",
													justifyContent: "space-between",
													alignItems: "center",
													background: "var(--bg-page)",
													padding: "0.5rem 0.75rem",
													borderRadius: "var(--radius-sm)",
													border: "1px solid var(--border-subtle)",
													fontSize: "0.8rem",
												}}
											>
												<span style={{ fontWeight: 500 }}>
													{idx + 1}. {item.team_name}
												</span>
												<div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
													<span style={{ color: "var(--text-secondary)" }}>
														{item.currentScore?.toFixed(1) || "--"}
													</span>
													<span style={{ color: "var(--text-tertiary)" }}>➔</span>
													<span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
														{item.newScore.toFixed(1)}
													</span>
													{!isDiffZero && (
														<span
															style={{
																fontSize: "0.7rem",
																fontWeight: 600,
																color: diff > 0 ? "var(--status-complete)" : "var(--status-failed)",
															}}
														>
															({diff > 0 ? "+" : ""}{diff.toFixed(1)})
														</span>
													)}
												</div>
											</div>
										);
									})}
								</div>
							)}
						</div>

						{/* Action Buttons */}
						<div
							style={{
								display: "flex",
								gap: "0.75rem",
								alignSelf: "flex-end",
							}}
						>
							<button
								onClick={handleReset}
								className="btn btn-secondary"
								style={{ padding: "0.5rem 1rem", fontSize: "0.8rem" }}
							>
								Reset Defaults
							</button>
							<button
								onClick={saveToStorage}
								className="btn btn-primary"
								style={{ padding: "0.5rem 1rem", fontSize: "0.8rem" }}
							>
								Save Configuration
							</button>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}
