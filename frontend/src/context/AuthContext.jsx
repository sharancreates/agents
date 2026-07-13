import { createContext, useState, useContext } from "react";

// Create the context
const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
	// Simulating a logged-in state.
	// Change this to 'null' if you want to test the logged-out view first!
	const [user, setUser] = useState({ name: "Demo Judge", role: "admin" });

	const login = () => {
		// In Week 4, this will be replaced with real JWT logic
		setUser({ name: "Demo Judge", role: "admin" });
	};

	const logout = () => {
		setUser(null);
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
