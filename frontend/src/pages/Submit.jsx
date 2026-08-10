import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { submitRepository } from "../services/api";

export default function Submit() {
	const navigate = useNavigate();
	const [teamName, setTeamName] = useState("");
	const [repoUrl, setRepoUrl] = useState("");
	const [commitSha, setCommitSha] = useState("");
	const [error, setError] = useState("");
	const [isSubmitting, setIsSubmitting] = useState(false);
	const [success, setSuccess] = useState(false);

	const handleSubmit = async (e) => {
		e.preventDefault();
		setError("");
		setSuccess(false);

		// Basic Validation
		if (!teamName.trim()) {
			setError("Team Name is required.");
			return;
		}

		if (!repoUrl.trim()) {
			setError("Repository URL is required.");
			return;
		}

		// Simple GitHub URL validation
		if (!repoUrl.startsWith("https://github.com/") && !repoUrl.startsWith("http://github.com/")) {
			setError("Please enter a valid GitHub Repository URL (must start with https://github.com/).");
			return;
		}

		// Commit SHA validation if provided
		if (commitSha && !/^[a-f0-9]{40}$/i.test(commitSha.trim())) {
			setError("Commit SHA must be a 40-character hexadecimal string.");
			return;
		}

		setIsSubmitting(true);

		try {
			await submitRepository({
				team_name: teamName.trim(),
				repo_url: repoUrl.trim(),
				commit_sha: commitSha.trim() || null,
			});
			setSuccess(true);
			setTimeout(() => {
				navigate("/");
			}, 1500);
		} catch (err) {
			setError(err.message || "Failed to submit repository. Please try again.");
			setIsSubmitting(false);
		}
	};

	return (
		<div style={{ maxWidth: "600px", margin: "0 auto", width: "100%" }}>
			<header
				style={{
					borderBottom: "1px solid var(--border-subtle)",
					paddingBottom: "1.25rem",
					marginBottom: "2rem",
				}}
			>
				<h1>Submit Entry</h1>
				<p style={{ marginTop: "0.25rem", color: "var(--text-secondary)" }}>
					Register your repository to initiate the automated grading agent pipeline.
				</p>
			</header>

			<div className="card" style={{ padding: "2rem" }}>
				{error && (
					<div
						style={{
							background: "var(--status-failed-bg)",
							border: "1px solid var(--status-failed-border)",
							color: "var(--status-failed)",
							padding: "0.75rem 1rem",
							borderRadius: "var(--radius-sm)",
							fontSize: "0.8125rem",
							marginBottom: "1.5rem",
							lineHeight: "1.4",
						}}
					>
						{error}
					</div>
				)}

				{success && (
					<div
						style={{
							background: "var(--status-complete-bg)",
							border: "1px solid var(--status-complete-border)",
							color: "var(--status-complete)",
							padding: "0.75rem 1rem",
							borderRadius: "var(--radius-sm)",
							fontSize: "0.8125rem",
							marginBottom: "1.5rem",
							lineHeight: "1.4",
						}}
					>
						✓ Project registered successfully! Initializing evaluation agents...
					</div>
				)}

				<form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
					<div className="form-group">
						<label htmlFor="teamName" className="form-label">
							Team Name
						</label>
						<input
							type="text"
							id="teamName"
							value={teamName}
							onChange={(e) => setTeamName(e.target.value)}
							placeholder="e.g. Alpha Devs"
							disabled={isSubmitting || success}
							className="form-input"
						/>
					</div>

					<div className="form-group">
						<label htmlFor="repoUrl" className="form-label">
							GitHub Repository URL
						</label>
						<input
							type="text"
							id="repoUrl"
							value={repoUrl}
							onChange={(e) => setRepoUrl(e.target.value)}
							placeholder="https://github.com/owner/repository"
							disabled={isSubmitting || success}
							className="form-input"
						/>
					</div>

					<div className="form-group">
						<div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
							<label htmlFor="commitSha" className="form-label">
								Commit SHA
							</label>
							<span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>Optional</span>
						</div>
						<input
							type="text"
							id="commitSha"
							value={commitSha}
							onChange={(e) => setCommitSha(e.target.value)}
							placeholder="e.g. 5d4d4226b796faac11e9301b..."
							disabled={isSubmitting || success}
							className="form-input"
							style={{ fontFamily: "var(--mono)" }}
						/>
						<p style={{ color: "var(--text-tertiary)", fontSize: "0.75rem", marginTop: "0.35rem" }}>
							Leaves empty to automatically evaluate the default branch head.
						</p>
					</div>

					<div
						style={{
							display: "flex",
							justifyContent: "flex-end",
							gap: "1rem",
							marginTop: "1rem",
							borderTop: "1px solid var(--border-subtle)",
							paddingTop: "1.25rem",
						}}
					>
						<button
							type="button"
							onClick={() => navigate("/")}
							disabled={isSubmitting || success}
							className="btn btn-secondary"
							style={{ padding: "0.5rem 1rem" }}
						>
							Cancel
						</button>
						<button
							type="submit"
							disabled={isSubmitting || success}
							className="btn btn-primary"
							style={{ padding: "0.5rem 1.25rem" }}
						>
							{isSubmitting ? "Submitting..." : "Initialize Analysis"}
						</button>
					</div>
				</form>
			</div>
		</div>
	);
}
