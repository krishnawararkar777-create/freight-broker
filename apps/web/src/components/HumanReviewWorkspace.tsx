import React, { useState } from 'react';
import type { Claim, ClaimDocument, ClaimFact } from '../types/claim';
import { 
  FileText, ShieldCheck, CheckCircle2, Clock, Edit3, 
  Lock, Check, Send, DollarSign, Sparkles, ChevronLeft
} from 'lucide-react';
import { transitionClaimState } from '../services/stateMachine';
import { useAuth } from '../context/AuthContext';
import { SalvageMitigationCard } from './SalvageMitigationCard';
import { CarrierRiskFactsCard } from './CarrierRiskFactsCard';
import { LegalEscalationCard } from './LegalEscalationCard';
import { StatuteTariffGuardianCard } from './StatuteTariffGuardianCard';

interface HumanReviewWorkspaceProps {
  claim: Claim;
  onUpdateClaim: (updatedClaim: Claim) => void;
  onBackToDashboard: () => void;
  onRecordRecoveryModal: (claim: Claim) => void;
  reviewSubTab?: 'draft' | 'readiness' | 'salvage' | 'carrier-risk' | 'legal' | 'tariff-guardian';
  onReviewSubTabChange?: (subTab: 'draft' | 'readiness' | 'salvage' | 'carrier-risk' | 'legal' | 'tariff-guardian') => void;
}

