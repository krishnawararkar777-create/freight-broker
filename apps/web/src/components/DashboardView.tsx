import React, { useState } from 'react';
import type { Claim, ClaimStatus } from '../types/claim';
import { 
  DollarSign, ShieldAlert, ArrowUpRight, 
  FileCheck, Clock, AlertTriangle, CheckCircle2, XCircle, UserCheck, Search, ChevronRight
} from 'lucide-react';
import { filterClaims, calculateDashboardMetrics } from '../lib/dashboard-filters';
import { DeadlineUrgencyBadge } from './DeadlineUrgencyBadge';

interface DashboardViewProps {
  claims: Claim[];
  onSelectClaim: (claimId: string) => void;
  onOpenUpload: () => void;
  onOpenAnalytics?: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ claims, onSelectClaim, onOpenUpload, onOpenAnalytics }) => {
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [claimTypeFilter, setClaimTypeFilter] = useState<string>('ALL');

  const metrics = calculateDashboardMetrics(claims);
  const totalClaimed = metrics.totalActiveClaimed;
  const totalRecovered = metrics.totalRecovered;
  const algolyraFees = totalRecovered * 0.20;
  const activeClaimsCount = claims.filter(c => c.status !== 'CLOSED' && c.status !== 'RECOVERED').length;

  const filteredClaims = filterClaims(claims, {
    status: filterStatus,
    claimType: claimTypeFilter,
    searchQuery: searchQuery
  });

  const getStatusBadge = (status: ClaimStatus) => {
    switch (status) {
      case 'HUMAN_REVIEW':
      case 'READY_FOR_REVIEW':
        return <span className="bg-amber-500/10 text-amber-400 border border-amber-500/30 px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1"><Clock className="w-3 h-3"/> Ready for Review</span>;
      case 'SUBMITTED':
      case 'AWAITING_RESPONSE':
        return <span className="bg-blue-500/10 text-blue-400 border border-blue-500/30 px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1"><FileCheck className="w-3 h-3"/> Submitted to Carrier</span>;
      case 'RECOVERED':
      case 'PARTIALLY_RECOVERED':
        return <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1"><CheckCircle2 className="w-3 h-3"/> Recovered</span>;
      case 'NEEDS_INFORMATION':
        return <span className="bg-rose-500/10 text-rose-400 border border-rose-500/30 px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1"><AlertTriangle className="w-3 h-3"/> Action Required</span>;
      case 'REJECTED':
        return <span className="bg-slate-800 text-slate-400 border border-slate-700 px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1"><XCircle className="w-3 h-3"/> Rejected</span>;
      default:
        return <span className="bg-slate-800 text-slate-300 px-2.5 py-1 rounded-full text-xs font-semibold">{status}</span>;
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/50 rounded-2xl p-6 border border-slate-800 shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Cargo Claims Operating Layer</h1>
          <p className="text-slate-400 text-sm mt-1">
            Automating freight evidence processing & Carmack deadline tracking. All financial decisions stay in broker control.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="bg-slate-950/80 px-4 py-2 rounded-xl border border-slate-800 text-right">
            <div className="text-[11px] text-slate-400 font-mono">Algolyra Pricing Model</div>
            <div className="text-sm font-bold text-cyan-400">20% Contingency Rate ($0 on $0)</div>
          </div>
          {onOpenAnalytics && (
            <button
              onClick={onOpenAnalytics}
              className="bg-indigo-600/80 hover:bg-indigo-500 text-white px-3.5 py-2.5 rounded-xl font-semibold text-xs border border-indigo-500/40 shadow-lg shadow-indigo-500/10 transition-all flex items-center gap-2"
            >
              📊 Executive Charts
            </button>
          )}
          <button
            onClick={onOpenUpload}
            className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 px-4 py-2.5 rounded-xl font-bold text-sm shadow-lg shadow-cyan-500/20 transition-all flex items-center gap-2"
          >
            + New Claim Intake
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 hover:border-slate-700 transition-colors shadow-lg">
          <div className="flex justify-between items-start text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Claimed Value</span>
            <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg">
              <DollarSign className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-3xl font-extrabold text-white font-mono">
              ${totalClaimed.toLocaleString()}
            </span>
          </div>
          <div className="mt-2 text-xs text-slate-400 flex items-center gap-1">
            <span className="text-slate-300 font-medium">{activeClaimsCount} active open claims</span>
          </div>
        </div>

        <div className="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 hover:border-slate-700 transition-colors shadow-lg">
          <div className="flex justify-between items-start text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Recovered Dollars</span>
            <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
              <ArrowUpRight className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-3xl font-extrabold text-emerald-400 font-mono">
              ${totalRecovered.toLocaleString()}
            </span>
          </div>
          <div className="mt-2 text-xs text-slate-400">
            Broker retains <strong className="text-slate-200">${(totalRecovered - algolyraFees).toLocaleString()}</strong> net
          </div>
        </div>

        <div className="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 hover:border-slate-700 transition-colors shadow-lg">
          <div className="flex justify-between items-start text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Algolyra Fee Ledger</span>
            <div className="p-2 bg-cyan-500/10 text-cyan-400 rounded-lg">
              <FileCheck className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-3xl font-extrabold text-cyan-400 font-mono">
              ${algolyraFees.toLocaleString()}
            </span>
          </div>
          <div className="mt-2 text-xs text-slate-400">
            20% contracted rate on verified recovery
          </div>
        </div>

        <div className="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 hover:border-slate-700 transition-colors shadow-lg">
          <div className="flex justify-between items-start text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Human Control Guard</span>
            <div className="p-2 bg-amber-500/10 text-amber-400 rounded-lg">
              <ShieldAlert className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-xl font-bold text-white">
              $5,000 Threshold
            </span>
          </div>
          <div className="mt-2 text-xs text-amber-400 flex items-center gap-1 font-medium">
            <UserCheck className="w-3.5 h-3.5" /> High-value claims require Senior Approver
          </div>
        </div>
      </div>

      <div className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="p-5 border-b border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h2 className="text-lg font-bold text-white">Freight Cargo Claims Queue</h2>
            <p className="text-xs text-slate-400">Select any claim to enter the split-screen Human Review Workspace.</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search PRO#, Claim#, Carrier..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-slate-950 text-slate-200 text-xs pl-8 pr-3 py-1.5 rounded-xl border border-slate-800 focus:border-cyan-400 outline-none w-48 font-mono"
              />
            </div>

            <select
              value={claimTypeFilter}
              onChange={(e) => setClaimTypeFilter(e.target.value)}
              className="bg-slate-950 text-slate-300 text-xs px-2.5 py-1.5 rounded-xl border border-slate-800 focus:border-cyan-400 outline-none"
            >
              <option value="ALL">All Types</option>
              <option value="DAMAGE">Cargo Damage</option>
              <option value="SHORTAGE">Shortage</option>
              <option value="CONCEALED_DAMAGE">Concealed Damage</option>
              <option value="OVERCHARGE">Overcharge</option>
            </select>

            <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
              {[
                { id: 'ALL', label: 'All Claims' },
                { id: 'REVIEW', label: 'Needs Review' },
                { id: 'SUBMITTED', label: 'Submitted' },
                { id: 'RECOVERED', label: 'Recovered' },
                { id: 'BLOCKED', label: 'Action Required' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setFilterStatus(tab.id)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                    filterStatus === tab.id
                      ? 'bg-cyan-500 text-slate-950 shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/60 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800 font-semibold">
              <tr>
                <th className="px-6 py-4">Claim #</th>
                <th className="px-6 py-4">Shipment & Carrier</th>
                <th className="px-6 py-4">Type</th>
                <th className="px-6 py-4">Claimed Amount</th>
                <th className="px-6 py-4">AI Readiness</th>
                <th className="px-6 py-4">Carmack Deadline</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {filteredClaims.map((claim) => (
                <tr 
                  key={claim.id}
                  onClick={() => onSelectClaim(claim.id)}
                  className="hover:bg-slate-800/50 cursor-pointer transition-colors group"
                >
                  <td className="px-6 py-4 font-mono font-bold text-cyan-400 group-hover:underline">
                    {claim.claimNumber}
                    {claim.humanThresholdTriggered && (
                      <span className="block text-[10px] text-amber-400 font-sans font-medium mt-0.5">
                        High Value ($5k+)
                      </span>
                    )}
                  </td>

                  <td className="px-6 py-4">
                    <div className="font-semibold text-slate-100">{claim.shipment?.carrierName}</div>
                    <div className="text-xs text-slate-400 font-mono">PRO: {claim.shipment?.proNumber}</div>
                  </td>

                  <td className="px-6 py-4 font-semibold text-slate-200">
                    {claim.claimType}
                  </td>

                  <td className="px-6 py-4 font-mono font-extrabold text-white">
                    ${claim.claimedAmount.toLocaleString()}
                    {claim.recoveredAmount > 0 && (
                      <span className="block text-[11px] text-emerald-400">
                        Rec: ${claim.recoveredAmount.toLocaleString()}
                      </span>
                    )}
                  </td>

                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-2">
                      <div className="w-12 bg-slate-800 rounded-full h-2 overflow-hidden border border-slate-700">
                        <div 
                          className={`h-full rounded-full ${
                            (claim.readinessScore || 0) >= 90
                              ? 'bg-emerald-400'
                              : (claim.readinessScore || 0) >= 70
                              ? 'bg-amber-400'
                              : 'bg-rose-500'
                          }`}
                          style={{ width: `${claim.readinessScore || 0}%` }}
                        />
                      </div>
                      <span className="text-xs font-bold font-mono text-slate-200">
                        {claim.readinessScore}%
                      </span>
                    </div>
                  </td>

                  <td className="px-6 py-4">
                    <DeadlineUrgencyBadge
                      deadlineDateIso={claim.deadlineAt || '2026-09-15T00:00:00Z'}
                      isConcealed={(claim.claimType as string) === 'CONCEALED_DAMAGE'}
                    />
                  </td>

                  <td className="px-6 py-4">
                    {getStatusBadge(claim.status)}
                  </td>

                  <td className="px-6 py-4 text-right">
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectClaim(claim.id);
                      }}
                      className="bg-slate-800 hover:bg-cyan-500 hover:text-slate-950 text-slate-200 font-semibold px-3 py-1.5 rounded-lg text-xs transition-all inline-flex items-center gap-1"
                    >
                      Review <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
