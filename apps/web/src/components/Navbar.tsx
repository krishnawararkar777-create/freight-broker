import React, { useEffect, useState } from 'react';
import { ShieldCheck, FileText, LayoutDashboard, Receipt, Scale, Activity, Upload, Sparkles, Lock, Server, LogOut } from 'lucide-react';
import type { HealthStatus } from '@algolyra/shared';
import type { UserProfile, UserOrganization, RBACRole } from '../types/auth';
import { fetchHealthStatus } from '../lib/api-client';

interface NavbarProps {
  activeTab: 'dashboard' | 'analytics' | 'review' | 'ledger' | 'rules' | 'audit';
  setActiveTab: (tab: 'dashboard' | 'analytics' | 'review' | 'ledger' | 'rules' | 'audit') => void;
  org: UserOrganization | null;
  role: RBACRole | null;
  userProfile: UserProfile | null;
  onLogout: () => void;
  onOpenUpload: () => void;
  selectedClaimNumber?: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  org,
  role,
  userProfile,
  onLogout,
  onOpenUpload,
  selectedClaimNumber
}) => {
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    fetchHealthStatus()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  const contingencyRateText = org ? `${(org.contingencyRate * 100).toFixed(0)}%` : '20%';

  return (
    <header className="bg-black border-b border-zinc-800 text-zinc-100 sticky top-0 z-50 shadow-md">
      <div className="bg-zinc-950 px-4 py-1.5 border-b border-zinc-800/80 text-xs flex justify-between items-center font-mono">
        <div className="flex items-center space-x-3 text-zinc-300">
          <span className="inline-flex items-center gap-1.5 font-semibold text-white">
            <Sparkles className="w-3.5 h-3.5 text-zinc-400" /> MARAJET PLATFORM (v4.0)
          </span>
          <span className="text-zinc-700">|</span>
          <span className="text-zinc-400">
            Model: <strong className="text-zinc-200">Contingency Fee ({contingencyRateText})</strong> — $0 Fee on $0 Recovered
          </span>
        </div>
        <div className="flex items-center space-x-3 text-zinc-400">
          <span className="inline-flex items-center gap-1 bg-zinc-900 text-zinc-300 px-2 py-0.5 rounded border border-zinc-800 text-[11px] font-medium">
            <Server className="w-3 h-3 text-zinc-400" />
            API: {health ? `${health.app} (${health.status.toUpperCase()})` : 'Connecting...'}
          </span>
          <span className="inline-flex items-center gap-1 bg-zinc-900 text-zinc-300 px-2 py-0.5 rounded border border-zinc-800 text-[11px] font-medium">
            <Lock className="w-3 h-3 text-emerald-400" /> Server Approval Guard Active
          </span>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-4">
            <div 
              onClick={() => setActiveTab('dashboard')}
              className="flex items-center space-x-3 cursor-pointer group"
            >
              <div className="w-9 h-9 rounded-xl bg-white flex items-center justify-center shadow-sm group-hover:bg-zinc-200 transition-colors">
                <ShieldCheck className="w-5 h-5 text-black" />
              </div>
              <div>
                <span className="text-lg font-bold tracking-tight text-white">
                  MARAJET
                </span>
                <div className="text-[10px] text-zinc-500 uppercase tracking-wider font-mono">
                  Cargo Claims Recovery
                </div>
              </div>
            </div>

            {org && (
              <div className="hidden md:flex items-center space-x-2 pl-4 border-l border-zinc-800">
                <span className="text-xs bg-zinc-900 text-zinc-200 px-2.5 py-1 rounded-md border border-zinc-800 font-medium">
                  🏢 {org.name}
                </span>
                {role && (
                  <span className="text-[10px] font-mono font-semibold bg-zinc-900 text-zinc-300 border border-zinc-700 px-2 py-0.5 rounded">
                    {role}
                  </span>
                )}
              </div>
            )}
          </div>

          <nav className="flex items-center space-x-1 sm:space-x-2">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 cursor-pointer ${
                activeTab === 'dashboard'
                  ? 'bg-white text-black font-semibold shadow-sm'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </button>

            <button
              onClick={() => setActiveTab('analytics')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 cursor-pointer ${
                activeTab === 'analytics'
                  ? 'bg-white text-black font-semibold shadow-sm'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
              }`}
            >
              <Activity className="w-4 h-4" />
              Executive Analytics
            </button>

            <button
              onClick={() => setActiveTab('review')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 relative cursor-pointer ${
                activeTab === 'review'
                  ? 'bg-white text-black font-semibold shadow-sm'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
              }`}
            >
              <FileText className="w-4 h-4" />
              Review Workspace
              {selectedClaimNumber && (
                <span className="ml-1 text-[10px] bg-zinc-800 text-zinc-200 font-mono font-bold px-1.5 py-0.5 rounded border border-zinc-700">
                  {selectedClaimNumber}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('ledger')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 cursor-pointer ${
                activeTab === 'ledger'
                  ? 'bg-white text-black font-semibold shadow-sm'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
              }`}
            >
              <Receipt className="w-4 h-4" />
              Recovery Ledger
            </button>

            <button
              onClick={() => setActiveTab('rules')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 cursor-pointer ${
                activeTab === 'rules'
                  ? 'bg-white text-black font-semibold shadow-sm'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
              }`}
            >
              <Scale className="w-4 h-4" />
              Carrier Rules
            </button>

            <button
              onClick={() => setActiveTab('audit')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 cursor-pointer ${
                activeTab === 'audit'
                  ? 'bg-white text-black font-semibold shadow-sm'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
              }`}
            >
              <Activity className="w-4 h-4" />
              Audit Log
            </button>
          </nav>

          <div className="flex items-center space-x-3">
            <button
              onClick={onOpenUpload}
              className="bg-white hover:bg-zinc-200 text-black px-3 py-1.5 rounded-lg text-xs font-semibold shadow-sm flex items-center gap-1.5 transition-all cursor-pointer"
            >
              <Upload className="w-3.5 h-3.5" />
              Ingest Claim
            </button>

            {userProfile && (
              <div className="flex items-center space-x-2 pl-2 border-l border-zinc-800">
                <div className="hidden lg:block text-right">
                  <div className="text-xs font-semibold text-zinc-200">{userProfile.name}</div>
                  <div className="text-[10px] text-zinc-500 font-mono truncate max-w-[120px]">{userProfile.email}</div>
                </div>

                <button
                  onClick={onLogout}
                  title="Sign Out of Workspace"
                  className="p-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-700 rounded-lg text-zinc-300 hover:text-white transition-all cursor-pointer flex items-center space-x-1 text-xs font-medium"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

