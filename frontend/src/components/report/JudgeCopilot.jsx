import { useState } from "react";
import { askJudgeCopilot } from "../../services/api";

const QUICK_PROMPTS = [
	"Where is authentication and authorization handled?",
	"Are there any sandbox security or execution risks?",
	"Does this submission integrate Google Gemini or AI APIs?",
	"How is rate limiting or quota gating enforced?"
];

export default function JudgeCopilot({ submissionId, repoUrl }) {
	const [isOpen, setIsOpen] = useState(false);
	const [question, setQuestion] = useState("");
	const [isLoading, setIsLoading] = useState(false);
	const [messages, setMessages] = useState([
		{
			role: "assistant",
			text: `Hello! I'm Judge Copilot, powered by AutoJudge's AST Codebase RAG Engine. Ask me any architectural, security, or implementation question about submission ${submissionId}.`,
			citations: []
		}
	]);

	const handleAsk = async (queryToAsk) => {
		const q = queryToAsk || question;
		if (!q.trim() || isLoading) return;

		const userMsg = { role: "user", text: q, citations: [] };
		setMessages((prev) => [...prev, userMsg]);
		setQuestion("");
		setIsLoading(true);

		try {
			const res = await askJudgeCopilot(submissionId, q);
			const botMsg = {
				role: "assistant",
				text: res.answer || "No response received.",
				citations: res.citations || []
			};
			setMessages((prev) => [...prev, botMsg]);
		} catch (err) {
			setMessages((prev) => [
				...prev,
				{
					role: "assistant",
					text: `Error retrieving codebase context: ${err.message}`,
					citations: []
				}
			]);
		} finally {
			setIsLoading(false);
		}
	};

	return (
		<div style={{
			background: "var(--bg-surface)",
			border: "1px solid var(--border-subtle)",
			borderRadius: "var(--radius-lg)",
			marginTop: "1.5rem",
			overflow: "hidden"
		}}>
			{/* Header Toggle */}
			<div
				onClick={() => setIsOpen(!isOpen)}
				style={{
					padding: "1rem 1.5rem",
					display: "flex",
					justifyContent: "space-between",
					alignItems: "center",
					cursor: "pointer",
					background: "rgba(99, 102, 241, 0.05)",
					borderBottom: isOpen ? "1px solid var(--border-subtle)" : "none"
				}}
			>
				<div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
					<span style={{ fontSize: "1.2rem" }}>🤖</span>
					<div>
						<h3 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)" }}>
							Ask AutoJudge: Judge Copilot
						</h3>
						<p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "0.15rem" }}>
							AST-aware conversational RAG with line-numbered code evidence.
						</p>
					</div>
				</div>
				<button
					className="btn btn-secondary"
					style={{ padding: "0.35rem 0.75rem", fontSize: "0.8rem" }}
				>
					{isOpen ? "Collapse ▲" : "Ask Question ▼"}
				</button>
			</div>

			{/* Expandable Copilot Interface */}
			{isOpen && (
				<div style={{ padding: "1.5rem" }}>
					{/* Quick Prompt Chips */}
					<div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "1.25rem" }}>
						{QUICK_PROMPTS.map((prompt, idx) => (
							<button
								key={idx}
								onClick={() => handleAsk(prompt)}
								disabled={isLoading}
								style={{
									background: "var(--bg-element)",
									border: "1px solid var(--border-subtle)",
									color: "var(--text-secondary)",
									padding: "0.35rem 0.75rem",
									borderRadius: "16px",
									fontSize: "0.75rem",
									cursor: "pointer",
									transition: "all 0.15s ease"
								}}
							>
								{prompt}
							</button>
						))}
					</div>

					{/* Chat Message History */}
					<div style={{
						maxHeight: "360px",
						overflowY: "auto",
						display: "flex",
						flexDirection: "column",
						gap: "1rem",
						marginBottom: "1.25rem",
						paddingRight: "0.5rem"
					}}>
						{messages.map((m, idx) => (
							<div
								key={idx}
								style={{
									alignSelf: m.role === "user" ? "flex-end" : "flex-start",
									maxWidth: "85%",
									background: m.role === "user" ? "var(--accent)" : "var(--bg-element)",
									color: m.role === "user" ? "#fff" : "var(--text-primary)",
									padding: "0.85rem 1rem",
									borderRadius: "var(--radius-md)",
									border: m.role === "user" ? "none" : "1px solid var(--border-subtle)",
									fontSize: "0.875rem",
									lineHeight: 1.5
								}}
							>
								<div style={{ whiteSpace: "pre-wrap" }}>{m.text}</div>

								{/* Citations if any */}
								{m.citations && m.citations.length > 0 && (
									<div style={{ marginTop: "0.75rem", borderTop: "1px solid rgba(255,255,255,0.1)", paddingTop: "0.5rem" }}>
										<div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.4rem" }}>
											Verified Code Evidence Citations:
										</div>
										<div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
											{m.citations.map((c, cIdx) => (
												<div
													key={cIdx}
													style={{
														background: "rgba(0,0,0,0.3)",
														padding: "0.35rem 0.6rem",
														borderRadius: "4px",
														fontFamily: "var(--mono)",
														fontSize: "0.75rem",
														display: "flex",
														justifyContent: "space-between",
														alignItems: "center"
													}}
												>
													<span style={{ color: "var(--accent)" }}>{c.citation || `${c.file_path}:${c.lines}`}</span>
													{c.similarity_score && (
														<span style={{ color: "var(--text-tertiary)", fontSize: "0.7rem" }}>
															{Math.round(c.similarity_score * 100)}% match
														</span>
													)}
												</div>
											))}
										</div>
									</div>
								)}
							</div>
						))}
						{isLoading && (
							<div style={{ alignSelf: "flex-start", color: "var(--text-tertiary)", fontSize: "0.85rem", fontStyle: "italic" }}>
								Copilot searching AST vector index and synthesizing answer...
							</div>
						)}
					</div>

					{/* Question Input Field */}
					<form
						onSubmit={(e) => { e.preventDefault(); handleAsk(); }}
						style={{ display: "flex", gap: "0.75rem" }}
					>
						<input
							type="text"
							placeholder="Ask a technical or architectural question about this codebase..."
							value={question}
							onChange={(e) => setQuestion(e.target.value)}
							disabled={isLoading}
							style={{
								flex: 1,
								padding: "0.65rem 0.85rem",
								background: "var(--bg-element)",
								border: "1px solid var(--border-subtle)",
								borderRadius: "var(--radius-sm)",
								color: "var(--text-primary)",
								fontSize: "0.875rem"
							}}
						/>
						<button
							type="submit"
							disabled={isLoading || !question.trim()}
							className="btn btn-primary"
							style={{ padding: "0.65rem 1.25rem", fontSize: "0.875rem" }}
						>
							{isLoading ? "Searching..." : "Ask Copilot"}
						</button>
					</form>
				</div>
			)}
		</div>
	);
}
