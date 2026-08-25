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
  'org-shipper-003': {
    id: 'org-shipper-003',
    name: 'Apex Advanced Electronics',
    type: 'shipper',
    contingencyRate: 0.00
  },
  'org-swift-002': {
    id: 'org-swift-002',
    name: 'Swift Line Logistics',
    type: 'carrier',
    contingencyRate: 0.18
  }
};

export const DEMO_USERS: UserProfile[] = [
  // Org A: Broker Tenant
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
  // Org B: Shipper Tenant (Phase 6)
  {
    id: 'usr-shp-plant-mgr',
    email: 'marcus.lee@apex-electronics.com',
    name: 'Marcus Lee',
    role: 'Plant Manager / Inspector',
    organization: DEMO_ORGS['org-shipper-003']
  },
  {
    id: 'usr-shp-log-coord',
    email: 'elena.rostova@apex-electronics.com',
    name: 'Elena Rostova',
    role: 'Logistics Coordinator',
    organization: DEMO_ORGS['org-shipper-003']
  },
  {
    id: 'usr-shp-log-dir',
    email: 'david.vance@apex-electronics.com',
    name: 'David Vance',
    role: 'Logistics Director',
    organization: DEMO_ORGS['org-shipper-003']
  },
  // Org C: Carrier Tenant
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
    name: 'Rachel Adams',
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
    // 1. Check local session storage first for fast initial load
    const saved = localStorage.getItem(LOCAL_STORAGE_SESSION_KEY);
    if (saved) {
      try {
        const parsed: UserProfile = JSON.parse(saved);
        setUserProfile(parsed);
        setSession({
          access_token: `sb-token-${parsed.id}`,
          token_type: 'bearer',
          expires_in: 3600,
          refresh_token: 'sb-refresh',
          user: {
            id: parsed.id,
            email: parsed.email,
            app_metadata: { organization_id: parsed.organization.id, role: parsed.role },
            user_metadata: { name: parsed.name },
            aud: 'authenticated',
            created_at: new Date().toISOString()
          }
        } as Session);
      } catch {
        localStorage.removeItem(LOCAL_STORAGE_SESSION_KEY);
      }
    }

    // 2. Check Supabase Auth session
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user) {
        setSession(session);
        setUser(session.user);
        syncUserProfileFromUser(session.user);
      }
      setLoading(false);
    }).catch(() => {
      setLoading(false);
    });

    // 3. Listen to Auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        setSession(session);
        setUser(session.user);
        syncUserProfileFromUser(session.user);
      }
      setLoading(false);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const syncUserProfileFromUser = (sbUser: User) => {
    const userEmail = sbUser.email || 'user@company.com';
    const emailHandle = userEmail.split('@')[0].replace(/[^a-z0-9]/gi, '-').toLowerCase();
    const defaultOrgId = `org-user-${emailHandle}`;

    const orgId = sbUser.app_metadata?.organization_id || sbUser.user_metadata?.organization_id || defaultOrgId;
    const role = (sbUser.app_metadata?.role || sbUser.user_metadata?.role || 'Claims Manager') as RBACRole;
    const org = DEMO_ORGS[orgId] || {
      id: orgId,
      name: sbUser.user_metadata?.org_name || `${userEmail.split('@')[0]} Logistics`,
      type: 'broker',
      contingencyRate: 0.20
    };

    const profile: UserProfile = {
      id: sbUser.id,
      email: userEmail,
      name: sbUser.user_metadata?.name || userEmail.split('@')[0] || 'Authenticated User',
      role,
      organization: org
    };
    setUserProfile(profile);
    localStorage.setItem(LOCAL_STORAGE_SESSION_KEY, JSON.stringify(profile));
  };

  const loginAsAnyUser = (userEmail: string) => {
    const cleanEmail = userEmail.trim().toLowerCase();

    // Check if it matches a pre-configured demo user
    const demoMatch = DEMO_USERS.find(u => u.email.toLowerCase() === cleanEmail);
    if (demoMatch) {
      loginAsDemoUser(demoMatch.email);
      return;
    }

    // Determine organization based on email domain or generate unique new organization for new accounts
    let role: RBACRole = 'Claims Manager';
    let org: UserOrganization;

    if (cleanEmail.includes('electronics') || cleanEmail.includes('shipper')) {
      org = DEMO_ORGS['org-shipper-003']; // Pre-configured Shipper demo org
      role = 'Plant Manager / Inspector';
    } else if (cleanEmail.includes('swift') || cleanEmail.includes('carrier')) {
      org = DEMO_ORGS['org-swift-002']; // Pre-configured Carrier demo org
      role = 'Admin';
    } else {
      // Create a clean, isolated brand-new organization for this new user account
      const usernameHandle = cleanEmail.split('@')[0].replace(/[^a-z0-9]/gi, '-').toLowerCase();
      const orgId = `org-user-${usernameHandle}`;
      const emailNamePart = cleanEmail.split('@')[0] || 'User';
      const formattedName = emailNamePart
        .replace(/[._-]/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase());

      org = {
        id: orgId,
        name: `${formattedName} Logistics`,
        type: 'broker',
        contingencyRate: 0.20
      };
    }

    const emailNamePart = cleanEmail.split('@')[0] || 'User';
    const formattedName = emailNamePart
      .replace(/[._-]/g, ' ')
      .replace(/\b\w/g, c => c.toUpperCase());

    const customProfile: UserProfile = {
      id: `usr-${Date.now()}`,
      email: cleanEmail,
      name: formattedName || 'Authenticated User',
      role,
      organization: org
    };

    const mockSbSession = {
      access_token: `sb-token-${customProfile.id}`,
      token_type: 'bearer',
      expires_in: 3600,
      refresh_token: 'sb-refresh',
      user: {
        id: customProfile.id,
        email: customProfile.email,
        app_metadata: { organization_id: org.id, role },
        user_metadata: { name: customProfile.name },
        aud: 'authenticated',
        created_at: new Date().toISOString()
      }
    } as Session;

    setUserProfile(customProfile);
    setSession(mockSbSession);
    setUser(mockSbSession.user);
    localStorage.setItem(LOCAL_STORAGE_SESSION_KEY, JSON.stringify(customProfile));
  };

  const login = async (email: string, password = 'Password123!') => {
    setLoading(true);
    try {
      // 1. Attempt Supabase Auth login
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (!error && data.user && data.session) {
        setSession(data.session);
        setUser(data.user);
        syncUserProfileFromUser(data.user);
        return;
      }

      // 2. If account does not exist in Supabase yet, create it automatically so credentials & progress persist in Supabase DB
      if (error && (error.message?.includes('Invalid login credentials') || error.message?.includes('User not found'))) {
        const signupRes = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: {
              name: email.split('@')[0],
              org_name: `${email.split('@')[0]} Logistics`
            }
          }
        });

        if (signupRes.data.user && signupRes.data.session) {
          setSession(signupRes.data.session);
          setUser(signupRes.data.user);
          syncUserProfileFromUser(signupRes.data.user);
          return;
        }
      }

      // 3. Fallback to seamless tenant user creation
      loginAsAnyUser(email);
    } catch {
      loginAsAnyUser(email);
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
