import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { User, AuthTokens, GoogleAuthPayload } from '../types';
import { api } from '../services/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  googleClientId: string;
  isGoogleAuthEnabled: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, role: string) => Promise<void>;
  loginWithGoogle: (payload: GoogleAuthPayload) => Promise<User>;
  logout: () => Promise<void>;
  demoLogin: (role: 'admin' | 'analyst' | 'viewer') => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [googleClientId, setGoogleClientId] = useState<string>(
    import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
  );
  const [isGoogleAuthEnabled, setIsGoogleAuthEnabled] = useState<boolean>(false);

  useEffect(() => {
    const initializeAuth = async () => {
      // 1. Fetch current user if token exists
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const currentUser = await api.getCurrentUser();
          setUser(currentUser);
        } catch (error) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setUser(null);
        }
      }

      // 2. Fetch Google OAuth Configuration from backend
      try {
        const gConfig = await api.getGoogleConfig();
        if (gConfig.client_id) {
          setGoogleClientId(gConfig.client_id);
          setIsGoogleAuthEnabled(true);
        } else if (import.meta.env.VITE_GOOGLE_CLIENT_ID) {
          setGoogleClientId(import.meta.env.VITE_GOOGLE_CLIENT_ID);
          setIsGoogleAuthEnabled(true);
        }
      } catch (err) {
        console.warn('Could not fetch backend Google Auth config:', err);
      }

      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const handleTokens = (tokens: AuthTokens): User => {
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
    setUser(tokens.user);
    return tokens.user;
  };

  const login = async (email: string, password: string) => {
    const tokens = await api.login(email, password);
    handleTokens(tokens);
  };

  const register = async (email: string, password: string, fullName: string, role: string) => {
    const tokens = await api.register(email, password, fullName, role);
    handleTokens(tokens);
  };

  const loginWithGoogle = async (payload: GoogleAuthPayload): Promise<User> => {
    const tokens = await api.googleAuth(payload);
    return handleTokens(tokens);
  };

  const logout = async () => {
    await api.logout();
    setUser(null);
  };

  const demoLogin = async (role: 'admin' | 'analyst' | 'viewer') => {
    const credentials = {
      admin: { email: 'admin@company.com', password: 'Admin@123456' },
      analyst: { email: 'analyst@company.com', password: 'Analyst@123456' },
      viewer: { email: 'viewer@company.com', password: 'Viewer@123456' },
    };
    const { email, password } = credentials[role];
    await login(email, password);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        googleClientId,
        isGoogleAuthEnabled,
        login,
        register,
        loginWithGoogle,
        logout,
        demoLogin,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
