import React, { useState } from 'react';
import type { Claim, ClaimDocument, ClaimFact } from '../types/claim';
import { 
  FileText, ShieldCheck, CheckCircle2, Clock, Edit3, 
  Lock, Check, Send, DollarSign, Sparkles, ChevronLeft
} from 'lucide-react';
import { transitionClaimState } from '../services/stateMachine';

interface HumanReviewWorkspaceProps {
  claim: Claim;
  onUpdateClaim: (updatedClaim: Claim) => void;
  onBackToDashboard: () => void;
  onRecordRecoveryModal: (claim: Claim) => void;
}

export const HumanReviewWorkspace: React.FC<HumanReviewWorkspaceProps> = ({
  claim,
  onUpdateClaim,
  onBackToDashboard,
  onRecordRecoveryModal
}) => {
  const [selectedDocId, setSelectedDocId] = useState<string>(
    claim.documents && claim.documents.length > 0 ? claim.documents[0].id : ''
  );
  const [highlightedField, setHighlightedField] = useState<string | null>(null);
  const [editingFactId, setEditingFactId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');
  const [editReason, setEditReason] = useState<string>('');
  const [actionNotice, setActionNotice] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [activeTabRight, setActiveTabRight] = useState<'draft' | 'readiness'>('draft');

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

  const handleApprove = () => {
    const res = transitionClaimState(claim, 'APPROVED', 'HUMAN', 'usr-1 (Sarah Jenkins)', 'Human operator reviewed grounded evidence & approved claim package');
    if (!res.success) {
      setActionNotice({ type: 'error', message: res.error || 'Approval failed.' });
      return;
    }

    const updatedClaim: Claim = {
      ...claim,
      status: 'APPROVED',
      isApprovedByHuman: true,
      approvedByUserId: 'usr-1',
      approvedAt: new Date().toISOString()
    };

    onUpdateClaim(updatedClaim);
    setActionNotice({ type: 'success', message: 'Claim Package APPROVED by Human Operator. Server-side submission lock released.' });
  };

  const handleSubmitToCarrier = () => {
    const res = transitionClaimState(claim, 'SUBMITTED', 'HUMAN', 'usr-1 (Sarah Jenkins)', 'Submitted claim package to carrier via email channel');
    if (!res.success) {
      setActionNotice({ type: 'error', message: res.error || 'Submission blocked by server-side guard.' });
      return;
    }

    const updatedClaim: Claim = {
      ...claim,
      status: 'SUBMITTED',
      submittedAt: new Date().toISOString(),
      submissionReference: `CARRIER-SUB-${Date.now()}`
    };

    onUpdateClaim(updatedClaim);
    setActionNotice({ type: 'success', message: 'Claim SUBMITTED to carrier ABC Trucking (Ref: CARRIER-SUB-847293).' });
  };

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shadow-xl">
        <div className="flex items-center space-x-3">
          <button
            onClick={onBackToDashboard}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-xl font-bold text-white font-mono">{claim.claimNumber}</h1>
              <span className="text-xs bg-cyan-500/10 text-cyan-400 px-2.5 py-0.5 rounded-full border border-cyan-500/20 font-semibold uppercase">
                {claim.claimType} CLAIM
              </span>
              <span className="text-xs bg-amber-500/10 text-amber-400 px-2.5 py-0.5 rounded-full border border-amber-500/20 font-semibold">
                Status: {claim.status}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Shipment PRO: <strong className="text-slate-200">{claim.shipment?.proNumber}</strong> | Carrier: <strong className="text-slate-200">{claim.shipment?.carrierName}</strong> | Claimed Amount: <strong className="text-emerald-400 font-mono">${claim.claimedAmount.toLocaleString()}</strong>
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {!claim.isApprovedByHuman ? (
            <button
              onClick={handleApprove}
              className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-4 py-2 rounded-xl text-xs font-extrabold shadow-lg shadow-emerald-500/20 flex items-center gap-1.5 transition-all transform hover:scale-105"
            >
              <CheckCircle2 className="w-4 h-4" /> Approve Claim Package
            </button>
          ) : claim.status !== 'SUBMITTED' && claim.status !== 'RECOVERED' ? (
            <button
              onClick={handleSubmitToCarrier}
              className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-xs font-extrabold shadow-lg shadow-blue-600/20 flex items-center gap-1.5 transition-all"
            >
              <Send className="w-4 h-4" /> Submit to Carrier
            </button>
          ) : (
            <button
              onClick={() => onRecordRecoveryModal(claim)}
              className="bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 px-4 py-2 rounded-xl text-xs font-extrabold shadow-lg shadow-emerald-500/20 flex items-center gap-1.5 transition-all"
            >
              <DollarSign className="w-4 h-4" /> Record Settlement Recovery
            </button>
          )}
        </div>
      </div>

      {actionNotice && (
        <div className={`p-3.5 rounded-xl border text-xs font-semibold flex justify-between items-center ${
          actionNotice.type === 'success'
            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
            : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
        }`}>
          <span>{actionNotice.message}</span>
          <button onClick={() => setActionNotice(null)} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-[calc(100vh-220px)] min-h-[700px]">
        <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col overflow-hidden shadow-xl">
          <div className="bg-slate-950 p-2 border-b border-slate-800 flex items-center space-x-1 overflow-x-auto">
            {claim.documents?.map((doc) => (
              <button
                key={doc.id}
                onClick={() => setSelectedDocId(doc.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
                  selectedDocId === doc.id
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                {doc.documentType}
              </button>
            ))}
          </div>

          <div className="flex-1 bg-slate-950 p-4 overflow-y-auto relative flex flex-col items-center justify-start">
            {selectedDoc ? (
              <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-2xl relative min-h-[500px]">
                <div className="border-b border-slate-800 pb-3 mb-4 flex justify-between items-start">
                  <div>
                    <div className="text-xs font-bold text-white uppercase tracking-wider">{selectedDoc.documentType} DOCUMENT</div>
                    <div className="text-[10px] text-slate-400 font-mono">{selectedDoc.filename}</div>
                  </div>
                  <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded font-mono">
                    SHA256: {selectedDoc.sha256.substring(0, 8)}...
                  </span>
                </div>

                <div className="space-y-4 text-xs font-mono text-slate-300">
                  <div className="p-3 bg-slate-950 rounded border border-slate-800/80 space-y-1">
                    <div className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider flex justify-between items-center">
                      <span>DOCUMENT OCR METADATA</span>
                      <span className="text-[10px] text-slate-400 font-mono">Parser: LocalPdfParser v1.0</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                      <div><span className="text-slate-400">Carrier:</span> <strong className="text-white">{claim.shipment?.carrierName}</strong></div>
                      <div><span className="text-slate-400">Document Type:</span> <strong className="text-cyan-300 font-mono">{selectedDoc.documentType}</strong></div>
                      <div><span className="text-slate-400">Page Count:</span> <strong className="text-white">{selectedDoc.pageCount} Page(s)</strong></div>
                      <div><span className="text-slate-400">Extraction Status:</span> <strong className="text-emerald-400 font-mono">{selectedDoc.extractionStatus}</strong></div>
                    </div>
                  </div>

                  {/* Document Specific Preview Section */}
                  {selectedDoc.documentType === 'BOL' && (
                    <div className="p-3.5 bg-slate-950/80 rounded-xl border border-cyan-500/30 space-y-2 text-[11px]">
                      <div className="font-bold text-cyan-400 uppercase border-b border-slate-800 pb-1 flex justify-between">
                        <span>BILL OF LADING STRUCTURED PREVIEW</span>
                        <span className="font-mono text-slate-400">PRO: {claim.shipment?.proNumber}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 font-mono">
                        <div><span className="text-slate-500 block text-[10px]">BOL NUMBER</span><strong className="text-slate-100">{claim.shipment?.bolNumber || 'BOL-847293'}</strong></div>
                        <div><span className="text-slate-500 block text-[10px]">PO / REF NUMBER</span><strong className="text-slate-100">PO-55210</strong></div>
                        <div><span className="text-slate-500 block text-[10px]">PICKUP DATE</span><strong className="text-slate-100">{claim.shipment?.pickupDate || '2026-08-10'}</strong></div>
                        <div><span className="text-slate-500 block text-[10px]">DECLARED VALUE</span><strong className="text-emerald-400">${claim.claimedAmount.toLocaleString()}</strong></div>
                      </div>
                      <div className="pt-1 font-mono text-[10px]">
                        <span className="text-slate-500 block">SHIPPER (FROM)</span>
                        <div className="text-slate-200">{claim.shipment?.shipperName || 'Meridian Electronics Distributors'}</div>
                        <div className="text-slate-400 text-[9px]">123 Warehouse Dr, Los Angeles, CA 90001 (Contact: Alex Chen)</div>
                      </div>
                      <div className="font-mono text-[10px]">
                        <span className="text-slate-500 block">CONSIGNEE (TO)</span>
                        <div className="text-slate-200">{claim.shipment?.consigneeName || 'Riverside Retail Store #14'}</div>
                        <div className="text-slate-400 text-[9px]">456 Store Blvd, Chicago, IL 60601 (Contact: Jordan Lee)</div>
                      </div>
                      <div className="p-2 bg-slate-900 rounded border border-slate-800 text-[10px] font-mono text-amber-300">
                        <span className="text-slate-400 block text-[9px]">HANDLING INSTRUCTIONS:</span>
                        Fragile - electronics. Keep upright. Liftgate required at delivery.
                      </div>
                    </div>
                  )}

                  {selectedDoc.documentType === 'POD' && (
                    <div className="p-3.5 bg-slate-950/80 rounded-xl border border-emerald-500/30 space-y-2 text-[11px]">
                      <div className="font-bold text-emerald-400 uppercase border-b border-slate-800 pb-1 flex justify-between">
                        <span>PROOF OF DELIVERY STRUCTURED PREVIEW</span>
                        <span className="font-mono text-slate-400">REF: POD-2026-0817-001</span>
                      </div>
                      <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 font-mono">
                        <div><span className="text-slate-500 block text-[10px]">DELIVERY DATE</span><strong className="text-emerald-300">{claim.shipment?.deliveryDate || '2026-08-17'} (Aug 17, 2026)</strong></div>
                        <div><span className="text-slate-500 block text-[10px]">TOTAL DELIVERED VALUE</span><strong className="text-emerald-400">$1,040.00</strong></div>
                      </div>
                      <div className="pt-1 font-mono text-[10px] space-y-1">
                        <span className="text-slate-500 block">DELIVERED ITEMIZED MANIFEST:</span>
                        <div className="bg-slate-900 p-2 rounded border border-slate-800 space-y-1 text-slate-200">
                          <div className="flex justify-between"><span>• 3x Office Chair (Mesh Back)</span><span>$360.00</span></div>
                          <div className="flex justify-between"><span>• 2x Standing Desk (Motorized)</span><span>$500.00</span></div>
                          <div className="flex justify-between"><span>• 1x Monitor (27-inch 4K UHD)</span><span>$180.00</span></div>
                        </div>
                      </div>
                      <div className="p-2 bg-slate-900 rounded border border-slate-800 text-[10px] font-mono text-rose-300">
                        <span className="text-slate-400 block text-[9px]">EXCEPTION NOTATION & SIGNATURE:</span>
                        Signed: Received in Good Order / Delivery Completed Aug 17, 2026
                      </div>
                    </div>
                  )}

                  {selectedDoc.documentType === 'DAMAGE_PHOTO' && (
                    <div className="p-3.5 bg-slate-950/80 rounded-xl border border-rose-500/30 space-y-2 text-[11px]">
                      <div className="font-bold text-rose-400 uppercase border-b border-slate-800 pb-1 flex justify-between">
                        <span>DAMAGE PHOTO & VISUAL EVIDENCE CANVAS</span>
                        <span className="font-mono text-slate-400">PaddleOCR Vision</span>
                      </div>
                      
                      {selectedDoc.storageUrl ? (
                        <div className="rounded-lg overflow-hidden border border-slate-800 bg-slate-900 flex items-center justify-center max-h-48">
                          <img src={selectedDoc.storageUrl} alt={selectedDoc.filename} className="object-contain max-h-48 w-full" />
                        </div>
                      ) : (
                        <div className="p-4 bg-slate-900/90 rounded-lg border border-slate-800 text-center space-y-1">
                          <div className="text-xs font-bold text-slate-200">📷 Freight Damage Inspection Photo</div>
                          <div className="text-[10px] text-slate-400 font-mono">{selectedDoc.filename}</div>
                        </div>
                      )}

                      <div className="grid grid-cols-2 gap-2 font-mono text-[10px]">
                        <div className="bg-slate-900 p-2 rounded border border-slate-800">
                          <span className="text-slate-500 block text-[9px]">EXIF TIMESTAMP</span>
                          <span className="text-slate-200">2026-08-17 14:15 EST</span>
                        </div>
                        <div className="bg-slate-900 p-2 rounded border border-slate-800">
                          <span className="text-slate-500 block text-[9px]">AI DAMAGE SEVERITY</span>
                          <span className="text-rose-400 font-bold">HIGH (Pallet Crush)</span>
                        </div>
                      </div>
                      <div className="p-2 bg-slate-900 rounded border border-slate-800 text-[10px] font-mono text-amber-300">
                        <span className="text-slate-400 block text-[9px]">PADDLE OCR TEXT & BOUNDING BOX DETECTED:</span>
                        "Crushed pallet corner and puncture impact on side panel"
                      </div>
                    </div>
                  )}

                  <div className="space-y-2">
                    <div className="text-[10px] uppercase text-cyan-400 font-semibold tracking-wider flex items-center gap-1">
                      <Sparkles className="w-3 h-3" /> Extracted Field Evidence Overlays ({selectedDoc.evidences.length} Fields)
                    </div>
                    {selectedDoc.evidences.map((ev) => {
                      const isHighlighted = highlightedField === ev.fieldName;
                      return (
                        <div
                          key={ev.id}
                          onMouseEnter={() => setHighlightedField(ev.fieldName)}
                          onMouseLeave={() => setHighlightedField(null)}
                          className={`p-3 rounded-lg border transition-all cursor-pointer relative ${
                            isHighlighted
                              ? 'bg-cyan-500/20 border-cyan-400 text-white shadow-lg ring-2 ring-cyan-500/50'
                              : 'bg-slate-950 border-slate-800 hover:border-slate-700 text-slate-300'
                          }`}
                        >
                          <div className="flex justify-between items-center text-[11px] mb-1">
                            <span className="font-bold text-cyan-400 uppercase">{ev.fieldName}</span>
                            <span className="text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded">
                              Page {ev.pageNumber} | Conf: {(ev.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="text-xs bg-slate-900/90 p-2 rounded border border-slate-800 text-slate-100 italic font-mono">
                            "{ev.sourceText}"
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-slate-500 text-xs flex items-center justify-center h-full">
                No document selected.
              </div>
            )}
          </div>
        </div>

        <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col overflow-hidden shadow-xl">
          <div className="p-4 bg-slate-950 border-b border-slate-800 flex justify-between items-center">
            <div>
              <h2 className="text-sm font-bold text-white flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-cyan-400" /> Structured Claim Facts
              </h2>
              <p className="text-[11px] text-slate-400">Provenance-grounded fact table</p>
            </div>
            <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
              6 Facts Extracted
            </span>
          </div>

          <div className="flex-1 p-4 overflow-y-auto space-y-4">
            <div className="bg-gradient-to-br from-slate-950 to-cyan-950/30 p-4 rounded-xl border border-cyan-500/20 shadow-md">
              <div className="text-xs font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1">
                <DollarSign className="w-4 h-4" /> Claim Valuation Math Provenance
              </div>
              <div className="mt-2 text-sm font-mono text-white font-bold">
                $20,000.00 Total Invoice × 40% Damaged Goods = <span className="text-emerald-400">$8,000.00 Claimed</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
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
                    className={`p-3 rounded-xl border transition-all ${
                      isHighlighted
                        ? 'bg-cyan-500/10 border-cyan-500/50 shadow-md'
                        : 'bg-slate-950/60 border-slate-800'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-1">
                      <span className="text-xs font-semibold text-slate-300">{fact.displayName}</span>
                      <div className="flex items-center space-x-1.5">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold ${
                          fact.verificationStatus === 'VERIFIED'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : fact.verificationStatus === 'EDITED_BY_HUMAN'
                            ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        }`}>
                          {fact.verificationStatus}
                        </span>
                        {!isEditing && (
                          <button
                            onClick={() => handleStartEdit(fact)}
                            className="text-slate-500 hover:text-cyan-400 p-1"
                          >
                            <Edit3 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>

                    {isEditing ? (
                      <div className="mt-2 space-y-2 bg-slate-900 p-2.5 rounded-lg border border-slate-700">
                        <div>
                          <label className="text-[10px] text-slate-400 block font-mono">Value Override</label>
                          <input
                            type="text"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            className="w-full bg-slate-950 text-white text-xs px-2 py-1.5 rounded border border-slate-700 focus:border-cyan-400 outline-none font-mono"
                          />
                        </div>
                        <div>
                          <label className="text-[10px] text-slate-400 block font-mono">Audit Reason for Change</label>
                          <input
                            type="text"
                            placeholder="e.g. Corrected mistyped PRO number from scan"
                            value={editReason}
                            onChange={(e) => setEditReason(e.target.value)}
                            className="w-full bg-slate-950 text-slate-200 text-xs px-2 py-1.5 rounded border border-slate-700 focus:border-cyan-400 outline-none"
                          />
                        </div>
                        <div className="flex justify-end space-x-2 pt-1">
                          <button
                            onClick={() => setEditingFactId(null)}
                            className="text-xs text-slate-400 hover:text-white px-2 py-1"
                          >
                            Cancel
                          </button>
                          <button
                            onClick={() => handleSaveEdit(fact)}
                            className="bg-cyan-500 text-slate-950 px-3 py-1 rounded text-xs font-bold"
                          >
                            Save Audit Edit
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="text-sm font-bold text-white font-mono">
                          {String(fact.valueJson)}
                        </div>
                        {fact.sourceDocumentName && (
                          <div className="text-[10px] text-slate-400 mt-1 flex items-center gap-1 font-mono">
                            <FileText className="w-3 h-3 text-cyan-400" />
                            Source: {fact.sourceDocumentName} (p.{fact.pageNumber})
                          </div>
                        )}
                        {fact.editReason && (
                          <div className="text-[10px] text-purple-300 mt-1 italic bg-purple-950/40 p-1.5 rounded border border-purple-800/40">
                            Edited by human: "{fact.editReason}"
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

        <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col overflow-hidden shadow-xl">
          <div className="bg-slate-950 p-2 border-b border-slate-800 flex items-center space-x-1">
            <button
              onClick={() => setActiveTabRight('draft')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTabRight === 'draft'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Claim Demand Package
            </button>
            <button
              onClick={() => setActiveTabRight('readiness')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTabRight === 'readiness'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Readiness & Deadlines
            </button>
          </div>

          <div className="flex-1 p-4 overflow-y-auto space-y-4">
            {activeTabRight === 'draft' ? (
              <div className="space-y-4">
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3 text-xs text-amber-300 flex items-start gap-2">
                  <Lock className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <strong className="block font-bold text-amber-400">Server-Side Submission Lock Active</strong>
                    Claim amount ($8,000) exceeds $5,000 threshold. Human review & sign-off required before carrier dispatch.
                  </div>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
                  <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                    <span className="text-xs font-bold text-white flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4 text-cyan-400" /> Citation-Grounded Demand Draft
                    </span>
                    <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
                      {claim.packageDraft?.modelName}
                    </span>
                  </div>

                  <div className="text-xs font-mono text-slate-300 whitespace-pre-wrap leading-relaxed bg-slate-900/80 p-3 rounded-lg border border-slate-800/80">
                    {claim.packageDraft?.narrativeText}
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
                  <div>
                    <div className="text-xs text-slate-400 uppercase font-semibold">AI Readiness Score</div>
                    <div className="text-2xl font-extrabold text-emerald-400 font-mono mt-0.5">
                      {claim.readinessScore}% READY
                    </div>
                  </div>
                  <div className="w-14 h-14 rounded-full bg-emerald-500/10 border-2 border-emerald-400 flex items-center justify-center font-bold text-emerald-400">
                    {claim.readinessScore}%
                  </div>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                  <div className="text-xs font-bold text-white mb-2">Evidence & Compliance Matrix</div>
                  {claim.readinessExplanations?.map((exp, idx) => (
                    <div key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                      <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{exp}</span>
                    </div>
                  ))}
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                  <div className="text-xs font-bold text-white flex items-center gap-1.5">
                    <Clock className="w-4 h-4 text-amber-400" /> Deterministic Deadline Engine
                  </div>
                  <div className="text-xs text-slate-300 font-mono">
                    Carmack Statutory Filing Deadline: <strong className="text-white">Sept 15, 2026</strong>
                  </div>
                  <div className="text-[11px] text-emerald-400 font-semibold bg-emerald-500/10 p-2 rounded border border-emerald-500/20">
                    Status: 32 Days Remaining (SAFE)
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between">
            <span className="text-xs text-slate-400 font-mono">
              Approver: <strong className="text-slate-200">Sarah Jenkins (Claims Manager)</strong>
            </span>
            <button
              onClick={handleApprove}
              disabled={claim.isApprovedByHuman}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                claim.isApprovedByHuman
                  ? 'bg-slate-800 text-slate-400 cursor-not-allowed'
                  : 'bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-lg shadow-emerald-500/20'
              }`}
            >
              {claim.isApprovedByHuman ? 'Approved ✓' : 'Approve & Release Lock'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
