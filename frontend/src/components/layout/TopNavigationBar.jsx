import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function TopNavigationBar() {
	const { user, logout } = useAuth();
	const location = useLocation();

	const isSubmissionsActive = location.pathname === "/" || (location.pathname.startsWith("/submission") && !location.pathname.includes("/submit") && !location.pathname.includes("/leaderboard"));
	const isSubmitActive = location.pathname === "/submit";
	const isLeaderboardActive = location.pathname === "/leaderboard";

	return (
		<header
			style={{
				position: "sticky",
				top: 0,
				zIndex: 100,
				backgroundColor: "rgba(9, 9, 11, 0.75)",
				backdropFilter: "blur(12px)",
				WebkitBackdropFilter: "blur(12px)",
				borderBottom: "1px solid var(--border-subtle)",
				width: "100%",
				marginBottom: "2rem",
			}}
		>
			<div
				className="container"
				style={{
					display: "flex",
					justifyContent: "space-between",
					alignItems: "center",
					height: "3.75rem",
				}}
			>
				<div style={{ display: "flex", alignItems: "center", gap: "2.5rem" }}>
					{/* Logo Section */}
					<Link to="/" style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "inherit" }}>
						<div
							style={{
								width: "8px",
								height: "8px",
								background: "var(--accent)",
								borderRadius: "50%",
								boxShadow: "0 0 10px rgba(99, 102, 241, 0.5)",
							}}
						></div>
						<strong
							style={{
								fontSize: "0.95rem",
								fontWeight: 600,
								letterSpacing: "-0.01em",
							}}
						>
							AutoJudge
						</strong>
					</Link>

					{/* Navigation Links */}
					<nav style={{ display: "flex", gap: "1.5rem" }}>
						<Link
							to="/"
							style={{
								color: isSubmissionsActive ? "var(--text-primary)" : "var(--text-secondary)",
								fontSize: "0.875rem",
								fontWeight: 500,
								transition: "color var(--transition)",
							}}
						>
							Submissions
						</Link>
						<Link
							to="/submit"
							style={{
								color: isSubmitActive ? "var(--text-primary)" : "var(--text-secondary)",
								fontSize: "0.875rem",
								fontWeight: 500,
								transition: "color var(--transition)",
							}}
						>
							Submit Entry
						</Link>
						<Link
							to="/leaderboard"
							style={{
								color: isLeaderboardActive ? "var(--text-primary)" : "var(--text-secondary)",
								fontSize: "0.875rem",
								fontWeight: 500,
								transition: "color var(--transition)",
							}}
						>
							Leaderboard
						</Link>
					</nav>
				</div>

				{/* User & Auth Actions */}
				<div style={{ display: "flex", alignItems: "center", gap: "1.25rem" }}>
					<span
						style={{
							color: "var(--text-secondary)",
							fontSize: "0.8rem",
							fontFamily: "var(--mono)",
							borderRight: "1px solid var(--border-subtle)",
							paddingRight: "1.25rem",
						}}
					>
						operator://{user?.name.toLowerCase()}
					</span>
					<button
						onClick={logout}
						className="btn btn-secondary"
						style={{
							padding: "0.35rem 0.75rem",
							fontSize: "0.75rem",
							fontWeight: 500,
						}}
					>
						Sign Out
					</button>
				</div>
			</div>
		</header>
	);
}
