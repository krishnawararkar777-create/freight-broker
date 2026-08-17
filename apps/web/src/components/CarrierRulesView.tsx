import React from 'react';
import type { CarrierRuleSet } from '../types/claim';
import { Scale, ShieldCheck } from 'lucide-react';

interface CarrierRulesViewProps {
  ruleSets: Record<string, CarrierRuleSet>;
}

export const CarrierRulesView: React.FC<CarrierRulesViewProps> = ({ ruleSets }) => {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Scale className="w-5 h-5 text-cyan-400" /> Carrier Rules & Statutory Engine
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Sourced and versioned tariff rules. Statutory Carmack limits & carrier-specific concealed damage notice windows.
          </p>
        </div>

        <div className="bg-slate-950 px-4 py-2 rounded-xl border border-slate-800 font-mono text-xs text-emerald-400 flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4" /> Versioned & Legal Compliance Verified
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.values(ruleSets).map((rule) => (
          <div key={rule.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-4">
            <div className="flex justify-between items-start border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white">{rule.carrierName}</h3>
                <span className="text-[10px] text-cyan-400 font-mono">RuleSet v{rule.version}</span>
              </div>
              <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded text-[10px] font-semibold">
                ACTIVE
              </span>
            </div>

            <div className="space-y-2 text-xs font-mono text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-400">Carmack Window:</span>
                <span className="font-bold text-white">{rule.carmackFilingWindowMonths} Months (Federal Min)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Concealed Damage Notice:</span>
                <span className="font-bold text-amber-400">{rule.concealedDamageNoticeDays} Days</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Post-Denial Lawsuit Window:</span>
                <span className="font-bold text-white">{rule.postDenialLawsuitYears} Years + 1 Day</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Submission Channel:</span>
                <span className="font-bold text-cyan-400">{rule.submissionChannel} ({rule.submissionTarget})</span>
              </div>
            </div>

            <div className="p-2.5 bg-slate-950 rounded-xl border border-slate-800 text-[11px] text-slate-400 space-y-1">
              <div className="font-semibold text-slate-300 flex justify-between items-center">
                <span>Source Citation:</span>
                {rule.sourceCitation.includes('UNVERIFIED') ? (
                  <span className="text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 px-1.5 py-0.5 rounded font-mono font-semibold">
                    UNVERIFIED DEMO
                  </span>
                ) : (
                  <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-1.5 py-0.5 rounded font-mono font-semibold">
                    VERIFIED TARIFF
                  </span>
                )}
              </div>
              <div className="italic font-mono text-[10px] text-slate-300">{rule.sourceCitation}</div>
              <div className="text-[10px] text-slate-500 pt-1">
                Verified: {rule.lastVerifiedAt} by {rule.verifiedBy}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
