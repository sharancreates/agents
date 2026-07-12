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
				setError("SYSTEM ERROR: CREDENTIALS CANNOT BE BLANK");
				setIsSubmitting(false);
			} else {
				login();
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
				background: "var(--bg-void)",
				backgroundImage: "radial-gradient(circle at 50% 50%, rgba(0, 229, 255, 0.08) 0%, transparent 60%)",
			}}
		>
			<div
				className="glass-panel"
				style={{
					width: "100%",
					maxWidth: "420px",
					padding: "2.5rem 2rem",
					border: "1px solid var(--glass-border)",
					boxShadow: "0 20px 40px rgba(0, 0, 0, 0.5), 0 0 25px rgba(0, 229, 255, 0.05)",
					textAlign: "center",
				}}
			>
				{/* Glowing Status Indicator logo */}
				<div
					style={{
						display: "flex",
						justifyContent: "center",
						alignItems: "center",
						gap: "0.5rem",
						marginBottom: "1.5rem",
					}}
				>
					<div
						style={{
							width: "12px",
							height: "12px",
							background: "var(--accent-cyan)",
							borderRadius: "50%",
							boxShadow: "0 0 10px var(--accent-cyan)",
							animation: "pulse 2s infinite ease-in-out",
						}}
					></div>
					<strong
						style={{
							fontSize: "1.5rem",
							letterSpacing: "2px",
							textTransform: "uppercase",
							fontFamily: "var(--font-mono)",
						}}
					>
						AUTO<span style={{ color: "var(--accent-cyan)" }}>JUDGE</span>
					</strong>
				</div>

				<h2
					style={{
						fontSize: "0.9rem",
						color: "var(--text-secondary)",
						fontFamily: "var(--font-mono)",
						letterSpacing: "1px",
						textTransform: "uppercase",
						marginBottom: "2rem",
					}}
				>
					SECURE TERMINAL SIGN-IN
				</h2>

				{error && (
					<div
						style={{
							background: "rgba(255, 0, 85, 0.1)",
							border: "1px solid var(--accent-red)",
							color: "var(--accent-red)",
							padding: "0.75rem",
							borderRadius: "4px",
							fontSize: "0.8rem",
							fontFamily: "var(--font-mono)",
							marginBottom: "1.5rem",
							textAlign: "left",
						}}
					>
						{error}
					</div>
				)}

				<form onSubmit={handleLoginSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
					<div style={{ textAlign: "left" }}>
						<label
							htmlFor="username"
							style={{
								display: "block",
								fontSize: "0.75rem",
								color: "var(--text-secondary)",
								fontFamily: "var(--font-mono)",
								textTransform: "uppercase",
								marginBottom: "0.5rem",
							}}
						>
							Operator ID
						</label>
						<input
							type="text"
							id="username"
							value={username}
							onChange={(e) => setUsername(e.target.value)}
							placeholder="Enter operator code (e.g. admin)"
							autoFocus
							style={{
								width: "100%",
								background: "rgba(0, 0, 0, 0.4)",
								border: "1px solid var(--glass-border)",
								borderRadius: "4px",
								padding: "0.75rem 1rem",
								color: "var(--text-primary)",
								fontFamily: "var(--font-mono)",
								fontSize: "0.9rem",
								outline: "none",
								transition: "border-color 0.2s, box-shadow 0.2s",
							}}
							onFocus={(e) => {
								e.target.style.borderColor = "var(--accent-cyan)";
								e.target.style.boxShadow = "0 0 10px rgba(0, 229, 255, 0.15)";
							}}
							onBlur={(e) => {
								e.target.style.borderColor = "var(--glass-border)";
								e.target.style.boxShadow = "none";
							}}
						/>
					</div>

					<div style={{ textAlign: "left" }}>
						<label
							htmlFor="password"
							style={{
								display: "block",
								fontSize: "0.75rem",
								color: "var(--text-secondary)",
								fontFamily: "var(--font-mono)",
								textTransform: "uppercase",
								marginBottom: "0.5rem",
							}}
						>
							Security Token
						</label>
						<input
							type="password"
							id="password"
							value={password}
							onChange={(e) => setPassword(e.target.value)}
							placeholder="••••••••"
							style={{
								width: "100%",
								background: "rgba(0, 0, 0, 0.4)",
								border: "1px solid var(--glass-border)",
								borderRadius: "4px",
								padding: "0.75rem 1rem",
								color: "var(--text-primary)",
								fontFamily: "var(--font-mono)",
								fontSize: "0.9rem",
								outline: "none",
								transition: "border-color 0.2s, box-shadow 0.2s",
							}}
							onFocus={(e) => {
								e.target.style.borderColor = "var(--accent-cyan)";
								e.target.style.boxShadow = "0 0 10px rgba(0, 229, 255, 0.15)";
							}}
							onBlur={(e) => {
								e.target.style.borderColor = "var(--glass-border)";
								e.target.style.boxShadow = "none";
							}}
						/>
					</div>

					<button
						type="submit"
						disabled={isSubmitting}
						style={{
							marginTop: "1rem",
							background: "transparent",
							color: "var(--accent-cyan)",
							border: "1px solid var(--accent-cyan)",
							padding: "0.8rem",
							borderRadius: "4px",
							fontSize: "0.9rem",
							fontFamily: "var(--font-mono)",
							fontWeight: "bold",
							textTransform: "uppercase",
							cursor: "pointer",
							transition: "all 0.2s",
							boxShadow: "0 0 10px rgba(0, 229, 255, 0.05)",
						}}
						onMouseEnter={(e) => {
							if (!isSubmitting) {
								e.target.style.background = "var(--accent-cyan)";
								e.target.style.color = "var(--bg-void)";
								e.target.style.boxShadow = "0 0 15px rgba(0, 229, 255, 0.3)";
							}
						}}
						onMouseLeave={(e) => {
							if (!isSubmitting) {
								e.target.style.background = "transparent";
								e.target.style.color = "var(--accent-cyan)";
								e.target.style.boxShadow = "0 0 10px rgba(0, 229, 255, 0.05)";
							}
						}}
					>
						{isSubmitting ? "AUTHORIZING ACCESS..." : "ESTABLISH SESSION"}
					</button>
				</form>

				<style>{`
					@keyframes pulse {
						0%, 100% { opacity: 0.6; transform: scale(1); }
						50% { opacity: 1; transform: scale(1.1); box-shadow: 0 0 15px var(--accent-cyan); }
					}
				`}</style>
			</div>
		</div>
	);
}
