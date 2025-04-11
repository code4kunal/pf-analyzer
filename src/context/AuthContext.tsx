'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: string;
  role: 'admin' | 'test';
}

interface AuthContextType {
  user: User | null;
  login: (id: string, password: string) => boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  // Check for existing session on mount
  useEffect(() => {
    const storedUserId = localStorage.getItem('userId');
    if (storedUserId) {
      const role: 'admin' | 'test' = storedUserId === 'admin' ? 'admin' : 'test';
      setUser({ id: storedUserId, role });
    }
  }, []);

  const login = (id: string, password: string): boolean => {
    // Validate credentials
    if (id === 'admin' && password === 'admin123') {
      const newUser: User = { id, role: 'admin' };
      setUser(newUser);
      localStorage.setItem('userId', id);
      return true;
    } else if (id === 'test' && password === 'test123') {
      const newUser: User = { id, role: 'test' };
      setUser(newUser);
      localStorage.setItem('userId', id);
      return true;
    }
    return false;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('userId');
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 