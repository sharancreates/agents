import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
	const { login } = useAuth();
	const navigate = useNavigate();
	const [username, setUsername] = useState("");
	const [password, setPassword] = useState("");
	const [error, setError] = useState("");
	const [isSubmitting, setIsSubmitting] = useState(false);

	const handleLoginSubmit = (e) => {
		e.preventDefault();
		setError("");
		setIsSubmitting(true);

		// Simple simulation of authentication with feedback
		setTimeout(() => {
			if (username.trim() === "" || password.trim() === "") {
				setError("Invalid credentials. Operator code and token cannot be blank.");
				setIsSubmitting(false);
			} else {
				login(username);
				navigate("/");
			}
		}, 800);
	};

	return (
		<div
			style={{
				minHeight: "100vh",
				display: "flex",
				justifyContent: "center",
				alignItems: "center",
				padding: "1.5rem",
				backgroundColor: "var(--bg-page)",
				backgroundImage: "radial-gradient(circle at 50% 50%, rgba(99, 102, 241, 0.05) 0%, transparent 60%)",
			}}
		>
			<div
				className="card"
				style={{
					width: "100%",
					maxWidth: "400px",
					padding: "2.5rem 2rem",
					boxShadow: "0 10px 30px rgba(0, 0, 0, 0.5)",
				}}
			>
				{/* Top Branding Section */}
				<div
					style={{
						display: "flex",
						flexDirection: "column",
						alignItems: "center",
						gap: "0.5rem",
						marginBottom: "2rem",
						textAlign: "center",
					}}
				>
					<div
						style={{
							width: "10px",
							height: "10px",
							background: "var(--accent)",
							borderRadius: "50%",
							boxShadow: "0 0 10px rgba(99, 102, 241, 0.5)",
						}}
					></div>
					<h1
						style={{
							fontSize: "1.25rem",
							fontWeight: 600,
							letterSpacing: "-0.01em",
						}}
					>
						AutoJudge
					</h1>
					<p style={{ color: "var(--text-secondary)", fontSize: "0.8rem", marginTop: "0.25rem" }}>
						Enter operator details to establish session
					</p>
				</div>

				{error && (
					<div
						style={{
							background: "var(--status-failed-bg)",
							border: "1px solid var(--status-failed-border)",
							color: "var(--status-failed)",
							padding: "0.75rem",
							borderRadius: "var(--radius-sm)",
							fontSize: "0.8125rem",
							marginBottom: "1.5rem",
							textAlign: "left",
							lineHeight: "1.4",
						}}
					>
						{error}
					</div>
				)}

				<form onSubmit={handleLoginSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
					<div className="form-group">
						<label htmlFor="username" className="form-label">
							Operator ID
						</label>
						<input
							type="text"
							id="username"
							value={username}
							onChange={(e) => setUsername(e.target.value)}
							placeholder="e.g. admin"
							autoFocus
							className="form-input"
						/>
					</div>

					<div className="form-group">
						<label htmlFor="password" className="form-label">
							Security Token
						</label>
						<input
							type="password"
							id="password"
							value={password}
							onChange={(e) => setPassword(e.target.value)}
							placeholder="••••••••"
							className="form-input"
						/>
					</div>

					<button
						type="submit"
						disabled={isSubmitting}
						className="btn btn-primary"
						style={{
							marginTop: "0.75rem",
							width: "100%",
							height: "2.75rem",
						}}
					>
						{isSubmitting ? "Establishing Session..." : "Sign In"}
					</button>
				</form>
			</div>
		</div>
	);
}
