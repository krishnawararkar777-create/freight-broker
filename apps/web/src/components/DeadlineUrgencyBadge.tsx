import React from 'react';
import { Clock, AlertTriangle, ShieldCheck, AlertCircle } from 'lucide-react';
import { getDeadlineUrgencyInfo } from '../lib/deadline-urgency';

interface DeadlineUrgencyBadgeProps {
  deadlineDateIso: string;
  isConcealed?: boolean;
  className?: string;
}

export const DeadlineUrgencyBadge: React.FC<DeadlineUrgencyBadgeProps> = ({
  deadlineDateIso,
  isConcealed = false,
  className = ''
}) => {
  const info = getDeadlineUrgencyInfo(deadlineDateIso, isConcealed);

  const getIcon = () => {
    switch (info.level) {
      case 'EXPIRED':
        return <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />;
      case 'CRITICAL':
        return <AlertTriangle className="w-3.5 h-3.5 text-rose-400 shrink-0 animate-pulse" />;
      case 'WARNING':
        return <Clock className="w-3.5 h-3.5 text-amber-400 shrink-0" />;
      case 'SAFE':
        return <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />;
    }
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold font-mono border ${info.badgeClass} ${className}`}>
      {getIcon()}
      {info.label}
    </span>
  );
};
