import { createContext, useState, useContext } from "react";

// Create the context
const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
	// Dynamic session check from localStorage
	const [user, setUser] = useState(() => {
		const saved = localStorage.getItem("operator_user");
		try {
			return saved ? JSON.parse(saved) : null;
		} catch {
			return null;
		}
	});

	const login = (username) => {
		const sessionUser = { name: username || "operator", role: "admin" };
		setUser(sessionUser);
		localStorage.setItem("operator_user", JSON.stringify(sessionUser));
	};

	const logout = () => {
		setUser(null);
		localStorage.removeItem("operator_user");
	};

	return (
		<AuthContext.Provider value={{ user, login, logout }}>
			{children}
		</AuthContext.Provider>
	);
};

// Custom hook for easy access in your components
// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext);
