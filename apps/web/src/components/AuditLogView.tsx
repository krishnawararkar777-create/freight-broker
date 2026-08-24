import React from 'react';
import type { AuditEvent } from '../types/claim';
import { Activity, UserCheck, Bot } from 'lucide-react';

interface AuditLogViewProps {
  auditEvents: AuditEvent[];
}

export const AuditLogView: React.FC<AuditLogViewProps> = ({ auditEvents }) => {
  return (
    <div className="space-y-6 animate-fade-in font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pt-1 pb-2">
        <div>
          <h1 className="font-serif text-3xl sm:text-4xl text-white font-bold tracking-tight">
            Audit Log & Telemetry
          </h1>
          <p className="text-zinc-400 text-sm mt-1 max-w-xl font-sans">
            Immutable trace of state machine transitions, OCR extraction provenance, and human review decisions.
          </p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 px-4 py-2 rounded-2xl font-mono text-xs text-zinc-300 shadow-sm flex items-center gap-2">
          <Activity className="w-4 h-4 text-white" />
          <span>Total Audit Events: {auditEvents.length}</span>
        </div>
      </div>

      {/* Events Card */}
      <div className="bg-zinc-950 border border-zinc-800/80 rounded-2xl overflow-hidden shadow-2xl p-6 space-y-4">
        <div className="flex justify-between items-center pb-2 border-b border-zinc-800/80">
          <h2 className="font-serif text-2xl font-bold text-white tracking-tight">
            System Execution Log
          </h2>
          <span className="text-xs font-mono font-semibold text-zinc-400">
            Real-Time Audit Stream
          </span>
        </div>

        <div className="space-y-2.5 font-mono text-xs">
          {auditEvents.map((evt) => (
            <div key={evt.id} className="p-3.5 bg-zinc-900/50 rounded-xl border border-zinc-800/80 flex flex-col md:flex-row justify-between items-start md:items-center gap-3 hover:border-zinc-700 transition-colors">
              <div className="flex items-center space-x-3">
                <span className={`p-1.5 rounded-lg text-xs font-mono font-bold flex items-center gap-1 shrink-0 ${
                  evt.actorType === 'AI'
                    ? 'bg-zinc-900 text-white border border-zinc-700'
                    : 'bg-white text-black border border-white'
                }`}>
                  {evt.actorType === 'AI' ? <Bot className="w-3.5 h-3.5"/> : <UserCheck className="w-3.5 h-3.5"/>}
                  {evt.actorType}
                </span>

                <div>
                  <div className="text-white font-bold text-xs">{evt.action}</div>
                  <div className="text-zinc-400 text-[11px]">Actor: {evt.actorId}</div>
                  {evt.reason && (
                    <div className="text-zinc-400 text-[10px] italic mt-0.5">{evt.reason}</div>
                  )}
                </div>
              </div>

              <div className="text-[10px] text-zinc-500 font-mono shrink-0">
                {new Date(evt.createdAt).toLocaleTimeString()} ({evt.id})
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
