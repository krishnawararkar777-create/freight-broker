import React, { createContext, useContext, useState, useEffect } from 'react';
import type { Session, User } from '@supabase/supabase-js';
import { supabase } from '../lib/supabase';
import type { RBACRole, UserOrganization, UserProfile } from '../types/auth';

export const DEMO_ORGS: Record<string, UserOrganization> = {
  'org-apex-001': {
    id: 'org-apex-001',
    name: 'Apex Freight Brokers',
    type: 'broker',
    contingencyRate: 0.20
  },
  'org-swift-002': {
    id: 'org-swift-002',
    name: 'Swift Line Logistics',
    type: 'carrier',
    contingencyRate: 0.18
  }
};

export const DEMO_USERS: UserProfile[] = [
  {
    id: 'usr-apex-mgr',
    email: 'sarah.jenkins@apex.com',
    name: 'Sarah Jenkins',
    role: 'Claims Manager',
    organization: DEMO_ORGS['org-apex-001']
  },
  {
    id: 'usr-apex-adm',
    email: 'admin@apex.com',
    name: 'Marcus Vance',
    role: 'Admin',
    organization: DEMO_ORGS['org-apex-001']
  },
  {
    id: 'usr-apex-op',
    email: 'operator@apex.com',
    name: 'Dave Miller',
    role: 'Claims Operator',
    organization: DEMO_ORGS['org-apex-001']
  },
  {
    id: 'usr-swift-adm',
    email: 'alex.vance@swift.com',
    name: 'Alex Vance',
    role: 'Admin',
    organization: DEMO_ORGS['org-swift-002']
  },
  {
    id: 'usr-swift-fin',
    email: 'finance@swift.com',
    name: 'Elena Rostova',
    role: 'Finance',
    organization: DEMO_ORGS['org-swift-002']
  }
];

interface AuthContextType {
  session: Session | null;
  user: User | null;
  userProfile: UserProfile | null;
  org: UserOrganization | null;
  role: RBACRole | null;
  loading: boolean;
  login: (email: string, password?: string) => Promise<void>;
  loginAsDemoUser: (userEmail: string) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const LOCAL_STORAGE_SESSION_KEY = 'marajet_auth_profile';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // 1. Initial Supabase session check
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (session?.user) {
        syncUserProfileFromUser(session.user);
      } else {
        restoreLocalDemoSession();
      }
      setLoading(false);
    });

    // 2. Subscribe to auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (session?.user) {
        syncUserProfileFromUser(session.user);
      } else {
        restoreLocalDemoSession();
      }
      setLoading(false);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const restoreLocalDemoSession = () => {
    try {
      const saved = localStorage.getItem(LOCAL_STORAGE_SESSION_KEY);
      if (saved) {
        const parsed: UserProfile = JSON.parse(saved);
        setUserProfile(parsed);
        // Synthesize dummy session object if logged in via demo switcher
        setSession({
          access_token: `demo-token-${parsed.id}`,
          token_type: 'bearer',
          expires_in: 3600,
          refresh_token: 'demo-refresh',
          user: {
            id: parsed.id,
            email: parsed.email,
            app_metadata: { organization_id: parsed.organization.id, role: parsed.role },
            user_metadata: { name: parsed.name },
            aud: 'authenticated',
            created_at: new Date().toISOString()
          }
        } as Session);
      } else {
        setUserProfile(null);
        setSession(null);
      }
    } catch {
      setUserProfile(null);
      setSession(null);
    }
  };

  const syncUserProfileFromUser = (sbUser: User) => {
    const orgId = sbUser.app_metadata?.organization_id || sbUser.user_metadata?.organization_id || 'org-apex-001';
    const role = (sbUser.app_metadata?.role || sbUser.user_metadata?.role || 'Claims Manager') as RBACRole;
    const org = DEMO_ORGS[orgId] || DEMO_ORGS['org-apex-001'];

    const profile: UserProfile = {
      id: sbUser.id,
      email: sbUser.email || 'user@company.com',
      name: sbUser.user_metadata?.name || sbUser.email?.split('@')[0] || 'User',
      role,
      organization: org
    };
    setUserProfile(profile);
    localStorage.setItem(LOCAL_STORAGE_SESSION_KEY, JSON.stringify(profile));
  };

  const login = async (email: string, password = 'Password123!') => {
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) {
        // Fallback for demo users if Supabase auth backend is unseeded
        const demoMatch = DEMO_USERS.find(u => u.email.toLowerCase() === email.toLowerCase());
        if (demoMatch) {
          loginAsDemoUser(demoMatch.email);
          return;
        }
        throw error;
      }
      if (data.user) {
        syncUserProfileFromUser(data.user);
      }
    } finally {
      setLoading(false);
    }
  };

  const loginAsDemoUser = (userEmail: string) => {
    const demo = DEMO_USERS.find(u => u.email.toLowerCase() === userEmail.toLowerCase()) || DEMO_USERS[0];
    setUserProfile(demo);
    const mockSbSession = {
      access_token: `demo-token-${demo.id}`,
      token_type: 'bearer',
      expires_in: 3600,
      refresh_token: 'demo-refresh',
      user: {
        id: demo.id,
        email: demo.email,
        app_metadata: { organization_id: demo.organization.id, role: demo.role },
        user_metadata: { name: demo.name },
        aud: 'authenticated',
        created_at: new Date().toISOString()
      }
    } as Session;

    setSession(mockSbSession);
    setUser(mockSbSession.user);
    localStorage.setItem(LOCAL_STORAGE_SESSION_KEY, JSON.stringify(demo));
  };

  const logout = async () => {
    setLoading(true);
    try {
      await supabase.auth.signOut();
    } catch {
      // Ignore
    } finally {
      localStorage.removeItem(LOCAL_STORAGE_SESSION_KEY);
      setSession(null);
      setUser(null);
      setUserProfile(null);
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        session,
        user,
        userProfile,
        org: userProfile?.organization || null,
        role: userProfile?.role || null,
        loading,
        login,
        loginAsDemoUser,
        logout
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
