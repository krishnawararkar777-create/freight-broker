import React from 'react';
import type { Claim, RecoveryEvent, FeeEvent } from '../types/claim';
import { Receipt } from 'lucide-react';

interface RecoveryLedgerViewProps {
  claims: Claim[];
  recoveryEvents: RecoveryEvent[];
  feeEvents: FeeEvent[];
}

export const RecoveryLedgerView: React.FC<RecoveryLedgerViewProps> = ({
  claims,
  recoveryEvents,
  feeEvents
}) => {
  const totalRecovered = recoveryEvents.reduce((sum, r) => sum + r.amount, 0);
  const totalAlgolyraFees = feeEvents.reduce((sum, f) => sum + f.feeAmount, 0);
  const netBrokerPayout = totalRecovered - totalAlgolyraFees;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Receipt className="w-5 h-5 text-cyan-400" /> Contingency Fee & Recovery Ledger
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Auditable event-based ledger. Algolyra fees are calculated strictly from verified recovery dollars.
          </p>
        </div>

        <div className="bg-slate-950 px-4 py-2 rounded-xl border border-slate-800 font-mono text-xs text-slate-300">
          Formula: <strong className="text-cyan-400">Fee = Eligible Recovered × 20% Contingency Rate</strong>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900 rounded-2xl p-5 border border-slate-800 shadow-lg">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Gross Carrier Recoveries</div>
          <div className="text-3xl font-extrabold text-emerald-400 font-mono mt-2">
            ${totalRecovered.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Total funds collected from carriers
          </p>
        </div>

        <div className="bg-slate-900 rounded-2xl p-5 border border-slate-800 shadow-lg">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Algolyra Contingency Revenue</div>
          <div className="text-3xl font-extrabold text-cyan-400 font-mono mt-2">
            ${totalAlgolyraFees.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            20% fee on recovered dollars ($0 on $0)
          </p>
        </div>

        <div className="bg-slate-900 rounded-2xl p-5 border border-slate-800 shadow-lg">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Broker Net Retained</div>
          <div className="text-3xl font-extrabold text-white font-mono mt-2">
            ${netBrokerPayout.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Recovered value retained by broker
          </p>
        </div>
      </div>

      <div className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 font-bold text-white text-sm flex justify-between items-center">
          <span>Recovery & Fee Event Audit Ledger</span>
          <span className="text-xs font-normal text-slate-400">{recoveryEvents.length} Verified Recovery Events</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-6 py-3.5">Event ID</th>
                <th className="px-6 py-3.5">Claim #</th>
                <th className="px-6 py-3.5">Payer / Carrier</th>
                <th className="px-6 py-3.5">Payment Ref</th>
                <th className="px-6 py-3.5">Recovered Amount</th>
                <th className="px-6 py-3.5">Rate</th>
                <th className="px-6 py-3.5">Algolyra Fee</th>
                <th className="px-6 py-3.5">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 font-mono">
              {recoveryEvents.map((rec) => {
                const fee = feeEvents.find(f => f.recoveryEventId === rec.id);
                const claim = claims.find(c => c.id === rec.claimId);

                return (
                  <tr key={rec.id} className="hover:bg-slate-800/40">
                    <td className="px-6 py-4 text-xs font-bold text-cyan-400">{rec.id}</td>
                    <td className="px-6 py-4 text-xs text-white font-bold">{claim?.claimNumber}</td>
                    <td className="px-6 py-4 text-xs text-slate-200">{rec.payer}</td>
                    <td className="px-6 py-4 text-xs text-slate-400">{rec.paymentReference}</td>
                    <td className="px-6 py-4 text-sm font-extrabold text-emerald-400">${rec.amount.toLocaleString()}</td>
                    <td className="px-6 py-4 text-xs text-slate-300">{( (fee?.contingencyRate || 0.2) * 100).toFixed(0)}%</td>
                    <td className="px-6 py-4 text-sm font-extrabold text-cyan-400">${fee?.feeAmount.toLocaleString()}</td>
                    <td className="px-6 py-4 text-xs">
                      <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded font-sans font-semibold">
                        {fee?.status || 'INVOICED'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