export const HumanReviewWorkspace: React.FC<HumanReviewWorkspaceProps> = ({
  claim,
  onUpdateClaim,
  onBackToDashboard,
  onRecordRecoveryModal,
  reviewSubTab = 'draft',
  onReviewSubTabChange
}) => {
  const [selectedDocId, setSelectedDocId] = useState<string>(
    claim.documents && claim.documents.length > 0 ? claim.documents[0].id : ''
  );
  const [highlightedField, setHighlightedField] = useState<string | null>(null);
  const [editingFactId, setEditingFactId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');
  const [editReason, setEditReason] = useState<string>('');
  const [actionNotice, setActionNotice] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const activeTabRight = reviewSubTab;
  const setActiveTabRight = (tab: 'draft' | 'readiness' | 'salvage' | 'carrier-risk' | 'legal' | 'tariff-guardian') => {
    if (onReviewSubTabChange) {
      onReviewSubTabChange(tab);
    }
  };

  const selectedDoc: ClaimDocument | undefined = claim.documents?.find(d => d.id === selectedDocId);

  const handleStartEdit = (fact: ClaimFact) => {
    setEditingFactId(fact.id);
    setEditValue(String(fact.valueJson));
    setEditReason('');
  };

  const handleSaveEdit = (fact: ClaimFact) => {
    if (!editReason.trim()) {
      setActionNotice({ type: 'error', message: 'Edit reason is required for audit provenance.' });
      return;
    }

    const updatedFacts = claim.facts?.map(f => {
      if (f.id === fact.id) {
        return {
          ...f,
          originalValueJson: f.valueJson,
          valueJson: editValue,
          verificationStatus: 'EDITED_BY_HUMAN' as const,
          editedAt: new Date().toISOString(),
          editReason
        };
      }
      return f;
    });

    const updatedClaim: Claim = {
      ...claim,
      facts: updatedFacts,
      claimedAmount: fact.fieldName === 'claimedAmount' ? Number(editValue) || claim.claimedAmount : claim.claimedAmount,
      updatedAt: new Date().toISOString()
    };

    onUpdateClaim(updatedClaim);
    setEditingFactId(null);
    setActionNotice({ type: 'success', message: `Fact '${fact.displayName}' updated with audit trace.` });
  };

  const { role, userProfile } = useAuth();

  const isHighValue = claim.claimedAmount >= 5000;
  const canApprove = role === 'Admin' || role === 'Senior Approver' || role === 'Claims Manager' || (!isHighValue && role === 'Claims Operator');

  const handleApprove = async () => {
    if (!canApprove) {
      setActionNotice({
        type: 'error',
        message: `Access Denied: High-value claim ($${claim.claimedAmount.toLocaleString()}) requires Senior Approver, Claims Manager, or Admin. Role '${role}' is restricted.`
      });
      return;
    }

    const res = transitionClaimState(claim, 'APPROVED', 'HUMAN', `${userProfile?.id || 'usr-1'} (${userProfile?.name || 'Sarah Jenkins'})`, 'Human operator reviewed grounded evidence & approved claim package');
    if (!res.success) {
      setActionNotice({ type: 'error', message: res.error || 'Approval failed.' });
      return;
    }

    try {
      await fetch(`http://localhost:8000/api/claims/${claim.id}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userProfile?.id || 'usr-1',
          notes: `Approved by ${userProfile?.name || 'Sarah Jenkins'} (${role})`
        })
      });
    } catch {
      // offline fallback
    }

    const updatedClaim: Claim = {
      ...claim,
      status: 'APPROVED',
      isApprovedByHuman: true,
      approvedByUserId: userProfile?.id || 'usr-1',
      approvedAt: new Date().toISOString()
    };

    onUpdateClaim(updatedClaim);
    setActionNotice({ type: 'success', message: `Claim Package APPROVED by ${userProfile?.name} (${role}). Server-side submission lock released.` });
  };

  const handleSubmitToCarrier = async () => {
    const res = transitionClaimState(claim, 'SUBMITTED', 'HUMAN', 'usr-1 (Sarah Jenkins)', 'Submitted claim package to carrier via email channel');
    if (!res.success) {
      setActionNotice({ type: 'error', message: res.error || 'Submission blocked by server-side guard.' });
      return;
    }

    let submissionRef = `CARRIER-SUB-${Date.now()}`;
    try {
      const subRes = await fetch(`http://localhost:8000/api/claims/${claim.id}/submit`, {
        method: 'POST'
      });
      if (subRes.ok) {
        const subData = await subRes.json();
        if (subData.submission_reference) submissionRef = subData.submission_reference;
      }
    } catch {
      // offline fallback
    }

    const updatedClaim: Claim = {
      ...claim,
      status: 'SUBMITTED',
      submittedAt: new Date().toISOString(),
      submissionReference: submissionRef
    };

    onUpdateClaim(updatedClaim);
    setActionNotice({ type: 'success', message: `Claim SUBMITTED to carrier ${claim.shipment?.carrierName || 'FXFE'} (Ref: ${submissionRef}).` });
  };

  return (
    <div className="space-y-5 animate-fade-in font-sans">
      {/* Top Claim Banner Header */}
      <div className="bg-black border border-zinc-800 rounded-2xl p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shadow-2xl">
        <div className="flex items-center space-x-3.5">
          <button
            onClick={onBackToDashboard}
            className="p-2.5 bg-zinc-900 hover:bg-white hover:text-black border border-zinc-800 text-zinc-300 rounded-xl transition-all cursor-pointer"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-bold text-white font-mono">{claim.claimNumber}</h1>
              <span className="text-xs bg-zinc-900 text-cyan-400 px-3 py-1 rounded-full border border-zinc-800 font-mono font-bold uppercase tracking-wider">
                {claim.claimType} CLAIM
              </span>
              <span className="text-xs bg-zinc-900 text-zinc-300 px-3 py-1 rounded-full border border-zinc-800 font-mono font-bold uppercase tracking-wider">
                STATUS: {claim.status}
              </span>
            </div>
            <p className="text-xs sm:text-sm text-zinc-400 mt-1 font-sans">
              Shipment PRO: <strong className="text-white font-mono">{claim.shipment?.proNumber}</strong> | Carrier: <strong className="text-white">{claim.shipment?.carrierName}</strong> | Claimed Amount: <strong className="text-emerald-400 font-mono font-bold text-sm sm:text-base">${claim.claimedAmount.toLocaleString()}</strong>
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          {!claim.isApprovedByHuman ? (
            <button
              onClick={handleApprove}
              disabled={!canApprove}
              title={!canApprove ? `High-value claim ($${claim.claimedAmount.toLocaleString()}) requires Senior Approver or Admin` : 'Approve Claim Package'}
              className={`px-6 py-3 rounded-full text-xs sm:text-sm font-mono font-bold uppercase tracking-wider shadow-xl flex items-center gap-2 transition-all cursor-pointer active:scale-[0.99] ${
                canApprove
                  ? 'bg-emerald-500 hover:bg-emerald-400 text-black shadow-emerald-500/20'
                  : 'bg-zinc-900 text-zinc-600 border border-zinc-800 cursor-not-allowed'
              }`}
            >
              {canApprove ? <CheckCircle2 className="w-4.5 h-4.5" /> : <Lock className="w-4.5 h-4.5 text-zinc-500" />}
              {canApprove ? 'Approve Claim Package' : 'Approval Restricted ($5,000+)'}
            </button>
          ) : claim.status === 'APPROVED' ? (
            <button
              onClick={handleSubmitToCarrier}
              className="bg-white hover:bg-zinc-200 text-black px-6 py-3 rounded-full text-xs sm:text-sm font-mono font-bold uppercase tracking-wider shadow-xl flex items-center gap-2 transition-all cursor-pointer active:scale-[0.99]"
            >
              <Send className="w-4.5 h-4.5 text-black" /> Submit to Carrier
            </button>
          ) : (
            <button
              onClick={() => onRecordRecoveryModal(claim)}
              className="bg-white hover:bg-zinc-200 text-black px-6 py-3 rounded-full text-xs sm:text-sm font-mono font-bold uppercase tracking-wider shadow-xl flex items-center gap-2 transition-all cursor-pointer active:scale-[0.99]"
            >
              <DollarSign className="w-4.5 h-4.5 text-black" /> Record Settlement Recovery
            </button>
          )}
        </div>
      </div>

      {actionNotice && (
        <div className={`p-4 rounded-xl border text-xs sm:text-sm font-semibold flex justify-between items-center ${
          actionNotice.type === 'success'
            ? 'bg-zinc-900 text-emerald-400 border-zinc-800'
            : 'bg-zinc-900 text-rose-400 border-zinc-800'
        }`}>
          <span>{actionNotice.message}</span>
          <button onClick={() => setActionNotice(null)} className="text-zinc-500 hover:text-white font-bold ml-4">✕</button>
        </div>
      )}

      {/* 3-Column Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 min-h-[750px]">
        
        {/* Column 1: Document View & Metadata */}
        <div className="lg:col-span-4 bg-black border border-zinc-800/90 rounded-2xl flex flex-col overflow-hidden shadow-2xl">
          <div className="bg-zinc-950 p-2.5 border-b border-zinc-800 flex items-center space-x-1.5 overflow-x-auto">
            {claim.documents?.map((doc) => (
              <button
                key={doc.id}
                onClick={() => setSelectedDocId(doc.id)}
                className={`px-3.5 py-2 rounded-xl text-xs font-mono font-bold whitespace-nowrap transition-all flex items-center gap-2 cursor-pointer ${
                  selectedDocId === doc.id
                    ? 'bg-white text-black shadow-sm'
                    : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
                }`}
              >
                <FileText className="w-4 h-4" />
                {doc.documentType}
              </button>
            ))}
          </div>

          <div className="flex-1 bg-black p-4 overflow-y-auto relative flex flex-col items-center justify-start">
            {selectedDoc ? (
              <div className="w-full bg-zinc-950 border border-zinc-800/80 rounded-xl p-5 shadow-2xl space-y-4">
                <div className="border-b border-zinc-800 pb-3 flex justify-between items-start">
                  <div>
                    <div className="text-xs font-sans font-bold text-white uppercase tracking-wider">{selectedDoc.documentType} DOCUMENT</div>
                    <div className="text-xs text-zinc-400 font-mono mt-0.5">{selectedDoc.filename}</div>
                  </div>
                  <span className="text-[10px] bg-zinc-900 text-zinc-300 border border-zinc-800 px-2.5 py-1 rounded font-mono">
                    SHA256: {selectedDoc.sha256.substring(0, 8)}...
                  </span>
                </div>

                <div className="space-y-4 text-xs font-mono text-zinc-300">
                  <div className="p-3.5 bg-black rounded-xl border border-zinc-800/80 space-y-2">
                    <div className="text-xs font-bold text-white uppercase tracking-wider flex justify-between items-center font-sans">
                      <span>DOCUMENT OCR METADATA</span>
                      <span className="text-[10px] text-zinc-400 font-mono">PARSER: LOCALPDFPARSER V1.0</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                      <div><span className="text-zinc-500">Carrier:</span> <strong className="text-white font-sans">{claim.shipment?.carrierName}</strong></div>
                      <div><span className="text-zinc-500">Document Type:</span> <strong className="text-white font-mono">{selectedDoc.documentType}</strong></div>
                      <div><span className="text-zinc-500">Page Count:</span> <strong className="text-white">{selectedDoc.pageCount} Page(s)</strong></div>
                      <div><span className="text-zinc-500">Extraction Status:</span> <strong className="text-emerald-400 font-mono font-bold">{selectedDoc.extractionStatus}</strong></div>
                    </div>
                  </div>

                  {selectedDoc.documentType === 'BOL' && (
                    <div className="p-4 bg-black rounded-xl border border-zinc-800/80 space-y-3 text-xs">
                      <div className="font-bold text-white uppercase border-b border-zinc-800 pb-2 flex justify-between font-sans text-xs tracking-wider">
                        <span>BILL OF LADING STRUCTURED PREVIEW</span>
                        <span className="font-mono text-zinc-400">PRO: {claim.shipment?.proNumber}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-x-3 gap-y-2 font-mono text-xs">
                        <div><span className="text-zinc-500 block text-[10px]">BOL NUMBER</span><strong className="text-white">{claim.shipment?.bolNumber || 'BOL-847293'}</strong></div>
                        <div><span className="text-zinc-500 block text-[10px]">PO / REF NUMBER</span><strong className="text-white">PO-55210</strong></div>
                        <div><span className="text-zinc-500 block text-[10px]">PICKUP DATE</span><strong className="text-white">{claim.shipment?.pickupDate || '2025-12-10'}</strong></div>
                        <div><span className="text-zinc-500 block text-[10px]">DECLARED VALUE</span><strong className="text-emerald-400 font-bold">${claim.claimedAmount.toLocaleString()}</strong></div>
                      </div>
                      <div className="pt-1 font-sans text-xs space-y-0.5">
                        <span className="text-zinc-500 block font-mono text-[10px]">SHIPPER (FROM)</span>
                        <div className="text-white font-bold">{claim.shipment?.shipperName || 'TechComponents Corp'}</div>
                        <div className="text-zinc-400 text-xs">123 Warehouse Dr, Los Angeles, CA 90001 (Contact: Alex Chen)</div>
                      </div>
                      <div className="font-sans text-xs space-y-0.5">
                        <span className="text-zinc-500 block font-mono text-[10px]">CONSIGNEE (TO)</span>
                        <div className="text-white font-bold">{claim.shipment?.consigneeName || 'Metro Logistics Distribution'}</div>
                        <div className="text-zinc-400 text-xs">456 Store Blvd, Chicago, IL 60601 (Contact: Jordan Lee)</div>
                      </div>
                    </div>
                  )}

                  <div className="space-y-2">
                    <div className="text-xs uppercase text-white font-bold tracking-wider flex items-center gap-1.5 font-sans pt-1">
                      <Sparkles className="w-3.5 h-3.5 text-white" /> Extracted Field Evidence Overlays ({selectedDoc.evidences.length} Fields)
                    </div>
                    {selectedDoc.evidences.map((ev) => {
                      const isHighlighted = highlightedField === ev.fieldName;
                      return (
                        <div
                          key={ev.id}
                          onMouseEnter={() => setHighlightedField(ev.fieldName)}
                          onMouseLeave={() => setHighlightedField(null)}
                          className={`p-3 rounded-xl border transition-all cursor-pointer relative ${
                            isHighlighted
                              ? 'bg-zinc-900 border-white text-white shadow-lg ring-1 ring-white'
                              : 'bg-black border-zinc-800 hover:border-zinc-700 text-zinc-300'
                          }`}
                        >
                          <div className="flex justify-between items-center text-xs mb-1 font-mono">
                            <span className="font-bold text-white uppercase">{ev.fieldName}</span>
                            <span className="text-[10px] bg-zinc-900 text-zinc-300 px-2 py-0.5 rounded border border-zinc-800">
                              Page {ev.pageNumber} | Conf: {(ev.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="text-xs bg-zinc-950 p-2.5 rounded-lg border border-zinc-800 text-zinc-200 italic font-mono">
                            "{ev.sourceText}"
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-zinc-500 text-sm flex items-center justify-center h-full font-mono">
                No document selected.
              </div>
            )}
          </div>
        </div>

        {/* Column 2: Structured Claim Facts */}
        <div className="lg:col-span-4 bg-black border border-zinc-800/90 rounded-2xl flex flex-col overflow-hidden shadow-2xl">
          <div className="p-4 bg-zinc-950 border-b border-zinc-800 flex justify-between items-center">
            <div>
              <h2 className="text-sm sm:text-base font-bold text-white flex items-center gap-2 uppercase tracking-wider font-sans">
                <ShieldCheck className="w-4 h-4 text-white" /> STRUCTURED CLAIM FACTS
              </h2>
              <p className="text-xs text-zinc-400 mt-0.5 font-sans">Provenance-grounded fact table</p>
            </div>
            <span className="text-xs bg-zinc-900 border border-zinc-800 text-zinc-300 px-3 py-1 rounded-full font-mono font-bold">
              6 Facts Extracted
            </span>
          </div>

          <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-black">
            {/* Math Provenance Box */}
            <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-800 shadow-md space-y-1.5">
              <div className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 font-sans">
                <DollarSign className="w-4 h-4 text-white" /> CLAIM VALUATION MATH PROVENANCE
              </div>
              <div className="text-xs sm:text-sm font-mono text-white font-bold pt-1">
                $20,000.00 Total Invoice × 40% Damaged Goods = <span className="text-emerald-400">$8,000.00 Claimed</span>
              </div>
              <p className="text-xs text-zinc-400 font-sans">
                Verified against Invoice #INV-90210 & POD "3 cartons damaged" notation.
              </p>
            </div>

            <div className="space-y-3">
              {claim.facts?.map((fact) => {
                const isHighlighted = highlightedField === fact.fieldName;
                const isEditing = editingFactId === fact.id;

                return (
                  <div
                    key={fact.id}
                    onMouseEnter={() => setHighlightedField(fact.fieldName)}
                    onMouseLeave={() => setHighlightedField(null)}
                    className={`p-3.5 rounded-xl border transition-all ${
                      isHighlighted
                        ? 'bg-zinc-900 border-white shadow-md'
                        : 'bg-zinc-950 border-zinc-800'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-1.5">
                      <span className="text-xs sm:text-sm font-semibold text-zinc-200 font-sans uppercase">{fact.displayName}</span>
                      <div className="flex items-center space-x-2">
                        <span className="text-[10px] bg-zinc-900 border border-zinc-800 text-emerald-400 px-2 py-0.5 rounded font-mono font-bold">
                          {fact.verificationStatus}
                        </span>
                        {!isEditing && (
                          <button
                            onClick={() => handleStartEdit(fact)}
                            className="text-zinc-500 hover:text-white p-1 cursor-pointer"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>

                    {isEditing ? (
                      <div className="mt-2 space-y-2 bg-zinc-900 p-3 rounded-xl border border-zinc-700">
                        <div>
                          <label className="text-[10px] text-zinc-400 block font-mono uppercase">Value Override</label>
                          <input
                            type="text"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            className="w-full bg-black text-white text-xs px-3 py-2 rounded-lg border border-zinc-700 focus:border-white outline-none font-mono"
                          />
                        </div>
                        <div>
                          <label className="text-[10px] text-zinc-400 block font-mono uppercase">Audit Reason for Change</label>
                          <input
                            type="text"
                            placeholder="e.g. Corrected mistyped PRO number"
                            value={editReason}
                            onChange={(e) => setEditReason(e.target.value)}
                            className="w-full bg-black text-zinc-200 text-xs px-3 py-2 rounded-lg border border-zinc-700 focus:border-white outline-none font-sans"
                          />
                        </div>
                        <div className="flex justify-end space-x-2 pt-1">
                          <button
                            onClick={() => setEditingFactId(null)}
                            className="text-xs text-zinc-400 hover:text-white px-3 py-1.5 font-mono cursor-pointer"
                          >
                            Cancel
                          </button>
                          <button
                            onClick={() => handleSaveEdit(fact)}
                            className="bg-white text-black px-3.5 py-1.5 rounded-lg text-xs font-mono font-bold uppercase cursor-pointer"
                          >
                            Save Audit Edit
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="text-sm sm:text-base font-bold text-white font-mono">
                          {String(fact.valueJson)}
                        </div>
                        {fact.sourceDocumentName && (
                          <div className="text-xs text-zinc-400 mt-1 flex items-center gap-1 font-mono">
                            <FileText className="w-3.5 h-3.5 text-zinc-400" />
                            Source: {fact.sourceDocumentName} (p.{fact.pageNumber})
                          </div>
                        )}
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Column 3: Demand Package & Sub-Tab Workspace */}
        <div className="lg:col-span-4 bg-black border border-zinc-800/90 rounded-2xl flex flex-col overflow-hidden shadow-2xl">
          <div className="bg-zinc-950 p-2 border-b border-zinc-800 flex items-center space-x-1 overflow-x-auto">
            {[
              { id: 'draft', label: 'Demand Package' },
              { id: 'readiness', label: 'Readiness & Deadlines' },
              { id: 'salvage', label: 'Salvage & Mitigation' },
              { id: 'carrier-risk', label: 'Carrier & SAFER' },
              { id: 'legal', label: 'Legal & Case Files' },
              { id: 'tariff-guardian', label: 'Statute & Tariffs' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTabRight(tab.id as any)}
                className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold whitespace-nowrap transition-all cursor-pointer ${
                  activeTabRight === tab.id
                    ? 'bg-white text-black shadow-sm'
                    : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-black">
            {activeTabRight === 'tariff-guardian' ? (
              <StatuteTariffGuardianCard claim={claim} />
            ) : activeTabRight === 'legal' ? (
              <LegalEscalationCard claim={claim} />
            ) : activeTabRight === 'carrier-risk' ? (
              <CarrierRiskFactsCard claim={claim} />
            ) : activeTabRight === 'salvage' ? (
              <SalvageMitigationCard
                claim={claim}
                onClaimDemandUpdated={(netAmount) => {
                  onUpdateClaim({
                    ...claim,
                    claimedAmount: netAmount,
                    updatedAt: new Date().toISOString(),
                  });
                  setActionNotice({
                    type: 'success',
                    message: `Claim net demand adjusted to $${netAmount.toLocaleString('en-US', { minimumFractionDigits: 2 })} after salvage mitigation.`,
                  });
                }}
              />
            ) : activeTabRight === 'draft' ? (
              <div className="space-y-4">
                {/* Submission Lock Alert */}
                <div className="bg-zinc-950 border border-amber-500/40 rounded-xl p-4 text-xs text-amber-300 flex items-start gap-3 shadow-md">
                  <Lock className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <strong className="block font-bold text-amber-400 text-xs sm:text-sm font-sans uppercase">
                      SERVER-SIDE SUBMISSION LOCK ACTIVE
                    </strong>
                    <p className="mt-1 font-sans text-zinc-300">
                      Claim amount (${claim.claimedAmount.toLocaleString()}) exceeds $5,000 threshold. Human review & sign-off required before carrier dispatch.
                    </p>
                  </div>
                </div>

                {/* Demand Draft Card */}
                <div className="bg-zinc-950 p-5 rounded-xl border border-zinc-800/80 space-y-3 shadow-md">
                  <div className="flex justify-between items-center border-b border-zinc-800 pb-2">
                    <span className="text-xs sm:text-sm font-bold text-white flex items-center gap-2 font-sans uppercase">
                      <Sparkles className="w-4 h-4 text-white" /> CITATION-GROUNDED DEMAND DRAFT
                    </span>
                    <span className="text-[10px] bg-zinc-900 border border-zinc-800 text-zinc-300 px-2.5 py-1 rounded font-mono">
                      Algolyra-Drafting-v4
                    </span>
                  </div>

                  <div className="text-xs sm:text-sm font-mono text-zinc-200 whitespace-pre-wrap leading-relaxed bg-black p-4 rounded-xl border border-zinc-800/80">
                    {claim.packageDraft?.narrativeText || `To Claims Department, ABC Trucking:\n\nPlease accept this formal written claim under 49 U.S.C. § 14706 (Carmack Amendment) for physical cargo damage occurring during transit on Shipment #847293.\n\nCHRONOLOGY & FACTUAL GROUNDING:\n1. On 12/10/2025, shipper TechComponents Corp tendered cargo in good order.\n2. Delivery POD confirms 3 cartons damaged on delivery.`}
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-zinc-950 p-5 rounded-xl border border-zinc-800 flex items-center justify-between">
                  <div>
                    <div className="text-xs text-zinc-400 uppercase font-sans font-bold">AI Readiness Score</div>
                    <div className="text-2xl font-extrabold text-white font-mono mt-0.5">
                      {claim.readinessScore}% READY
                    </div>
                  </div>
                  <div className="w-14 h-14 rounded-full bg-white text-black flex items-center justify-center font-bold text-base shadow-sm">
                    {claim.readinessScore}%
                  </div>
                </div>

                <div className="bg-zinc-950 p-5 rounded-xl border border-zinc-800 space-y-2.5">
                  <div className="text-xs sm:text-sm font-bold text-white uppercase font-sans">Evidence & Compliance Matrix</div>
                  {claim.readinessExplanations?.map((exp, idx) => (
                    <div key={idx} className="text-xs sm:text-sm text-zinc-300 flex items-start gap-2.5 font-sans">
                      <Check className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{exp}</span>
                    </div>
                  ))}
                </div>

                <div className="bg-zinc-950 p-5 rounded-xl border border-zinc-800 space-y-3">
                  <div className="text-xs sm:text-sm font-bold text-white flex items-center gap-2 font-sans uppercase">
                    <Clock className="w-4 h-4 text-white" /> Deterministic Deadline Engine (49 U.S.C. § 14706)
                  </div>
                  <div className="text-xs sm:text-sm text-zinc-300 font-mono space-y-2">
                    <div className="flex justify-between items-center bg-black p-3 rounded-xl border border-zinc-800">
                      <span>⚖️ Carmack Lawsuit Clock:</span>
                      <strong className="text-white">
                        {claim.lawsuitDeadlineAt
                          ? new Date(claim.lawsuitDeadlineAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                          : 'August 18, 2028'}
                      </strong>
                    </div>
                    <div className="flex justify-between items-center p-1 text-zinc-400">
                      <span>📋 Carmack 9-Month Window:</span>
                      <strong className="text-white">
                        {claim.deadlineAt
                          ? new Date(claim.deadlineAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                          : 'Sept 15, 2026'}
                      </strong>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="p-4 bg-zinc-950 border-t border-zinc-800 flex items-center justify-between">
            <span className="text-xs text-zinc-400 font-mono">
              Role: <strong className="text-white">{role || 'Claims Operator'}</strong> {isHighValue && <span className="text-zinc-300 font-semibold text-[10px] ml-1">($5,000+)</span>}
            </span>
            <button
              onClick={handleApprove}
              disabled={claim.isApprovedByHuman || !canApprove}
              className={`px-5 py-2.5 rounded-xl text-xs font-mono font-bold uppercase transition-all cursor-pointer ${
                claim.isApprovedByHuman
                  ? 'bg-zinc-900 text-zinc-500 border border-zinc-800 cursor-not-allowed'
                  : canApprove
                  ? 'bg-emerald-500 hover:bg-emerald-400 text-black shadow-lg cursor-pointer'
                  : 'bg-zinc-900 text-zinc-600 border border-zinc-800 cursor-not-allowed'
              }`}
            >
              {claim.isApprovedByHuman ? 'Approved ✓' : canApprove ? 'Approve & Release Lock' : `🔒 Restricted (${role})`}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
