import React from 'react';
import { 
  LayoutGrid, Activity, FileText, Receipt, Scale, 
  Upload, Sparkles, Clock, RefreshCw, Truck, Shield, 
  Server, Lock, LogOut 
} from 'lucide-react';
import type { UserProfile, UserOrganization, RBACRole } from '../types/auth';

interface SidebarProps {
  activeTab: 'dashboard' | 'analytics' | 'review' | 'ledger' | 'rules' | 'audit';
  setActiveTab: (tab: 'dashboard' | 'analytics' | 'review' | 'ledger' | 'rules' | 'audit') => void;
  reviewSubTab: 'draft' | 'readiness' | 'salvage' | 'carrier-risk' | 'legal' | 'tariff-guardian';
  setReviewSubTab: (subTab: 'draft' | 'readiness' | 'salvage' | 'carrier-risk' | 'legal' | 'tariff-guardian') => void;
  org: UserOrganization | null;
  role: RBACRole | null;
  userProfile: UserProfile | null;
  onLogout: () => void;
  onOpenUpload: () => void;
  selectedClaimNumber?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  reviewSubTab,
  setReviewSubTab,
  org,
  userProfile,
  onLogout,
  onOpenUpload,
  selectedClaimNumber = '847293'
}) => {
  const userInitial = userProfile?.name ? userProfile.name[0].toUpperCase() : 'K';
  const displayUserName = userProfile?.name || 'Krishnawararkar15';
  const displayOrgName = org?.name || 'APEX FREIGHT BROKERS';

  const handleReviewSubTabClick = (subTab: 'draft' | 'readiness' | 'salvage' | 'carrier-risk' | 'legal' | 'tariff-guardian') => {
    setActiveTab('review');
    setReviewSubTab(subTab);
  };

  return (
    <aside className="w-64 bg-black border-r border-zinc-800/80 flex flex-col h-screen sticky top-0 shrink-0 z-40 select-none font-sans">
      {/* Brand Header */}
      <div className="p-4 flex items-center space-x-2.5">
        <div className="w-6 h-6 bg-white transform rotate-45 flex items-center justify-center shadow-sm shrink-0">
          <div className="w-2 h-2 bg-black" />
        </div>
        <div className="flex items-baseline space-x-1">
          <span className="font-mono font-bold tracking-widest text-sm text-white uppercase">
            ALGOLYRA
          </span>
          <span className="font-mono text-zinc-500 text-xs">
            OS
          </span>
        </div>
      </div>

      {/* Server Status Sub-bar */}
      <div className="border-y border-zinc-800/80 py-2 px-4 flex items-center justify-between text-[10px] font-mono text-zinc-400 uppercase tracking-wider bg-zinc-950/40">
        <span className="flex items-center gap-1.5">
          <Server className="w-3 h-3 text-zinc-400" />
          WAIT
        </span>
        <span className="flex items-center gap-1.5">
          <Lock className="w-3 h-3 text-zinc-400" />
          SECURE
        </span>
      </div>

      {/* Scrollable Navigation Body */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-5">
        {/* OVERVIEW SECTION */}
        <div>
          <div className="px-3 pb-2 text-[10px] font-mono font-semibold tracking-widest text-zinc-500 uppercase">
            OVERVIEW
          </div>
          <nav className="space-y-1">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-mono font-semibold transition-all cursor-pointer ${
                activeTab === 'dashboard'
                  ? 'bg-zinc-900 text-white border border-zinc-700/80 shadow-sm'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-900/50'
              }`}
            >
              <LayoutGrid className="w-4 h-4" />
              <span>DASHBOARD</span>
            </button>

            <button
              onClick={() => setActiveTab('analytics')}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-mono font-semibold transition-all cursor-pointer ${
                activeTab === 'analytics'
                  ? 'bg-zinc-900 text-white border border-zinc-700/80 shadow-sm'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-900/50'
              }`}
            >
              <Activity className="w-4 h-4" />
              <span>ANALYTICS</span>
            </button>

            {/* REVIEW WITH NESTED SUB-ITEMS */}
            <div>
              <button
                onClick={() => setActiveTab('review')}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-mono font-semibold transition-all cursor-pointer ${
                  activeTab === 'review'
                    ? 'bg-zinc-900 text-white border border-zinc-700/80 shadow-sm'
                    : 'text-zinc-400 hover:text-white hover:bg-zinc-900/50'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <FileText className="w-4 h-4" />
                  <span>REVIEW</span>
                </div>
                <span className="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-700/80 text-zinc-300">
                  {selectedClaimNumber.replace(/^CLM-/, '')}
                </span>
              </button>

              {/* Nested Sub-navigation when REVIEW tab is active */}
              {activeTab === 'review' && (
                <div className="ml-5 pl-3 border-l border-zinc-800 space-y-1 mt-1.5 mb-1 animate-fade-in">
                  <button
                    onClick={() => handleReviewSubTabClick('draft')}
                    className={`w-full flex items-center space-x-2 px-2.5 py-1.5 rounded-lg text-[11px] font-mono font-semibold transition-all cursor-pointer ${
                      reviewSubTab === 'draft'
                        ? 'bg-zinc-800/90 text-white border border-zinc-700'
                        : 'text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span className="truncate">DEMAND PACKAGE</span>
                  </button>

                  <button
                    onClick={() => handleReviewSubTabClick('readiness')}
                    className={`w-full flex items-center space-x-2 px-2.5 py-1.5 rounded-lg text-[11px] font-mono font-medium transition-all cursor-pointer ${
                      reviewSubTab === 'readiness'
                        ? 'bg-zinc-800/90 text-white border border-zinc-700 font-semibold'
                        : 'text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    <Clock className="w-3.5 h-3.5" />
                    <span className="truncate">READINESS & DEADLI...</span>
                  </button>

                  <button
                    onClick={() => handleReviewSubTabClick('salvage')}
                    className={`w-full flex items-center space-x-2 px-2.5 py-1.5 rounded-lg text-[11px] font-mono font-medium transition-all cursor-pointer ${
                      reviewSubTab === 'salvage'
                        ? 'bg-zinc-800/90 text-white border border-zinc-700 font-semibold'
                        : 'text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span className="truncate">SALVAGE & MITIGATI...</span>
                  </button>

                  <button
                    onClick={() => handleReviewSubTabClick('carrier-risk')}
                    className={`w-full flex items-center space-x-2 px-2.5 py-1.5 rounded-lg text-[11px] font-mono font-medium transition-all cursor-pointer ${
                      reviewSubTab === 'carrier-risk'
                        ? 'bg-zinc-800/90 text-white border border-zinc-700 font-semibold'
                        : 'text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    <Truck className="w-3.5 h-3.5" />
                    <span className="truncate">CARRIER & SAFER</span>
                  </button>

                  <button
                    onClick={() => handleReviewSubTabClick('legal')}
                    className={`w-full flex items-center space-x-2 px-2.5 py-1.5 rounded-lg text-[11px] font-mono font-medium transition-all cursor-pointer ${
                      reviewSubTab === 'legal'
                        ? 'bg-zinc-800/90 text-white border border-zinc-700 font-semibold'
                        : 'text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    <Scale className="w-3.5 h-3.5" />
                    <span className="truncate">LEGAL & CASE FILES</span>
                  </button>

                  <button
                    onClick={() => handleReviewSubTabClick('tariff-guardian')}
                    className={`w-full flex items-center space-x-2 px-2.5 py-1.5 rounded-lg text-[11px] font-mono font-medium transition-all cursor-pointer ${
                      reviewSubTab === 'tariff-guardian'
                        ? 'bg-zinc-800/90 text-white border border-zinc-700 font-semibold'
                        : 'text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    <Shield className="w-3.5 h-3.5" />
                    <span className="truncate">STATUTE & TARIFFS</span>
                  </button>
                </div>
              )}
            </div>
          </nav>
        </div>

        {/* SETTINGS & LOGS SECTION */}
        <div>
          <div className="px-3 pb-2 text-[10px] font-mono font-semibold tracking-widest text-zinc-500 uppercase">
            SETTINGS & LOGS
          </div>
          <nav className="space-y-1">
            <button
              onClick={() => setActiveTab('ledger')}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-mono font-semibold transition-all cursor-pointer ${
                activeTab === 'ledger'
                  ? 'bg-zinc-900 text-white border border-zinc-700/80 shadow-sm'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-900/50'
              }`}
            >
              <Receipt className="w-4 h-4" />
              <span>LEDGER</span>
            </button>

            <button
              onClick={() => setActiveTab('rules')}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-mono font-semibold transition-all cursor-pointer ${
                activeTab === 'rules'
                  ? 'bg-zinc-900 text-white border border-zinc-700/80 shadow-sm'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-900/50'
              }`}
            >
              <Scale className="w-4 h-4" />
              <span>RULES</span>
            </button>

            <button
              onClick={() => setActiveTab('audit')}
              className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-mono font-semibold transition-all cursor-pointer ${
                activeTab === 'audit'
                  ? 'bg-zinc-900 text-white border border-zinc-700/80 shadow-sm'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-900/50'
              }`}
            >
              <Activity className="w-4 h-4" />
              <span>AUDIT LOG</span>
            </button>
          </nav>
        </div>
      </div>

      {/* Sidebar Footer CTA & User Bar */}
      <div className="p-3 border-t border-zinc-800/80 space-y-3 bg-black">
        {/* INGEST CLAIM White CTA Button */}
        <button
          onClick={onOpenUpload}
          className="w-full bg-white hover:bg-zinc-200 text-black font-mono font-bold text-xs uppercase tracking-wider py-2.5 px-3 rounded-xl flex items-center justify-center space-x-2 shadow-sm transition-all cursor-pointer active:scale-[0.99]"
        >
          <Upload className="w-3.5 h-3.5" />
          <span>INGEST CLAIM</span>
        </button>

        {/* User Profile */}
        <div className="pt-1 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2.5 min-w-0">
            <div className="w-7 h-7 rounded-full bg-zinc-900 border border-zinc-700 flex items-center justify-center font-bold text-xs text-white shrink-0">
              {userInitial}
            </div>
            <div className="min-w-0">
              <div className="font-bold text-white text-xs truncate">
                {displayUserName}
              </div>
              <div className="text-[9px] font-mono text-zinc-500 uppercase tracking-wider truncate">
                {displayOrgName}
              </div>
            </div>
          </div>

          <button
            onClick={onLogout}
            title="Sign Out of Workspace"
            className="p-1.5 hover:bg-zinc-800 rounded-lg text-zinc-500 hover:text-white transition-colors cursor-pointer shrink-0 ml-1"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
