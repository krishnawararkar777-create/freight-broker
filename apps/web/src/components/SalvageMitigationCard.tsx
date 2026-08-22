import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, Calculator, CheckCircle2, MapPin, FileText, DollarSign
} from 'lucide-react';
import type { Claim } from '../types/claim';

interface SalvageMitigationCardProps {
  claim: Claim;
  onClaimDemandUpdated?: (netAmount: number) => void;
}

export const COMMODITY_OPTIONS = [
  { value: 'METALS_MACHINERY', label: 'Metals & Industrial Machinery', baseRate: '40% base scrap residual' },
  { value: 'ELECTRONICS', label: 'Electronic Components & Equipment', baseRate: '25% base parts/refurb residual' },
  { value: 'DRY_GOODS', label: 'Dry Packaged Goods & Retail Merchandise', baseRate: '15% discount retailer residual' },
  { value: 'GENERAL_MERCHANDISE', label: 'General Freight & Commodity Mix', baseRate: '10% generic residual' },
  { value: 'PERISHABLES_FOOD', label: 'Food & Perishables (FDA/Sanitary Destruction)', baseRate: '0% (Mandated Total Loss)' },
  { value: 'PHARMACEUTICALS', label: 'Pharmaceuticals / Health Products (DEA/FDA)', baseRate: '0% (Mandated Total Loss)' },
];

export const DISPOSITION_OPTIONS = [
  { value: 'RETAINED_FOR_SALVAGE', label: 'Retained on Site for Carrier Inspection', badge: 'bg-amber-950/60 text-amber-300 border-amber-800/40' },
  { value: 'DESTROYED', label: 'Certified Destruction (Health/Safety Mandate)', badge: 'bg-rose-950/60 text-rose-300 border-rose-800/40' },
  { value: 'SOLD_BY_CONSIGNEE', label: 'Realized Salvage Sale (Net Proceeds Deducted)', badge: 'bg-emerald-950/60 text-emerald-300 border-emerald-800/40' },
  { value: 'PENDING_INSPECTION', label: 'Pending Carrier Salvage Inspector', badge: 'bg-blue-950/60 text-blue-300 border-blue-800/40' },
];

