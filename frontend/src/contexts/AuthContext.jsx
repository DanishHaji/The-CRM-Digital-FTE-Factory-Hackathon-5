import { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/router';

const AuthContext = createContext({});

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Check for existing session on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (error) {
        console.error('Error parsing stored user:', error);
        localStorage.removeItem('user');
      }
    }
    setLoading(false);
  }, []);

  const signup = async (email, password, name) => {
    try {
      // For MVP, we'll use localStorage for authentication
      // In production, this should call the backend API
      const newUser = {
        id: Date.now().toString(),
        email,
        name,
        createdAt: new Date().toISOString(),
      };

      localStorage.setItem('user', JSON.stringify(newUser));
      setUser(newUser);

      return { success: true, user: newUser };
    } catch (error) {
      console.error('Signup error:', error);
      return { success: false, error: error.message };
    }
  };

  const login = async (email, password) => {
    try {
      // For MVP, we'll use localStorage for authentication
      // In production, this should call the backend API and verify credentials
      const storedUser = localStorage.getItem('user');

      if (storedUser) {
        const parsedUser = JSON.parse(storedUser);
        if (parsedUser.email === email) {
          setUser(parsedUser);
          return { success: true, user: parsedUser };
        }
      }

      // If no user found, create a new one (simplified for MVP)
      const newUser = {
        id: Date.now().toString(),
        email,
        name: email.split('@')[0],
        createdAt: new Date().toISOString(),
      };

      localStorage.setItem('user', JSON.stringify(newUser));
      setUser(newUser);

      return { success: true, user: newUser };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: error.message };
    }
  };

  const logout = () => {
    localStorage.removeItem('user');
    setUser(null);
    router.push('/');
  };

  const value = {
    user,
    loading,
    signup,
    login,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
