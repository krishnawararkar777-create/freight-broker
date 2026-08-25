import React from 'react';
import type { Claim, RecoveryEvent, FeeEvent } from '../types/claim';
import { Receipt, CheckCircle2 } from 'lucide-react';

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
    <div className="space-y-6 animate-fade-in font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pt-1 pb-2">
        <div>
          <h1 className="font-serif text-3xl sm:text-4xl text-white font-bold tracking-tight">
            Fee & Recovery Ledger
          </h1>
          <p className="text-zinc-400 text-sm mt-1 max-w-xl font-sans">
            Auditable event-based financial ledger. Algolyra fees are calculated strictly from verified recovery dollars.
          </p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 px-4 py-2 rounded-2xl font-mono text-xs text-zinc-300 shadow-sm">
          Formula: <strong className="text-white">Fee = Eligible Recovered × 20% Contingency Rate</strong>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 font-montserrat">
        <div className="bg-zinc-950 rounded-2xl p-5 border border-zinc-800/80 shadow-xl flex flex-col justify-between">
          <div className="text-[11px] font-montserrat font-bold uppercase tracking-widest text-zinc-400">
            GROSS CARRIER RECOVERIES
          </div>
          <div className="text-3xl sm:text-4xl font-bold font-grotesk text-white mt-4 tracking-tight">
            ${totalRecovered.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <p className="text-xs font-montserrat text-zinc-500 mt-2">
            Total funds collected from carriers
          </p>
        </div>

        <div className="bg-zinc-950 rounded-2xl p-5 border border-zinc-800/80 shadow-xl flex flex-col justify-between">
          <div className="text-[11px] font-montserrat font-bold uppercase tracking-widest text-zinc-400">
            ALGOLYRA CONTINGENCY REVENUE
          </div>
          <div className="text-3xl sm:text-4xl font-bold font-grotesk text-white mt-4 tracking-tight">
            ${totalAlgolyraFees.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <p className="text-xs font-montserrat text-zinc-500 mt-2">
            20% fee on recovered dollars ($0 on $0)
          </p>
        </div>

        <div className="bg-white text-black rounded-2xl p-5 border border-white shadow-2xl flex flex-col justify-between">
          <div className="text-[11px] font-montserrat font-bold uppercase tracking-widest text-zinc-600">
            BROKER NET RETAINED
          </div>
          <div className="text-3xl sm:text-4xl font-bold font-grotesk text-black mt-4 tracking-tight">
            ${netBrokerPayout.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <p className="text-xs font-montserrat font-semibold text-zinc-800 mt-2">
            Recovered value retained by broker
          </p>
        </div>
      </div>

      {/* Ledger Table or Honest Zero-State */}
      <div className="bg-zinc-950 rounded-2xl border border-zinc-800/80 overflow-hidden shadow-2xl p-6 space-y-4">
        <div className="flex justify-between items-center pb-2 border-b border-zinc-800/80">
          <div>
            <h2 className="font-serif text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              <Receipt className="w-5 h-5 text-white" /> Recovery & Fee Audit Trail
            </h2>
            <p className="text-xs text-zinc-400 mt-0.5 font-montserrat">
              Immutable timestamped ledger events
            </p>
          </div>
          <span className="text-xs font-mono font-bold text-zinc-300 bg-zinc-900 border border-zinc-800 px-3.5 py-1 rounded-full">
            {recoveryEvents.length} Verified Recovery Events
          </span>
        </div>

        {recoveryEvents.length === 0 ? (
          <div className="py-12 text-center space-y-3 font-montserrat">
            <div className="w-12 h-12 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center mx-auto text-zinc-400">
              <Receipt className="w-6 h-6 text-zinc-300" />
            </div>
            <h3 className="text-sm font-bold text-white">No Recovery Ledger Events Yet</h3>
            <p className="text-xs text-zinc-400 max-w-sm mx-auto">
              This organization has $0 in carrier recoveries. When a cargo claim settlement is recorded, verified fee ledger entries will automatically appear here.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-zinc-300 border-collapse">
              <thead>
                <tr className="text-[10px] font-mono font-semibold tracking-wider text-zinc-400 uppercase border-b border-zinc-800">
                  <th className="py-3 px-4">EVENT ID</th>
                  <th className="py-3 px-4">CLAIM #</th>
                  <th className="py-3 px-4">PAYER / CARRIER</th>
                  <th className="py-3 px-4">PAYMENT REF</th>
                  <th className="py-3 px-4">RECOVERED AMOUNT</th>
                  <th className="py-3 px-4">RATE</th>
                  <th className="py-3 px-4">ALGOLYRA FEE</th>
                  <th className="py-3 px-4">STATUS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/60 font-mono">
                {recoveryEvents.map((rec) => {
                  const fee = feeEvents.find(f => f.recoveryEventId === rec.id);
                  const claim = claims.find(c => c.id === rec.claimId);

                  return (
                    <tr key={rec.id} className="hover:bg-zinc-900/60 transition-colors">
                      <td className="py-4 px-4 font-bold text-white">{rec.id}</td>
                      <td className="py-4 px-4 font-bold text-zinc-200">{claim?.claimNumber || rec.claimId}</td>
                      <td className="py-4 px-4 text-zinc-300 font-sans">{rec.payer}</td>
                      <td className="py-4 px-4 text-zinc-500">{rec.paymentReference}</td>
                      <td className="py-4 px-4 font-extrabold text-white">${rec.amount.toLocaleString()}</td>
                      <td className="py-4 px-4 text-zinc-400">{((fee?.contingencyRate || 0.2) * 100).toFixed(0)}%</td>
                      <td className="py-4 px-4 font-extrabold text-white">${fee?.feeAmount.toLocaleString()}</td>
                      <td className="py-4 px-4">
                        <span className="bg-zinc-900 text-emerald-400 border border-zinc-800 px-2.5 py-1 rounded-full font-mono text-[11px] font-semibold flex items-center gap-1 w-fit">
                          <CheckCircle2 className="w-3 h-3 text-emerald-400" /> {fee?.status || 'INVOICED'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
