import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import MainLayout from "./components/layout/MainLayout";
import Dashboard from "./pages/Dashboard";
import SubmissionDetail from "./pages/SubmissionDetail";
import Submit from "./pages/Submit";
import Login from "./pages/Login";
import Leaderboard from "./pages/Leaderboard";

function App() {
	return (
		<AuthProvider>
			<BrowserRouter>
				<Routes>
					<Route path="/login" element={<Login />} />

					<Route element={<MainLayout />}>
						<Route path="/" element={<Dashboard />} />
						<Route path="/submit" element={<Submit />} />
						<Route path="/leaderboard" element={<Leaderboard />} />
						<Route
							path="/submission/:id"
							element={<SubmissionDetail />}
						/>
					</Route>
				</Routes>
			</BrowserRouter>
		</AuthProvider>
	);
}

export default App;
