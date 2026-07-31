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
		<div className="app-container">
			{/* Our newly modularized navigation bar */}
			<TopNavigationBar />

			{/* Main Content Area where child routes will render */}
			<main className="container" style={{ flex: 1, paddingBottom: "3rem" }}>
				<Outlet />
			</main>
		</div>
	);
}
