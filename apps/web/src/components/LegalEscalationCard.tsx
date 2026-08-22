import React, { useState, useEffect } from 'react';
import { 
  Scale, CheckCircle2, ChevronRight, FileText, 
  Clock, UserCheck, AlertCircle, Copy
} from 'lucide-react';
import type { Claim } from '../types/claim';
import { useAuth } from '../context/AuthContext';

interface LegalRecord {
  id: string;
  claim_id: string;
  organization_id: string;
  is_escalated: boolean;
  escalation_tier_rate: number;
  escalated_by_user_id?: string;
  escalated_at?: string;
  escalation_reason?: string;
  current_milestone: string;
  milestone_updated_at?: string;
  assigned_counsel_name?: string;
  counsel_firm?: string;
  case_file_notes?: string;
}

interface DossierData {
  dossier_title: string;
  claim_id: string;
  pro_number: string;
  carrier_name: string;
  carrier_mc?: string;
  gross_claim_amount: number;
  lawsuit_deadline_at?: string;
  fee_tier: string;
  contingency_rate: number;
  current_milestone: string;
  assigned_counsel?: string;
  counsel_firm?: string;
  table_of_contents: Array<{
    document_id: string;
    document_type: string;
    filename: string;
    sha256: string;
    page_count: number;
    uploaded_at?: string;
  }>;
  chronology: Array<{
    event: string;
    timestamp: string;
    source: string;
  }>;
  evidence_chain_of_custody_verified: boolean;
  generated_at: string;
}

interface LegalEscalationCardProps {
  claim: Claim;
}

const MILESTONES = [
  { id: 'PRE_LITIGATION', label: 'Pre-Litigation' },
  { id: 'DEMAND_LETTER_SENT', label: 'Demand Sent' },
  { id: 'REFERRED_TO_COUNSEL', label: 'Referred to Counsel' },
  { id: 'LAWSUIT_FILED', label: 'Lawsuit Filed' },
  { id: 'DISCOVERY', label: 'Discovery' },
  { id: 'SETTLED', label: 'Settled' },
  { id: 'JUDGMENT_ENTERED', label: 'Judgment' },
];

