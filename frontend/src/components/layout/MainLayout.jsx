import { Outlet, Navigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import TopNavigationBar from "./TopNavigationBar";

export default function MainLayout() {
	const { user } = useAuth();

	// Route protection: If no user is logged in, redirect to the login page
	if (!user) {
		return <Navigate to="/login" replace />;
	}

	return (
		<div
			style={{
				minHeight: "100vh",
				display: "flex",
				flexDirection: "column",
			}}
		>
			{/* Our newly modularized navigation bar */}
			<TopNavigationBar />

			{/* Main Content Area where child routes will render */}
			<main
				style={{
					padding: "0 2rem 2rem 2rem",
					flex: 1,
					display: "flex",
					flexDirection: "column",
				}}
			>
				<Outlet />
			</main>
		</div>
	);
}
