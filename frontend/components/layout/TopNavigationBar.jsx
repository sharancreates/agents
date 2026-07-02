import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function TopNavigationBar() {
	const { user, logout } = useAuth();

	return (
		<header
			className="glass-panel"
			style={{
				margin: "1rem 2rem",
				padding: "1rem 2rem",
				display: "flex",
				justifyContent: "space-between",
				alignItems: "center",
				position: "sticky",
				top: "1rem",
				zIndex: 100,
			}}
		>
			<div style={{ display: "flex", alignItems: "center", gap: "3rem" }}>
				{/* Logo Section */}
				<div
					style={{
						display: "flex",
						alignItems: "center",
						gap: "0.5rem",
					}}
				>
					<div
						style={{
							width: "12px",
							height: "12px",
							background: "var(--accent-cyan)",
							borderRadius: "50%",
							boxShadow: "0 0 10px var(--accent-cyan)",
						}}
					></div>
					<strong
						style={{
							fontSize: "1.25rem",
							letterSpacing: "1px",
							textTransform: "uppercase",
						}}
					>
						Auto
						<span style={{ color: "var(--accent-cyan)" }}>
							Judge
						</span>
					</strong>
				</div>

				{/* Navigation Links */}
				<nav style={{ display: "flex", gap: "2rem" }}>
					<Link
						to="/"
						style={{
							color: "var(--text-secondary)",
							textDecoration: "none",
							fontWeight: 600,
							transition: "color 0.2s",
						}}
						onMouseEnter={(e) =>
							(e.target.style.color = "var(--text-primary)")
						}
						onMouseLeave={(e) =>
							(e.target.style.color = "var(--text-secondary)")
						}
					>
						Submissions
					</Link>
					<Link
						to="#"
						style={{
							color: "var(--text-secondary)",
							textDecoration: "none",
							fontWeight: 600,
							transition: "color 0.2s",
						}}
					>
						Leaderboard
					</Link>
				</nav>
			</div>

			{/* User & Auth Actions */}
			<div
				style={{
					display: "flex",
					alignItems: "center",
					gap: "1.5rem",
					fontFamily: "var(--font-mono)",
				}}
			>
				<span
					style={{
						color: "var(--text-secondary)",
						fontSize: "0.85rem",
					}}
				>
					ID: {user?.name.toUpperCase()}
				</span>
				<button
					onClick={logout}
					style={{
						background: "transparent",
						color: "var(--accent-red)",
						border: "1px solid var(--accent-red)",
						padding: "0.4rem 1rem",
						borderRadius: "4px",
						cursor: "pointer",
						fontFamily: "var(--font-mono)",
						textTransform: "uppercase",
						fontSize: "0.8rem",
						transition: "all 0.2s",
					}}
					onMouseEnter={(e) => {
						e.target.style.background = "var(--accent-red)";
						e.target.style.color = "var(--bg-void)";
					}}
					onMouseLeave={(e) => {
						e.target.style.background = "transparent";
						e.target.style.color = "var(--accent-red)";
					}}
				>
					Terminate Session
				</button>
			</div>
		</header>
	);
}
