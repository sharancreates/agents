import { useState, useEffect } from "react";
import { streamEvaluationTraces } from "../../services/api";

const COUNCIL_STAGES = [
	{ id: "ReconAgent", label: "Recon & Architecture", desc: "Discovers runtime, entrypoint, & stack" },
	{ id: "QAAgent", label: "Dynamic QA Sandbox", desc: "Synthesizes boundary tests in microVM" },
	{ id: "QualityAgent", label: "Semantic Quality", desc: "AST complexity & maintainability audit" },
	{ id: "ForensicsAgent", label: "Git Forensics", desc: "Commit intervals & plagiarism signals" },
	{ id: "CriticAgent", label: "Critic Consensus", desc: "Adversarial evidence calibration" },
	{ id: "FeedbackCoach", label: "Feedback Coach", desc: "Generates constructive dossier" },
];

export default function AgentTraceStream({ submissionId, initialTraces = [], pipelineStatus = "pending" }) {
	const [traces, setTraces] = useState(initialTraces || []);
	const [status, setStatus] = useState(pipelineStatus);
	const [activeStage, setActiveStage] = useState(null);
	const [isConnected, setIsConnected] = useState(false);

	useEffect(() => {
		if (initialTraces && initialTraces.length > 0) {
			setTraces(initialTraces);
		}
	}, [initialTraces]);

	useEffect(() => {
		if (!submissionId) return;

		setIsConnected(true);
		const cleanup = streamEvaluationTraces(
			submissionId,
			(event) => {
				if (event.event === "connected") {
					setStatus(event.status);
				} else if (event.event === "agent.trace" && event.trace) {
					setTraces((prev) => {
						const exists = prev.some((t) => t.timestamp === event.trace.timestamp && t.action === event.trace.action);
						return exists ? prev : [...prev, event.trace];
					});
					setActiveStage(event.trace.agent_role);
				} else if (event.event === "pipeline.complete") {
					setStatus(event.status);
					setIsConnected(false);
				}
			},
			() => {
				setIsConnected(false);
			}
		);

		return () => cleanup();
	}, [submissionId]);

	// Compute completed stages from traces
	const rolesSeen = new Set(traces.map((t) => t.agent_role));

	return (
		<div style={{
			background: "var(--bg-surface)",
			border: "1px solid var(--border-subtle)",
			borderRadius: "var(--radius-lg)",
			padding: "1.5rem",
			marginTop: "1.5rem"
		}}>
			{/* Header */}
			<div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "1rem" }}>
				<div>
					<h3 style={{ fontSize: "1.1rem", fontWeight: 600, display: "flex", alignItems: "center", gap: "0.5rem" }}>
						<span>Agentic Council Deliberation Feed</span>
					</h3>
					<p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "0.2rem" }}>
						Live thought traces streamed directly from the autonomous evaluation council.
					</p>
				</div>
				<div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
					<span style={{
						width: "8px",
						height: "8px",
						borderRadius: "50%",
						backgroundColor: isConnected ? "var(--success)" : status === "complete" ? "var(--success)" : "var(--text-tertiary)",
						boxShadow: isConnected ? "0 0 8px var(--success)" : "none"
					}}></span>
					<span>{status === "complete" ? "Council Adjourned" : isConnected ? "Live SSE Stream" : "Synchronized"}</span>
				</div>
			</div>

			{/* Stage Progression Pills */}
			<div style={{
				display: "grid",
				gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
				gap: "0.75rem",
				marginBottom: "1.5rem"
			}}>
				{COUNCIL_STAGES.map((stg) => {
					const isDone = rolesSeen.has(stg.id) || status === "complete";
					const isCurrent = activeStage === stg.id && status === "running";

					return (
						<div
							key={stg.id}
							style={{
								padding: "0.75rem",
								borderRadius: "var(--radius-md)",
								background: isCurrent ? "rgba(99, 102, 241, 0.12)" : isDone ? "rgba(34, 197, 94, 0.08)" : "var(--bg-element)",
								border: `1px solid ${isCurrent ? "var(--accent)" : isDone ? "rgba(34, 197, 94, 0.3)" : "var(--border-subtle)"}`,
								transition: "all 0.2s ease"
							}}
						>
							<div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
								<span style={{ fontSize: "0.8rem", fontWeight: 600, color: isCurrent ? "var(--accent)" : isDone ? "var(--success)" : "var(--text-secondary)" }}>
									{stg.label}
								</span>
								<span style={{ fontSize: "0.75rem" }}>
									{isDone ? "✓" : isCurrent ? "●" : "○"}
								</span>
							</div>
							<p style={{ fontSize: "0.7rem", color: "var(--text-tertiary)", marginTop: "0.25rem", lineHeight: 1.2 }}>
								{stg.desc}
							</p>
						</div>
					);
				})}
			</div>

			{/* Chronological Deliberation Events */}
			<div style={{
				maxHeight: "380px",
				overflowY: "auto",
				display: "flex",
				flexDirection: "column",
				gap: "0.75rem",
				paddingRight: "0.5rem"
			}}>
				{traces.length === 0 ? (
					<div style={{ textAlign: "center", padding: "2rem", color: "var(--text-tertiary)", fontSize: "0.875rem" }}>
						Awaiting council convening. Agent thought events will appear here in real-time.
					</div>
				) : (
					traces.map((tr, idx) => (
						<div
							key={idx}
							style={{
								background: "var(--bg-element)",
								border: "1px solid var(--border-subtle)",
								borderRadius: "var(--radius-md)",
								padding: "0.85rem 1rem",
								display: "flex",
								flexDirection: "column",
								gap: "0.35rem"
							}}
						>
							<div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
								<div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
									<span style={{
										fontSize: "0.75rem",
										fontWeight: 600,
										color: "var(--accent)",
										background: "rgba(99, 102, 241, 0.15)",
										padding: "0.15rem 0.5rem",
										borderRadius: "var(--radius-sm)",
										fontFamily: "var(--mono)"
									}}>
										{tr.agent_role}
									</span>
									<span style={{ fontSize: "0.8rem", fontWeight: 500, color: "var(--text-primary)" }}>
										{tr.action}
									</span>
								</div>
								<span style={{ fontSize: "0.7rem", color: "var(--text-tertiary)", fontFamily: "var(--mono)" }}>
									{tr.timestamp ? new Date(tr.timestamp).toLocaleTimeString() : ""}
								</span>
							</div>
							<p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", margin: 0, lineHeight: 1.4 }}>
								{tr.reasoning}
							</p>
							{tr.payload && Object.keys(tr.payload).length > 0 && (
								<pre style={{
									fontSize: "0.75rem",
									color: "var(--text-tertiary)",
									background: "rgba(0,0,0,0.25)",
									padding: "0.5rem",
									borderRadius: "var(--radius-sm)",
									margin: "0.25rem 0 0 0",
									overflowX: "auto"
								}}>
									{JSON.stringify(tr.payload, null, 2)}
								</pre>
							)}
						</div>
					))
				)}
			</div>
		</div>
	);
}
