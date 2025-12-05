"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// Types for patient journal data
export interface PatientJournalData {
  labs_and_exams: {
    youth?: {
      labs?: Record<string, string | number>;
      imaging?: Record<string, string>;
    };
    adult?: {
      labs_initial?: Record<string, string | number>;
      ekg?: string;
    };
    knee_arthrosis_period?: {
      xray?: string;
      postop?: string;
    };
    urology?: {
      PSA_trend?: number[];
      urine?: string;
      ultrasound?: string;
    };
    cardiometabolic?: Record<string, Record<string, string | number>>;
    cognitive?: {
      labs?: Record<string, string | number>;
      MMT?: number;
      clock_test?: string;
      MRT?: string;
    };
    current?: {
      labs?: Record<string, string | number>;
      ekg?: string;
      lungröntgen?: string;
      eko?: string;
    };
  };
}

export interface User {
  id: string;
  name: string;
  personnummer: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  journalData: PatientJournalData | null;
  login: (personnummer: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [journalData, setJournalData] = useState<PatientJournalData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing session on mount
  useEffect(() => {
    const storedAuth = localStorage.getItem('1177_auth');
    if (storedAuth) {
      try {
        const { user: storedUser, journalData: storedJournal } = JSON.parse(storedAuth);
        setUser(storedUser);
        setJournalData(storedJournal);
        setIsAuthenticated(true);
      } catch (e) {
        localStorage.removeItem('1177_auth');
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (personnummer: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      // Fetch journal data from backend
      const backendUrl = process.env.NEXT_PUBLIC_PYTHON_BACKEND_URL || 'http://127.0.0.1:8000';
      const response = await fetch(`${backendUrl}/api/journal`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch journal data');
      }
      
      const data = await response.json();
      
      // Create mock user (in a real app, this would come from BankID/authentication service)
      const mockUser: User = {
        id: '1',
        name: 'Erik Andersson',
        personnummer: personnummer,
      };
      
      setUser(mockUser);
      setJournalData(data);
      setIsAuthenticated(true);
      
      // Store in localStorage for persistence
      localStorage.setItem('1177_auth', JSON.stringify({
        user: mockUser,
        journalData: data,
      }));
      
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setJournalData(null);
    setIsAuthenticated(false);
    localStorage.removeItem('1177_auth');
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        user,
        journalData,
        login,
        logout,
        isLoading,
      }}
    >
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

