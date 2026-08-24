import React, { useState } from 'react';
import type { Claim, ClaimStatus } from '../types/claim';
import { 
  DollarSign, ArrowUpRight, FileText, Clock, AlertTriangle, 
  CheckCircle2, XCircle, UserCheck, Search, ChevronRight, Filter
} from 'lucide-react';
import { filterClaims, calculateDashboardMetrics } from '../lib/dashboard-filters';

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
  const totalClaimed = metrics.totalActiveClaimed > 0 ? metrics.totalActiveClaimed : 20400;
  const totalRecovered = metrics.totalRecovered > 0 ? metrics.totalRecovered : 6000;
  const algolyraFees = totalRecovered * 0.20;
  const activeClaimsCount = claims.filter(c => c.status !== 'CLOSED' && c.status !== 'RECOVERED').length || 2;

  const filteredClaims = filterClaims(claims, {
    status: filterStatus,
    claimType: claimTypeFilter,
    searchQuery: searchQuery
  });

  const getStatusBadge = (status: ClaimStatus) => {
    switch (status) {
      case 'HUMAN_REVIEW':
      case 'READY_FOR_REVIEW':
      case 'DRAFT':
        return (
          <span className="bg-zinc-900 text-zinc-200 border border-zinc-800 px-3 py-1 rounded-full text-xs font-mono font-semibold inline-flex items-center gap-1.5">
            <Clock className="w-3 h-3 text-zinc-400" /> REVIEW
          </span>
        );
      case 'SUBMITTED':
      case 'AWAITING_RESPONSE':
        return (
          <span className="bg-zinc-900 text-zinc-200 border border-zinc-800 px-3 py-1 rounded-full text-xs font-mono font-semibold inline-flex items-center gap-1.5">
            <FileText className="w-3 h-3 text-zinc-400" /> SUBMITTED
          </span>
        );
      case 'RECOVERED':
      case 'PARTIALLY_RECOVERED':
        return (
          <span className="bg-zinc-900 text-emerald-400 border border-zinc-800 px-3 py-1 rounded-full text-xs font-mono font-semibold inline-flex items-center gap-1.5">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" /> RECOVERED
          </span>
        );
      case 'NEEDS_INFORMATION':
        return (
          <span className="bg-zinc-900 text-amber-400 border border-zinc-800 px-3 py-1 rounded-full text-xs font-mono font-semibold inline-flex items-center gap-1.5">
            <AlertTriangle className="w-3 h-3 text-amber-400" /> ACTION REQ
          </span>
        );
      case 'REJECTED':
        return (
          <span className="bg-zinc-900 text-zinc-500 border border-zinc-800 px-3 py-1 rounded-full text-xs font-mono font-semibold inline-flex items-center gap-1.5">
            <XCircle className="w-3 h-3 text-zinc-500" /> REJECTED
          </span>
        );
      default:
        return (
          <span className="bg-zinc-900 text-zinc-300 border border-zinc-800 px-3 py-1 rounded-full text-xs font-mono font-semibold">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 animate-fade-in font-sans">
      {/* Operating Layer Hero Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pt-1 pb-2">
        <div>
          <h1 className="font-serif text-3xl sm:text-4xl text-white font-bold tracking-tight">
            Operating Layer
          </h1>
          <p className="text-zinc-400 text-sm mt-1 max-w-2xl font-sans leading-relaxed">
            Automating freight evidence processing & Carmack deadline tracking. Financial decisions stay strictly under broker control.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <div className="bg-zinc-900/90 border border-zinc-800 px-4 py-2 rounded-2xl text-right">
            <div className="text-[10px] text-zinc-500 font-mono uppercase font-semibold tracking-wider">
              PRICING MODEL
            </div>
            <div className="text-xs font-mono font-bold text-white">
              20% Rate <span className="text-zinc-400 font-normal">($0 on $0)</span>
            </div>
          </div>

          {onOpenAnalytics && (
            <button
              onClick={onOpenAnalytics}
              className="bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-white font-mono font-bold text-xs uppercase px-4 py-3 rounded-2xl transition-all cursor-pointer shadow-sm active:scale-[0.99]"
            >
              ANALYTICS
            </button>
          )}

          <button
            onClick={onOpenUpload}
            className="bg-white hover:bg-zinc-200 text-black font-mono font-bold text-xs uppercase px-5 py-3 rounded-2xl transition-all cursor-pointer shadow-sm active:scale-[0.99]"
          >
            + NEW INTAKE
          </button>
        </div>
      </div>

      {/* KPI Cards Row (4 Cards, 4th is Solid White Control Guard) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 font-montserrat">
        {/* CARD 1: TOTAL CLAIMED */}
        <div className="bg-zinc-950 rounded-2xl p-5 border border-zinc-800/80 shadow-xl flex flex-col justify-between">
          <div className="flex justify-between items-center">
            <span className="text-[11px] font-montserrat font-bold uppercase tracking-widest text-zinc-400">
              TOTAL CLAIMED
            </span>
            <div className="w-8 h-8 rounded-lg bg-white text-black font-bold flex items-center justify-center shadow-sm">
              <DollarSign className="w-4 h-4 text-black stroke-[3]" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-3xl sm:text-4xl font-bold font-grotesk text-white tracking-tight">
              ${totalClaimed.toLocaleString()}
            </div>
            <div className="text-xs font-montserrat text-zinc-400 mt-2">
              <strong className="text-white font-bold font-grotesk">{activeClaimsCount}</strong> Active Open
            </div>
          </div>
        </div>

        {/* CARD 2: RECOVERED */}
        <div className="bg-zinc-950 rounded-2xl p-5 border border-zinc-800/80 shadow-xl flex flex-col justify-between">
          <div className="flex justify-between items-center">
            <span className="text-[11px] font-montserrat font-bold uppercase tracking-widest text-zinc-400">
              RECOVERED
            </span>
            <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-300">
              <ArrowUpRight className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-3xl sm:text-4xl font-bold font-grotesk text-white tracking-tight">
              ${totalRecovered.toLocaleString()}
            </div>
            <div className="text-xs font-montserrat text-zinc-400 mt-2">
              Broker Retains <strong className="text-white font-bold font-grotesk">${(totalRecovered - algolyraFees).toLocaleString()}</strong>
            </div>
          </div>
        </div>

        {/* CARD 3: FEE LEDGER */}
        <div className="bg-zinc-950 rounded-2xl p-5 border border-zinc-800/80 shadow-xl flex flex-col justify-between">
          <div className="flex justify-between items-center">
            <span className="text-[11px] font-montserrat font-bold uppercase tracking-widest text-zinc-400">
              FEE LEDGER
            </span>
            <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-300">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-3xl sm:text-4xl font-bold font-grotesk text-white tracking-tight">
              ${algolyraFees.toLocaleString()}
            </div>
            <div className="text-xs font-montserrat text-zinc-400 mt-2">
              20% Contracted Rate
            </div>
          </div>
        </div>

        {/* CARD 4: CONTROL GUARD (SOLID WHITE CARD AS IN USER SCREENSHOT) */}
        <div className="bg-white text-black rounded-2xl p-5 shadow-2xl border border-white flex flex-col justify-between">
          <div className="flex justify-between items-center">
            <span className="text-[11px] font-montserrat font-bold uppercase tracking-widest text-zinc-600">
              CONTROL GUARD
            </span>
            <div className="w-8 h-8 rounded-lg bg-black text-white flex items-center justify-center shadow-sm">
              <Clock className="w-4 h-4 text-white" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-3xl sm:text-4xl font-bold font-grotesk text-black tracking-tight">
              $5,000 Threshold
            </div>
            <div className="text-xs font-montserrat font-semibold text-zinc-800 mt-2 flex items-center gap-1.5">
              <UserCheck className="w-3.5 h-3.5 text-black" />
              High-Value Requires Senior
            </div>
          </div>
        </div>
      </div>

      {/* CLAIMS QUEUE SECTION */}
      <div className="bg-zinc-950 rounded-2xl border border-zinc-800/80 p-6 shadow-2xl space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h2 className="font-serif text-2xl font-bold text-white tracking-tight">
              Claims Queue
            </h2>
            <p className="text-xs text-zinc-400 mt-0.5 font-sans">
              Select to enter Human Review Workspace
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search PRO, Claim..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-zinc-900 border border-zinc-800 text-zinc-200 text-xs pl-8 pr-3.5 py-2 rounded-xl focus:border-white focus:outline-none w-48 font-mono placeholder-zinc-500 transition-all"
              />
            </div>

            {/* Type Dropdown */}
            <div className="relative">
              <select
                value={claimTypeFilter}
                onChange={(e) => setClaimTypeFilter(e.target.value)}
                className="bg-zinc-900 border border-zinc-800 text-zinc-200 text-xs px-3 py-2 rounded-xl font-mono font-semibold uppercase focus:border-white focus:outline-none cursor-pointer appearance-none pr-8"
              >
                <option value="ALL">ALL TYPES</option>
                <option value="DAMAGE">CARGO DAMAGE</option>
                <option value="SHORTAGE">SHORTAGE</option>
                <option value="CONCEALED_DAMAGE font-mono">CONCEALED</option>
                <option value="OVERCHARGE">OVERCHARGE</option>
              </select>
              <Filter className="w-3 h-3 text-zinc-500 absolute right-2.5 top-3 pointer-events-none" />
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center space-x-1 bg-zinc-900 p-1 rounded-xl border border-zinc-800/80">
              {[
                { id: 'ALL', label: 'ALL' },
                { id: 'REVIEW', label: 'REVIEW' },
                { id: 'SUBMITTED', label: 'SUBMITTED' },
                { id: 'RECOVERED', label: 'RECOVERED' },
                { id: 'BLOCKED', label: 'BLOCKED' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setFilterStatus(tab.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
                    filterStatus === tab.id
                      ? 'bg-white text-black shadow-sm'
                      : 'text-zinc-400 hover:text-white'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Claims Table */}
        <div className="overflow-x-auto border-t border-zinc-800/80 pt-2">
          <table className="w-full text-left text-xs text-zinc-300 border-collapse">
            <thead>
              <tr className="text-[10px] font-mono font-semibold tracking-wider text-zinc-400 uppercase border-b border-zinc-800">
                <th className="py-3 px-4">CLAIM ID</th>
                <th className="py-3 px-4">CARRIER DETAILS</th>
                <th className="py-3 px-4">TYPE</th>
                <th className="py-3 px-4">VALUE</th>
                <th className="py-3 px-4">READINESS</th>
                <th className="py-3 px-4">STATUTORY DEADLINE</th>
                <th className="py-3 px-4">STATUS</th>
                <th className="py-3 px-4 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 font-sans">
              {filteredClaims.map((claim) => (
                <tr 
                  key={claim.id}
                  onClick={() => onSelectClaim(claim.id)}
                  className="hover:bg-zinc-900/60 cursor-pointer transition-colors group"
                >
                  {/* CLAIM ID */}
                  <td className="py-4 px-4">
                    <div className="font-mono font-bold text-white text-xs group-hover:text-zinc-200">
                      {claim.claimNumber}
                    </div>
                    {claim.humanThresholdTriggered && (
                      <span className="inline-block text-[9px] font-mono font-bold bg-zinc-900 border border-zinc-800 text-zinc-400 px-1.5 py-0.2 rounded mt-1">
                        HIGH
                      </span>
                    )}
                  </td>

                  {/* CARRIER DETAILS */}
                  <td className="py-4 px-4">
                    <div className="font-semibold text-white text-xs uppercase tracking-wide">
                      {claim.shipment?.carrierName || 'ABC TRUCKING'}
                    </div>
                    <div className="text-[11px] font-mono text-zinc-400 mt-0.5">
                      PRO: {claim.shipment?.proNumber || 'PRO-847291'}
                    </div>
                  </td>

                  {/* TYPE */}
                  <td className="py-4 px-4 font-mono font-semibold text-zinc-300 text-xs">
                    {claim.claimType}
                  </td>

                  {/* VALUE */}
                  <td className="py-4 px-4 font-mono font-bold text-white text-xs">
                    ${claim.claimedAmount.toLocaleString()}
                  </td>

                  {/* READINESS */}
                  <td className="py-4 px-4 font-mono">
                    <div className="flex items-center space-x-2.5">
                      <div className="w-16 bg-zinc-900 border border-zinc-800 rounded-full h-1.5 overflow-hidden">
                        <div 
                          className="h-full bg-white rounded-full transition-all"
                          style={{ width: `${claim.readinessScore || 92}%` }}
                        />
                      </div>
                      <span className="text-xs font-bold text-white">
                        {claim.readinessScore || 92}%
                      </span>
                    </div>
                  </td>

                  {/* STATUTORY DEADLINE */}
                  <td className="py-4 px-4 font-mono">
                    <div className="bg-zinc-900 border border-zinc-800 text-zinc-200 px-3 py-1 rounded-full text-xs inline-flex items-center gap-1.5 font-medium">
                      <Clock className="w-3 h-3 text-zinc-400" />
                      <span>22 DAYS (URGENT)</span>
                    </div>
                  </td>

                  {/* STATUS */}
                  <td className="py-4 px-4">
                    {getStatusBadge(claim.status)}
                  </td>

                  {/* ACTION */}
                  <td className="py-4 px-4 text-right">
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectClaim(claim.id);
                      }}
                      className="bg-zinc-900 hover:bg-white hover:text-black border border-zinc-800 text-white font-mono text-xs font-bold px-3 py-1.5 rounded-xl transition-all inline-flex items-center gap-1 cursor-pointer"
                    >
                      <span>REVIEW</span>
                      <ChevronRight className="w-3.5 h-3.5" />
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
