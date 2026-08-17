import React, { useState } from 'react';
import type { Claim } from '../types/claim';
import { DollarSign, CheckCircle2, X } from 'lucide-react';
import { recordRecoveryEvent } from '../services/billingLedger';

interface RecordRecoveryModalProps {
  claim: Claim | null;
  isOpen: boolean;
  onClose: () => void;
  onRecordRecovery: (updatedClaim: Claim, recoveryEvent: any, feeEvent: any) => void;
}

export const RecordRecoveryModal: React.FC<RecordRecoveryModalProps> = ({
  claim,
  isOpen,
  onClose,
  onRecordRecovery
}) => {
  const [amount, setAmount] = useState<string>('7500');
  const [paymentRef, setPaymentRef] = useState<string>('CHK-77192-CARRIER');
  const [payer, setPayer] = useState<string>(claim?.shipment?.carrierName || 'ABC Trucking');

  if (!isOpen || !claim) return null;

  const numericAmount = Number(amount) || 0;
  const feeAmount = numericAmount * 0.20;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const result = recordRecoveryEvent(
      claim,
      numericAmount,
      0.20,
      paymentRef,
      payer
    );

    const updatedClaim: Claim = {
      ...claim,
      ...result.updatedClaim
    };

    onRecordRecovery(updatedClaim, result.recoveryEvent, result.feeEvent);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5 animate-scale-up">
        <div className="flex justify-between items-center border-b border-slate-800 pb-3">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-emerald-400" /> Record Settlement Recovery
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs text-slate-300 font-mono block">Claim Number</label>
            <input
              type="text"
              disabled
              value={claim.claimNumber}
              className="w-full bg-slate-950 text-slate-400 text-xs px-3 py-2 rounded-lg border border-slate-800 font-mono"
            />
          </div>

          <div>
            <label className="text-xs text-slate-300 font-mono block">Carrier Settlement Check Amount ($)</label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="w-full bg-slate-950 text-emerald-400 text-sm font-bold px-3 py-2 rounded-lg border border-slate-700 focus:border-emerald-400 outline-none font-mono"
            />
          </div>

          <div>
            <label className="text-xs text-slate-300 font-mono block">Payer / Carrier Name</label>
            <input
              type="text"
              value={payer}
              onChange={(e) => setPayer(e.target.value)}
              className="w-full bg-slate-950 text-slate-200 text-xs px-3 py-2 rounded-lg border border-slate-700 focus:border-emerald-400 outline-none"
            />
          </div>

          <div>
            <label className="text-xs text-slate-300 font-mono block">Check / Check Reference #</label>
            <input
              type="text"
              value={paymentRef}
              onChange={(e) => setPaymentRef(e.target.value)}
              className="w-full bg-slate-950 text-slate-200 text-xs px-3 py-2 rounded-lg border border-slate-700 focus:border-emerald-400 outline-none font-mono"
            />
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs space-y-1">
            <div className="flex justify-between text-slate-400">
              <span>Gross Recovery:</span>
              <span className="text-white font-mono font-bold">${numericAmount.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-cyan-400 font-semibold">
              <span>Algolyra Fee (20%):</span>
              <span className="font-mono">${feeAmount.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-emerald-400 font-extrabold border-t border-slate-800 pt-1">
              <span>Broker Net Retained:</span>
              <span className="font-mono">${(numericAmount - feeAmount).toLocaleString()}</span>
            </div>
          </div>

          <button
            type="submit"
            className="w-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-extrabold py-2.5 rounded-xl text-sm transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-1.5"
          >
            <CheckCircle2 className="w-4 h-4" /> Confirm & Record Recovery Event
          </button>
        </form>
      </div>
    </div>
  );
};