export const SalvageMitigationCard: React.FC<SalvageMitigationCardProps> = ({ claim, onClaimDemandUpdated }) => {
  const [commodity, setCommodity] = useState<string>('ELECTRONICS');
  const [damageSeverity, setDamageSeverity] = useState<number>(0.30); // 30% damage
  const [grossInvoice, setGrossInvoice] = useState<number>(claim.claimedAmount || 5000);
  const [realizedValue, setRealizedValue] = useState<string>('');
  const [dispositionStatus, setDispositionStatus] = useState<string>('RETAINED_FOR_SALVAGE');
  const [storageLocation, setStorageLocation] = useState<string>('Consignee Dock Bay 4, Secure Cage');
  const [notes, setNotes] = useState<string>('Palletized in original packaging with shrink-wrap preserved for carrier adjuster inspection.');
  
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [showProofDoc, setShowProofDoc] = useState<boolean>(false);

  // Fetch active salvage record on mount
  useEffect(() => {
    fetch(`http://localhost:8000/api/claims/${claim.id}/salvage`)
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data) {
          setCommodity(data.commodity_category);
          setDamageSeverity(data.damage_severity_score);
          setGrossInvoice(data.gross_invoice_value);
          setRealizedValue(data.realized_salvage_value ? String(data.realized_salvage_value) : '');
          setDispositionStatus(data.disposition_status);
          if (data.storage_location) setStorageLocation(data.storage_location);
          if (data.notes) setNotes(data.notes);
        }
      })
      .catch(() => {});
  }, [claim.id]);

  // Deterministic local calculation
  const getBaseRate = (cat: string) => {
    switch (cat) {
      case 'METALS_MACHINERY': return 0.40;
      case 'ELECTRONICS': return 0.25;
      case 'DRY_GOODS': return 0.15;
      case 'PERISHABLES_FOOD':
      case 'PHARMACEUTICALS': return 0.00;
      default: return 0.10;
    }
  };

  const baseRate = getBaseRate(commodity);
  const effectiveSalvageRate = Math.round(baseRate * (1 - damageSeverity) * 10000) / 10000;
  const estimatedSalvage = Math.round(grossInvoice * effectiveSalvageRate * 100) / 100;
  const salvageOffset = realizedValue ? parseFloat(realizedValue) || 0 : estimatedSalvage;
  const netClaimDemand = Math.max(0, Math.round((grossInvoice - salvageOffset) * 100) / 100);

  const handleSaveSalvage = async () => {
    setIsSaving(true);
    setSaveSuccess(null);
    try {
      const payload = {
        commodity_category: commodity,
        damage_severity_score: damageSeverity,
        gross_invoice_value: grossInvoice,
        realized_salvage_value: realizedValue ? parseFloat(realizedValue) : null,
        disposition_status: dispositionStatus,
        storage_location: storageLocation,
        notes: notes,
      };

      const res = await fetch(`http://localhost:8000/api/claims/${claim.id}/salvage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setSaveSuccess('Salvage valuation & factual mitigation record saved. Claim net demand updated.');
        if (onClaimDemandUpdated) {
          onClaimDemandUpdated(netClaimDemand);
        }
      } else {
        setSaveSuccess('Error saving salvage record.');
      }
    } catch {
      setSaveSuccess('Failed to connect to salvage API.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl space-y-6 text-slate-100">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-cyan-950/80 text-cyan-400 border border-cyan-800/50 rounded-lg">
            <Calculator className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">Salvage Valuation & Mitigation Engine</h3>
            <p className="text-xs text-slate-400">
              Deterministic loss mitigation math neutralizing carrier "Failure to Protect Salvage" pretexts
            </p>
          </div>
        </div>
        <span className="px-3 py-1 text-xs font-semibold rounded-full bg-emerald-950/60 text-emerald-300 border border-emerald-800/40 flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5" /> NMFC Mitigation Guard
        </span>
      </div>

      {/* Grid Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Commodity Category */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300">Commodity Classification</label>
          <select
            value={commodity}
            onChange={(e) => setCommodity(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            {COMMODITY_OPTIONS.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
          <p className="text-[11px] text-cyan-400/90 font-mono">
            {COMMODITY_OPTIONS.find((c) => c.value === commodity)?.baseRate}
          </p>
        </div>

        {/* Damage Severity Slider */}
        <div className="space-y-1.5">
          <div className="flex justify-between items-center text-xs">
            <span className="font-semibold text-slate-300">Damage Severity Score</span>
            <span className="font-mono font-bold text-amber-400">{(damageSeverity * 100).toFixed(0)}% Damaged ({(100 - damageSeverity * 100).toFixed(0)}% Sound)</span>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={damageSeverity}
            onChange={(e) => setDamageSeverity(parseFloat(e.target.value))}
            className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
          />
          <div className="flex justify-between text-[10px] text-slate-400">
            <span>Minor Scuffs (0%)</span>
            <span>Partial Damage (50%)</span>
            <span>Total Destruction (100%)</span>
          </div>
        </div>

        {/* Gross Invoiced Loss */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300">Gross Invoiced Value ($)</label>
          <div className="relative">
            <DollarSign className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="number"
              value={grossInvoice}
              onChange={(e) => setGrossInvoice(parseFloat(e.target.value) || 0)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>

        {/* Realized Salvage Proceeds (Optional) */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300">
            Realized Salvage Sale Proceeds ($) <span className="text-slate-400 font-normal">(Optional Override)</span>
          </label>
          <div className="relative">
            <DollarSign className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="number"
              placeholder="Leave empty to use AI estimate"
              value={realizedValue}
              onChange={(e) => setRealizedValue(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>
      </div>

      {/* Math Breakdown Box */}
      <div className="bg-slate-950/80 border border-cyan-900/40 rounded-xl p-4 space-y-3">
        <div className="text-xs font-semibold text-cyan-300 uppercase tracking-wider flex items-center gap-1.5">
          <Calculator className="w-4 h-4" /> Deterministic Claim Net Demand Calculation
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-center">
          <div className="bg-slate-900/90 border border-slate-800 p-3 rounded-lg">
            <div className="text-[11px] text-slate-400">Gross Invoiced Loss</div>
            <div className="text-lg font-bold text-white font-mono">${grossInvoice.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
          </div>
          <div className="bg-slate-900/90 border border-slate-800 p-3 rounded-lg">
            <div className="text-[11px] text-slate-400">
              {realizedValue ? 'Realized Salvage Sale' : `Estimated Salvage (${(effectiveSalvageRate * 100).toFixed(1)}%)`}
            </div>
            <div className="text-lg font-bold text-amber-400 font-mono">
              - ${salvageOffset.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </div>
          </div>
          <div className="bg-emerald-950/40 border border-emerald-800/60 p-3 rounded-lg">
            <div className="text-[11px] text-emerald-400 font-semibold">Net Claim Demand to Carrier</div>
            <div className="text-lg font-extrabold text-emerald-300 font-mono">
              ${netClaimDemand.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </div>
          </div>
        </div>
      </div>

      {/* Cargo Disposition Record */}
      <div className="space-y-4 pt-2 border-t border-slate-800">
        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Factual Cargo Disposition & Storage Record
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs text-slate-300">Physical Disposition Status</label>
            <select
              value={dispositionStatus}
              onChange={(e) => setDispositionStatus(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
            >
              {DISPOSITION_OPTIONS.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs text-slate-300">Storage / Segregation Location</label>
            <div className="relative">
              <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={storageLocation}
                onChange={(e) => setStorageLocation(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs text-slate-300">Factual Mitigation Notes</label>
          <textarea
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      {/* Action Buttons & Feedback */}
      <div className="flex items-center justify-between pt-3 border-t border-slate-800">
        <button
          type="button"
          onClick={() => setShowProofDoc(!showProofDoc)}
          className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1.5 transition-colors"
        >
          <FileText className="w-4 h-4" /> {showProofDoc ? 'Hide Mitigation Proof Document' : 'View Factual Mitigation Record'}
        </button>

        <button
          type="button"
          onClick={handleSaveSalvage}
          disabled={isSaving}
          className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium text-xs rounded-lg shadow-lg shadow-cyan-900/30 transition-all flex items-center gap-2 disabled:opacity-50"
        >
          {isSaving ? 'Updating...' : 'Save & Update Net Demand'}
        </button>
      </div>

      {saveSuccess && (
        <div className="p-3 bg-emerald-950/60 border border-emerald-800/40 rounded-lg text-xs text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          {saveSuccess}
        </div>
      )}

      {/* Factual Mitigation Proof Document Preview */}
      {showProofDoc && (
        <div className="mt-4 p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="font-bold text-slate-200">FACTUAL RECORD OF CARGO LOSS MITIGATION & SALVAGE</span>
            <span className="text-[10px] text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded">STATUS: DUTY SATISFIED</span>
          </div>
          <div className="text-slate-300 text-[11px] leading-relaxed space-y-1.5">
            <p><strong>Claim ID:</strong> {claim.id} | <strong>Claim Reference:</strong> {claim.claimNumber || 'CLM-847293'}</p>
            <p><strong>Gross Invoice Value:</strong> ${grossInvoice.toFixed(2)}</p>
            <p><strong>Salvage Offset Deducted:</strong> -${salvageOffset.toFixed(2)} ({realizedValue ? 'Realized Sale' : `${commodity} ${(effectiveSalvageRate * 100).toFixed(1)}%`})</p>
            <p><strong>Net Claim Demand to Carrier:</strong> ${netClaimDemand.toFixed(2)}</p>
            <p><strong>Physical Disposition:</strong> {dispositionStatus} at {storageLocation}</p>
            <p className="p-2.5 bg-slate-900/90 border border-slate-800 rounded text-slate-400 mt-2">
              "This factual record documents that cargo under claim {claim.id} was mitigated pursuant to standard cargo loss duty. Gross invoice value of ${grossInvoice.toFixed(2)} has been adjusted by a salvage deduction of ${salvageOffset.toFixed(2)}, yielding a net claim demand of ${netClaimDemand.toFixed(2)}. Current physical disposition: {dispositionStatus} at {storageLocation}."
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
