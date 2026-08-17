import type { CarrierRuleSet } from '../types/claim';

export interface DeadlineCalculationResult {
  carmackDeadline: string; // ISO date string (9 months)
  daysRemainingCarmack: number;
  carmackUrgency: 'CRITICAL' | 'WARNING' | 'NORMAL' | 'EXPIRED';
  
  concealedDamageDeadline?: string; // ISO date string (e.g. 5 days)
  daysRemainingConcealed?: number;
  concealedUrgency?: 'CRITICAL' | 'WARNING' | 'NORMAL' | 'EXPIRED';

  lawsuitDeadline?: string; // 2 years + 1 day post denial
  sourceRules: string;
}

export function calculateClaimDeadlines(
  deliveryDateStr: string,
  ruleSet: CarrierRuleSet,
  denialDateStr?: string
): DeadlineCalculationResult {
  const deliveryDate = new Date(deliveryDateStr);
  const now = new Date();

  // 1. Carmack Statutory Filing Window (9 months minimum under 49 U.S.C. § 14706)
  const carmackDate = new Date(deliveryDate);
  carmackDate.setMonth(carmackDate.getMonth() + ruleSet.carmackFilingWindowMonths);
  const carmackDeadlineIso = carmackDate.toISOString();
  
  const diffMsCarmack = carmackDate.getTime() - now.getTime();
  const daysRemainingCarmack = Math.ceil(diffMsCarmack / (1000 * 60 * 60 * 24));
  
  let carmackUrgency: 'CRITICAL' | 'WARNING' | 'NORMAL' | 'EXPIRED' = 'NORMAL';
  if (daysRemainingCarmack < 0) carmackUrgency = 'EXPIRED';
  else if (daysRemainingCarmack <= 14) carmackUrgency = 'CRITICAL';
  else if (daysRemainingCarmack <= 45) carmackUrgency = 'WARNING';

  // 2. Concealed Damage Tariff Window (2-5 business days)
  const concealedDate = new Date(deliveryDate);
  concealedDate.setDate(concealedDate.getDate() + ruleSet.concealedDamageNoticeDays);
  const concealedDeadlineIso = concealedDate.toISOString();
  const diffMsConcealed = concealedDate.getTime() - now.getTime();
  const daysRemainingConcealed = Math.ceil(diffMsConcealed / (1000 * 60 * 60 * 24));

  let concealedUrgency: 'CRITICAL' | 'WARNING' | 'NORMAL' | 'EXPIRED' = 'NORMAL';
  if (daysRemainingConcealed < 0) concealedUrgency = 'EXPIRED';
  else if (daysRemainingConcealed <= 2) concealedUrgency = 'CRITICAL';
  else if (daysRemainingConcealed <= 5) concealedUrgency = 'WARNING';

  // 3. Post-Denial Lawsuit Window
  let lawsuitDeadlineIso: string | undefined;
  if (denialDateStr) {
    const denialDate = new Date(denialDateStr);
    const lawsuitDate = new Date(denialDate);
    lawsuitDate.setFullYear(lawsuitDate.getFullYear() + ruleSet.postDenialLawsuitYears);
    lawsuitDate.setDate(lawsuitDate.getDate() + 1);
    lawsuitDeadlineIso = lawsuitDate.toISOString();
  }

  return {
    carmackDeadline: carmackDeadlineIso,
    daysRemainingCarmack,
    carmackUrgency,
    concealedDamageDeadline: concealedDeadlineIso,
    daysRemainingConcealed,
    concealedUrgency,
    lawsuitDeadline: lawsuitDeadlineIso,
    sourceRules: `Carmack 49 U.S.C. § 14706 (${ruleSet.carmackFilingWindowMonths}mo) & Tariff RuleSet v${ruleSet.version} (${ruleSet.concealedDamageNoticeDays}d concealed)`
  };
}
