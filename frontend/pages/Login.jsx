import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
	const { login } = useAuth();
	const navigate = useNavigate();

	const handleLogin = () => {
		login();
		// Redirect to the dashboard after "successful" login
		navigate("/");
	};

	return (
		<div style={{ padding: "2rem", textAlign: "center" }}>
			<h1>Hackathon Auto-Judge Login</h1>
			<p>Please sign in to view the evaluation dashboard.</p>
			<button
				onClick={handleLogin}
				style={{
					padding: "0.5rem 1rem",
					fontSize: "1.1rem",
					cursor: "pointer",
				}}
			>
				Sign In (Mock)
			</button>
		</div>
	);
}
