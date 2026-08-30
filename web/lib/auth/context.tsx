"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface User {
  id: string;
  firstName: string;
  lastName: string;
  displayName: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const DEFAULT_USER: User = {
  id: "user-001",
  firstName: process.env.NEXT_PUBLIC_USER_FIRST_NAME || "John",
  lastName: process.env.NEXT_PUBLIC_USER_LAST_NAME || "Doe",
  displayName: process.env.NEXT_PUBLIC_USER_DISPLAY_NAME || "Dr. Smith",
  role: process.env.NEXT_PUBLIC_USER_ROLE || "Cardiologist",
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const stored = localStorage.getItem("aegis-user");
      return stored ? JSON.parse(stored) : null;
    } catch {
      localStorage.removeItem("aegis-user");
      return null;
    }
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string): Promise<boolean> => {
    // For demo purposes, accept any non-empty credentials
    // In production, this would call the backend auth endpoint
    if (username && password) {
      const newUser = { ...DEFAULT_USER, id: `user-${username}` };
      setUser(newUser);
      localStorage.setItem("aegis-user", JSON.stringify(newUser));
      return true;
    }
    return false;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("aegis-user");
    localStorage.removeItem("aegis-api-key");
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
