import React, { useEffect, useState } from 'react';
import { ShieldCheck, FileText, LayoutDashboard, Receipt, Scale, Activity, Upload, Sparkles, Lock, Server, LogOut } from 'lucide-react';
import type { HealthStatus } from '@algolyra/shared';
import type { UserProfile, UserOrganization, RBACRole } from '../types/auth';
import { fetchHealthStatus } from '../lib/api-client';

interface NavbarProps {
  activeTab: 'dashboard' | 'review' | 'ledger' | 'rules' | 'audit';
  setActiveTab: (tab: 'dashboard' | 'review' | 'ledger' | 'rules' | 'audit') => void;
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
    <header className="bg-slate-900 border-b border-slate-800 text-slate-100 sticky top-0 z-50 shadow-xl">
      <div className="bg-gradient-to-r from-slate-950 via-cyan-950/40 to-slate-950 px-4 py-1.5 border-b border-slate-800/80 text-xs flex justify-between items-center">
        <div className="flex items-center space-x-3 text-slate-300">
          <span className="inline-flex items-center gap-1.5 font-semibold text-cyan-400">
            <Sparkles className="w-3.5 h-3.5" /> ALGOLYRA OPERATING SYSTEM (v4)
          </span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-300 font-mono">
            Model: <strong className="text-emerald-400">Contingency Fee ({contingencyRateText})</strong> — $0 Fee on $0 Recovered
          </span>
        </div>
        <div className="flex items-center space-x-3 text-slate-400">
          <span className="inline-flex items-center gap-1 bg-cyan-500/10 text-cyan-400 px-2 py-0.5 rounded border border-cyan-500/20 font-medium">
            <Server className="w-3 h-3" />
            API: {health ? `${health.app} (${health.status.toUpperCase()})` : 'Connecting...'}
          </span>
          <span className="inline-flex items-center gap-1 bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/20 font-medium">
            <Lock className="w-3 h-3" /> Server-Side Human Approval Guard Active
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
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 group-hover:scale-105 transition-transform">
                <ShieldCheck className="w-6 h-6 text-white" />
              </div>
              <div>
                <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-cyan-400 bg-clip-text text-transparent">
                  ALGOLYRA
                </span>
                <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                  Freight Cargo Claims Recovery
                </div>
              </div>
            </div>

            {org && (
              <div className="hidden md:flex items-center space-x-2 pl-4 border-l border-slate-800">
                <span className="text-xs bg-slate-800/80 text-slate-200 px-2.5 py-1 rounded-md border border-slate-700 font-medium">
                  🏢 {org.name}
                </span>
                {role && (
                  <span className="text-[10px] font-mono font-semibold bg-cyan-950 text-cyan-300 border border-cyan-800/80 px-2 py-0.5 rounded">
                    {role}
                  </span>
                )}
              </div>
            )}
          </div>

          <nav className="flex items-center space-x-1 sm:space-x-2">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                activeTab === 'dashboard'
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </button>

            <button
              onClick={() => setActiveTab('review')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 relative ${
                activeTab === 'review'
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <FileText className="w-4 h-4" />
              Human Review Workspace
              {selectedClaimNumber && (
                <span className="ml-1 text-[10px] bg-cyan-500 text-slate-950 font-bold px-1.5 py-0.5 rounded">
                  {selectedClaimNumber}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('ledger')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                activeTab === 'ledger'
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Receipt className="w-4 h-4" />
              Recovery & Fee Ledger
            </button>

            <button
              onClick={() => setActiveTab('rules')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                activeTab === 'rules'
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Scale className="w-4 h-4" />
              Carrier Rules Engine
            </button>

            <button
              onClick={() => setActiveTab('audit')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                activeTab === 'audit'
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Activity className="w-4 h-4" />
              AI Telemetry & Audit
            </button>
          </nav>

          <div className="flex items-center space-x-3">
            <button
              onClick={onOpenUpload}
              className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white px-3 py-1.5 rounded-lg text-xs font-semibold shadow-lg shadow-cyan-500/25 flex items-center gap-1.5 transition-all transform hover:scale-[1.02]"
            >
              <Upload className="w-3.5 h-3.5" />
              Ingest Claim
            </button>

            {userProfile && (
              <div className="flex items-center space-x-2 pl-2 border-l border-slate-800">
                <div className="hidden lg:block text-right">
                  <div className="text-xs font-semibold text-slate-200">{userProfile.name}</div>
                  <div className="text-[10px] text-slate-400 font-mono truncate max-w-[120px]">{userProfile.email}</div>
                </div>

                <button
                  onClick={onLogout}
                  title="Sign Out of Workspace"
                  className="p-2 bg-slate-800 hover:bg-rose-950/50 hover:text-rose-400 border border-slate-700 hover:border-rose-500/50 rounded-lg text-slate-300 transition-all cursor-pointer flex items-center space-x-1 text-xs font-semibold"
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

