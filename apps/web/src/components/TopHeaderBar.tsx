import React from 'react';
import type { UserOrganization, RBACRole } from '../types/auth';

interface TopHeaderBarProps {
  org: UserOrganization | null;
  role: RBACRole | null;
  activeTab: 'dashboard' | 'analytics' | 'review' | 'ledger' | 'rules' | 'audit';
}

export const TopHeaderBar: React.FC<TopHeaderBarProps> = ({ org, role, activeTab }) => {
  const orgName = org?.name || 'Apex Freight Brokers';
  const userRole = role ? role.toUpperCase() : 'CLAIMS MANAGER';

  const tabLabels: Record<string, string> = {
    dashboard: 'Dashboard',
    analytics: 'Analytics',
    review: 'Review Workspace',
    ledger: 'Recovery Ledger',
    rules: 'Carrier Rules',
    audit: 'Audit Log'
  };

  return (
    <header className="h-14 border-b border-zinc-800/80 bg-black/90 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30 font-mono text-xs select-none">
      {/* Left Breadcrumb */}
      <div className="flex items-center space-x-2.5">
        <div className="w-3.5 h-3.5 bg-white transform rotate-45 flex items-center justify-center shrink-0">
          <div className="w-1 h-1 bg-black" />
        </div>
        <div className="flex items-center space-x-2 font-semibold text-zinc-200">
          <span>{orgName}</span>
          <span className="text-zinc-600">/</span>
          <span className="text-white font-bold">{tabLabels[activeTab] || 'Dashboard'}</span>
        </div>
      </div>

      {/* Right Monospace Metadata */}
      <div className="flex items-center space-x-3 text-[11px] text-zinc-400 font-mono tracking-wider uppercase">
        <div>
          MODEL: <span className="text-white font-bold">CONTINGENCY FEE</span>
        </div>
        <span className="text-zinc-700">|</span>
        <div>
          ROLE: <span className="text-white font-bold">{userRole}</span>
        </div>
      </div>
    </header>
  );
};
