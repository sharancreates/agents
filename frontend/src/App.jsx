import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "../context/AuthContext";
import MainLayout from "../components/layout/MainLayout";
import Dashboard from "../pages/Dashboard";
import SubmissionDetail from "../pages/SubmissionDetail";
import Login from "../pages/Login";

function App() {
	return (
		<AuthProvider>
			<BrowserRouter>
				<Routes>
					<Route path="/login" element={<Login />} />

					<Route element={<MainLayout />}>
						<Route path="/" element={<Dashboard />} />
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
