export type UrgencyLevel = 'CRITICAL' | 'WARNING' | 'SAFE' | 'EXPIRED';

export interface DeadlineUrgencyInfo {
  level: UrgencyLevel;
  daysRemaining: number;
  formattedDeadline: string;
  label: string;
  badgeClass: string;
}

export function calculateDeadlineDaysRemaining(deadlineDateIso: string): number {
  if (!deadlineDateIso) return 0;
  const deadline = new Date(deadlineDateIso).getTime();
  const now = new Date().getTime();
  const diffTime = deadline - now;
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

export function getDeadlineUrgencyInfo(deadlineDateIso: string, isConcealed: boolean = false): DeadlineUrgencyInfo {
  const daysRemaining = calculateDeadlineDaysRemaining(deadlineDateIso);
  const dateObj = new Date(deadlineDateIso);
  const formattedDeadline = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

  if (daysRemaining < 0) {
    return {
      level: 'EXPIRED',
      daysRemaining,
      formattedDeadline,
      label: `EXPIRED (${Math.abs(daysRemaining)} days ago)`,
      badgeClass: 'bg-rose-500/20 text-rose-400 border-rose-500/40'
    };
  }

  if (isConcealed || daysRemaining <= 30) {
    return {
      level: 'CRITICAL',
      daysRemaining,
      formattedDeadline,
      label: `${daysRemaining} Days Left (URGENT)`,
      badgeClass: 'bg-rose-500/10 text-rose-400 border-rose-500/30'
    };
  }

  if (daysRemaining <= 60) {
    return {
      level: 'WARNING',
      daysRemaining,
      formattedDeadline,
      label: `${daysRemaining} Days Remaining`,
      badgeClass: 'bg-amber-500/10 text-amber-400 border-amber-500/30'
    };
  }

  return {
    level: 'SAFE',
    daysRemaining,
    formattedDeadline,
    label: `${formattedDeadline} (${daysRemaining} Days Safe)`,
    badgeClass: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
  };
}
