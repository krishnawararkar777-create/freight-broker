import React from 'react';
import type { CarrierRuleSet } from '../types/claim';
import { ShieldCheck } from 'lucide-react';

interface CarrierRulesViewProps {
  ruleSets: Record<string, CarrierRuleSet>;
}

export const CarrierRulesView: React.FC<CarrierRulesViewProps> = ({ ruleSets }) => {
  return (
    <div className="space-y-6 animate-fade-in font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pt-1 pb-2">
        <div>
          <h1 className="font-serif text-3xl sm:text-4xl text-white font-bold tracking-tight">
            Carrier Rules & Statutory Engine
          </h1>
          <p className="text-zinc-400 text-sm mt-1 max-w-xl font-sans">
            Sourced and versioned tariff rules. Statutory Carmack limits & carrier-specific concealed damage notice windows.
          </p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 px-4 py-2 rounded-2xl font-mono text-xs text-white flex items-center gap-1.5 shadow-sm">
          <ShieldCheck className="w-4 h-4 text-emerald-400" /> 
          <span>Versioned Tariff Rules Verified</span>
        </div>
      </div>

      {/* Rules Grid (2 Boxes per Row) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 font-montserrat">
        {Object.values(ruleSets).map((rule) => (
          <div key={rule.id} className="bg-zinc-950 border border-zinc-800/80 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex justify-between items-start border-b border-zinc-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white uppercase tracking-wide">{rule.carrierName}</h3>
                <span className="text-[10px] text-zinc-400 font-mono">RuleSet v{rule.version}</span>
              </div>
              <span className="bg-zinc-900 text-white border border-zinc-700 px-2 py-0.5 rounded text-[10px] font-mono font-bold">
                ACTIVE
              </span>
            </div>

            <div className="space-y-2 text-xs font-mono text-zinc-300">
              <div className="flex justify-between">
                <span className="text-zinc-500">Carmack Window:</span>
                <span className="font-bold text-white">{rule.carmackFilingWindowMonths} Months (Federal Min)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Concealed Damage Notice:</span>
                <span className="font-bold text-white">{rule.concealedDamageNoticeDays} Days</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Post-Denial Lawsuit Window:</span>
                <span className="font-bold text-white">{rule.postDenialLawsuitYears} Years + 1 Day</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Submission Channel:</span>
                <span className="font-bold text-white">{rule.submissionChannel} ({rule.submissionTarget})</span>
              </div>
            </div>

            <div className="p-3 bg-zinc-900/60 rounded-xl border border-zinc-800 text-[11px] text-zinc-400 space-y-1.5">
              <div className="font-semibold text-zinc-300 flex justify-between items-center font-mono text-[10px]">
                <span>Source Citation:</span>
                {rule.sourceCitation.includes('UNVERIFIED') ? (
                  <span className="bg-zinc-900 text-amber-400 border border-zinc-800 px-1.5 py-0.5 rounded font-mono font-semibold">
                    UNVERIFIED DEMO
                  </span>
                ) : (
                  <span className="bg-zinc-900 text-emerald-400 border border-zinc-800 px-1.5 py-0.5 rounded font-mono font-semibold">
                    VERIFIED TARIFF
                  </span>
                )}
              </div>
              <div className="italic font-mono text-[10px] text-zinc-300">{rule.sourceCitation}</div>
              <div className="text-[10px] text-zinc-500 pt-1 font-mono">
                Verified: {rule.lastVerifiedAt} by {rule.verifiedBy}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