export const LegalEscalationCard: React.FC<LegalEscalationCardProps> = ({ claim }) => {
  const { user, role, userProfile } = useAuth();
  const [legalRecord, setLegalRecord] = useState<LegalRecord | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isEscalating, setIsEscalating] = useState<boolean>(false);
  const [showEscalateModal, setShowEscalateModal] = useState<boolean>(false);
  const [showDossierModal, setShowDossierModal] = useState<boolean>(false);
  const [dossier, setDossier] = useState<DossierData | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  // Form State
  const [tierRate, setTierRate] = useState<number>(0.30);
  const [reason, setReason] = useState<string>('');
  const [counselName, setCounselName] = useState<string>('');
  const [counselFirm, setCounselFirm] = useState<string>('');

  const currentRole = role || userProfile?.role || '';
  const isSeniorOrFinance = ['Senior Approver', 'Finance', 'Admin', 'Claims Manager'].includes(currentRole);

  const fetchLegalData = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/claims/${claim.id}/legal-escalation`);
      if (res.ok) {
        const data = await res.json();
        setLegalRecord(data);
      }
    } catch {
      // Offline fallback
      setLegalRecord({
        id: 'esc-fallback',
        claim_id: claim.id,
        organization_id: 'org-1',
        is_escalated: false,
        escalation_tier_rate: 0.30,
        current_milestone: 'PRE_LITIGATION',
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLegalData();
  }, [claim.id]);

  const handleEscalateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsEscalating(true);
    const activeUserId = user?.id || userProfile?.id || 'usr-apex-mgr';
    try {
      const res = await fetch(`http://localhost:8000/api/claims/${claim.id}/legal-escalation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: activeUserId,
          escalation_tier_rate: tierRate,
          escalation_reason: reason,
          assigned_counsel_name: counselName || undefined,
          counsel_firm: counselFirm || undefined,
        }),
      });
      if (res.ok) {
        const updated = await res.json();
        setLegalRecord(updated);
      } else {
        setLegalRecord({
          id: `esc-${Date.now()}`,
          claim_id: claim.id,
          organization_id: 'org-1',
          is_escalated: true,
          escalation_tier_rate: tierRate,
          assigned_counsel_name: counselName,
          counsel_firm: counselFirm,
          escalation_reason: reason,
          current_milestone: 'REFERRED_TO_COUNSEL',
        });
      }
    } catch {
      setLegalRecord({
        id: `esc-${Date.now()}`,
        claim_id: claim.id,
        organization_id: 'org-1',
        is_escalated: true,
        escalation_tier_rate: tierRate,
        assigned_counsel_name: counselName,
        counsel_firm: counselFirm,
        escalation_reason: reason,
        current_milestone: 'REFERRED_TO_COUNSEL',
      });
    } finally {
      setShowEscalateModal(false);
      setIsEscalating(false);
    }
  };

  const handleMilestoneChange = async (newMilestone: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/claims/${claim.id}/milestones`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ milestone: newMilestone }),
      });
      if (res.ok) {
        const updated = await res.json();
        setLegalRecord(updated);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleFetchDossier = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/claims/${claim.id}/case-file-dossier`);
      if (res.ok) {
        const data = await res.json();
        setDossier(data);
        setShowDossierModal(true);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleCopyDossier = () => {
    if (!dossier) return;
    navigator.clipboard.writeText(JSON.stringify(dossier, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const activeRate = legalRecord?.is_escalated ? legalRecord.escalation_tier_rate : 0.20;
  const grossAmount = claim.claimedAmount || 10000;
  const feeAmount = grossAmount * activeRate;
  const netClientAmount = grossAmount - feeAmount;

  if (isLoading && !legalRecord) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 text-center text-slate-400 text-xs animate-pulse">
        Loading Tiered Fee Ledger & Legal Escalation Status...
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl space-y-5 text-slate-100">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-lg border ${
            legalRecord?.is_escalated 
              ? 'bg-purple-950/80 text-purple-400 border-purple-800/50' 
              : 'bg-emerald-950/80 text-emerald-400 border-emerald-800/50'
          }`}>
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-white">Tiered Recovery Fee Ledger & Case File</h3>
              <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold border ${
                legalRecord?.is_escalated
                  ? 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                  : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
              }`}>
                {legalRecord?.is_escalated ? `LEGAL TIER (${(activeRate * 100).toFixed(0)}%)` : 'STANDARD TIER (20%)'}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Role-gated legal escalation fee ledger and attorney case-file evidence assembly
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {!legalRecord?.is_escalated && (
            <button
              type="button"
              onClick={() => setShowEscalateModal(true)}
              disabled={!isSeniorOrFinance}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border flex items-center gap-1.5 transition-all ${
                isSeniorOrFinance
                  ? 'bg-purple-600 hover:bg-purple-500 text-white border-purple-500 shadow-lg shadow-purple-900/30'
                  : 'bg-slate-800 text-slate-500 border-slate-700 cursor-not-allowed opacity-60'
              }`}
              title={!isSeniorOrFinance ? 'Requires Senior Approver or Finance role' : undefined}
            >
              <UserCheck className="w-3.5 h-3.5" />
              Escalate to Legal Tier
            </button>
          )}

          <button
            type="button"
            onClick={handleFetchDossier}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 flex items-center gap-1.5 transition-all"
          >
            <FileText className="w-3.5 h-3.5 text-cyan-400" />
            Assemble Evidence Dossier
          </button>
        </div>
      </div>

      {/* Role Permission Notice if not Senior/Finance */}
      {!isSeniorOrFinance && !legalRecord?.is_escalated && (
        <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl text-xs text-slate-400 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-amber-400" />
          <span>Contingency escalation to 30%–35% legal tier requires authorization from a <strong>Senior Approver</strong> or <strong>Finance</strong> role.</span>
        </div>
      )}

      {/* Real-time Tier Math Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="bg-slate-950/80 border border-slate-800 p-3.5 rounded-xl space-y-1">
          <div className="text-[11px] text-slate-400 uppercase font-semibold">Gross Claim Amount</div>
          <div className="text-lg font-bold text-white font-mono">
            ${grossAmount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[10px] text-slate-500">100% principal demand</div>
        </div>

        <div className="bg-slate-950/80 border border-slate-800 p-3.5 rounded-xl space-y-1">
          <div className="text-[11px] text-slate-400 uppercase font-semibold flex justify-between">
            <span>Contingency Recovery Fee</span>
            <span className="text-purple-400 font-mono font-bold">{(activeRate * 100).toFixed(0)}%</span>
          </div>
          <div className="text-lg font-bold text-purple-300 font-mono">
            ${feeAmount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[10px] text-slate-500">
            {legalRecord?.is_escalated ? 'Litigation recovery tier' : 'Standard pre-litigation rate'}
          </div>
        </div>

        <div className="bg-slate-950/80 border border-slate-800 p-3.5 rounded-xl space-y-1">
          <div className="text-[11px] text-slate-400 uppercase font-semibold flex justify-between">
            <span>Net Recovery to Client</span>
            <span className="text-emerald-400 font-mono font-bold">{((1 - activeRate) * 100).toFixed(0)}%</span>
          </div>
          <div className="text-lg font-bold text-emerald-400 font-mono">
            ${netClientAmount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[10px] text-slate-500">Net client disbursement</div>
        </div>
      </div>

      {/* Litigation Milestones Stepper */}
      <div className="bg-slate-950/80 border border-slate-800 p-4 rounded-xl space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-cyan-400" />
            Litigation Milestone Progress
          </span>
          {legalRecord?.assigned_counsel_name && (
            <span className="text-xs text-slate-400">
              Assigned Counsel: <strong className="text-white">{legalRecord.assigned_counsel_name}</strong> {legalRecord.counsel_firm ? `(${legalRecord.counsel_firm})` : ''}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1 overflow-x-auto pb-1">
          {MILESTONES.map((m, idx) => {
            const isCurrent = legalRecord?.current_milestone === m.id;
            const currentIndex = MILESTONES.findIndex(x => x.id === (legalRecord?.current_milestone || 'PRE_LITIGATION'));
            const isPast = idx <= currentIndex;

            return (
              <React.Fragment key={m.id}>
                <button
                  type="button"
                  onClick={() => handleMilestoneChange(m.id)}
                  className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap flex items-center gap-1.5 ${
                    isCurrent
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-900/40'
                      : isPast
                      ? 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                      : 'bg-slate-950 text-slate-600 border border-slate-900 hover:text-slate-400'
                  }`}
                >
                  {isPast ? <CheckCircle2 className="w-3 h-3 text-cyan-400" /> : <div className="w-2 h-2 rounded-full bg-slate-700" />}
                  {m.label}
                </button>
                {idx < MILESTONES.length - 1 && (
                  <ChevronRight className="w-3.5 h-3.5 text-slate-700 shrink-0" />
                )}
              </React.Fragment>
            );
          })}
        </div>

        {legalRecord?.case_file_notes && (
          <div className="text-[11px] text-slate-400 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 font-mono">
            {legalRecord.case_file_notes}
          </div>
        )}
      </div>

      {/* Escalate to Legal Tier Modal */}
      {showEscalateModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Scale className="w-5 h-5 text-purple-400" />
                Authorize Legal Tier Escalation
              </h3>
              <button
                type="button"
                onClick={() => setShowEscalateModal(false)}
                className="text-slate-400 hover:text-white text-xs"
              >
                Cancel
              </button>
            </div>

            <form onSubmit={handleEscalateSubmit} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-400 font-medium mb-1">Escalation Contingency Fee Tier</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setTierRate(0.30)}
                    className={`p-2.5 rounded-lg border text-center font-bold ${
                      tierRate === 0.30
                        ? 'bg-purple-950 border-purple-500 text-purple-300'
                        : 'bg-slate-950 border-slate-800 text-slate-400'
                    }`}
                  >
                    30% Legal Tier
                  </button>
                  <button
                    type="button"
                    onClick={() => setTierRate(0.35)}
                    className={`p-2.5 rounded-lg border text-center font-bold ${
                      tierRate === 0.35
                        ? 'bg-purple-950 border-purple-500 text-purple-300'
                        : 'bg-slate-950 border-slate-800 text-slate-400'
                    }`}
                  >
                    35% Legal Tier
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Assigned Counsel Name</label>
                <input
                  type="text"
                  value={counselName}
                  onChange={(e) => setCounselName(e.target.value)}
                  placeholder="e.g. Robert Vance, Esq."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:border-purple-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Law Firm / Practice Group</label>
                <input
                  type="text"
                  value={counselFirm}
                  onChange={(e) => setCounselFirm(e.target.value)}
                  placeholder="e.g. Vance & Sterling LLP"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:border-purple-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Escalation Authorization Reason</label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  rows={2}
                  placeholder="e.g. Carrier bad-faith denial; transferring case file for federal court filing."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:border-purple-500 focus:outline-none"
                  required
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowEscalateModal(false)}
                  className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isEscalating}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-lg transition-all"
                >
                  {isEscalating ? 'Authorizing...' : 'Authorize Escalation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Assembled Case-File Dossier Modal */}
      {showDossierModal && dossier && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full p-5 space-y-4 shadow-2xl max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <FileText className="w-5 h-5 text-cyan-400" />
                  Attorney Case File Evidence Dossier
                </h3>
                <p className="text-[11px] text-slate-400">
                  Compiled Table of Contents, SHA-256 Hashes & Carmack Deadlines
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleCopyDossier}
                  className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs flex items-center gap-1"
                >
                  <Copy className="w-3.5 h-3.5" />
                  {copied ? 'Copied JSON!' : 'Copy JSON'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowDossierModal(false)}
                  className="text-slate-400 hover:text-white text-xs px-2"
                >
                  Close
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-4 text-xs pr-1 font-mono">
              {/* Header Info */}
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1">
                <div className="text-slate-400">PRO NUMBER: <strong className="text-white">{dossier.pro_number}</strong></div>
                <div className="text-slate-400">CARRIER: <strong className="text-white">{dossier.carrier_name}</strong></div>
                <div className="text-slate-400">CLAIM DEMAND: <strong className="text-emerald-400">${dossier.gross_claim_amount.toLocaleString()}</strong></div>
                <div className="text-slate-400">CARMACK 2-YEAR LAWSUIT DEADLINE: <strong className="text-amber-400">{dossier.lawsuit_deadline_at || 'Pending calculation'}</strong></div>
              </div>

              {/* Table of Contents */}
              <div className="space-y-1.5">
                <div className="text-slate-300 font-bold uppercase text-[11px]">Table of Contents & Document Hashes ({dossier.table_of_contents.length})</div>
                <div className="space-y-1">
                  {dossier.table_of_contents.map((d, i) => (
                    <div key={i} className="bg-slate-950 p-2 rounded border border-slate-800 flex items-center justify-between text-[11px]">
                      <div>
                        <span className="text-cyan-400 font-bold">[{d.document_type}]</span> {d.filename} ({d.page_count} pg)
                      </div>
                      <div className="text-slate-500 text-[10px]">
                        SHA-256: {d.sha256.substring(0, 16)}...
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Factual Chronology */}
              <div className="space-y-1.5">
                <div className="text-slate-300 font-bold uppercase text-[11px]">Factual Chronology Timeline ({dossier.chronology.length})</div>
                <div className="space-y-1">
                  {dossier.chronology.map((c, i) => (
                    <div key={i} className="bg-slate-950 p-2 rounded border border-slate-800 flex items-center justify-between text-[11px]">
                      <span className="text-slate-200">{c.event}</span>
                      <span className="text-slate-400">{new Date(c.timestamp).toLocaleDateString()} ({c.source})</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
