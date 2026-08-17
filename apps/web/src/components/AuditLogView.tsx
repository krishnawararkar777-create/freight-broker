import React from 'react';
import type { AuditEvent } from '../types/claim';
import { Activity, UserCheck, Bot } from 'lucide-react';

interface AuditLogViewProps {
  auditEvents: AuditEvent[];
}

export const AuditLogView: React.FC<AuditLogViewProps> = ({ auditEvents }) => {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-cyan-400" /> AI Telemetry & Server Guard Audit Trail
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Immutable log of every state machine transition, extraction confidence trace, and human review decision.
          </p>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 font-bold text-white text-sm">
          System Execution Log ({auditEvents.length} Events)
        </div>

        <div className="p-4 space-y-3 font-mono text-xs">
          {auditEvents.map((evt) => (
            <div key={evt.id} className="p-3 bg-slate-950 rounded-xl border border-slate-800/80 flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
              <div className="flex items-center space-x-3">
                <span className={`p-1.5 rounded-lg text-xs font-bold flex items-center gap-1 ${
                  evt.actorType === 'AI'
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                    : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                }`}>
                  {evt.actorType === 'AI' ? <Bot className="w-3.5 h-3.5"/> : <UserCheck className="w-3.5 h-3.5"/>}
                  {evt.actorType}
                </span>

                <div>
                  <div className="text-white font-bold">{evt.action}</div>
                  <div className="text-slate-400 text-[11px]">Actor: {evt.actorId}</div>
                  {evt.reason && (
                    <div className="text-amber-400 text-[10px] italic mt-0.5">{evt.reason}</div>
                  )}
                </div>
              </div>

              <div className="text-[10px] text-slate-500 font-mono">
                {new Date(evt.createdAt).toLocaleTimeString()} ({evt.id})
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
