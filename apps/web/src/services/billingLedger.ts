import type { RecoveryEvent, FeeEvent, Claim } from '../types/claim';

export interface RecordRecoveryResult {
  recoveryEvent: RecoveryEvent;
  feeEvent: FeeEvent;
  updatedClaim: Partial<Claim>;
}

export function recordRecoveryEvent(
  claim: Claim,
  amount: number,
  contingencyRate: number,
  paymentReference: string,
  payer: string,
  evidenceDocumentId?: string
): RecordRecoveryResult {
  const recoveryEventId = `REC-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
  const feeEventId = `FEE-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
  const nowStr = new Date().toISOString();

  const feeAmount = Math.round((amount * contingencyRate) * 100) / 100;

  const recoveryEvent: RecoveryEvent = {
    id: recoveryEventId,
    claimId: claim.id,
    amount,
    currency: claim.currency || 'USD',
    receivedAt: nowStr,
    paymentReference,
    payer,
    evidenceDocumentId,
    status: 'CONFIRMED',
    createdAt: nowStr
  };

  const feeEvent: FeeEvent = {
    id: feeEventId,
    claimId: claim.id,
    recoveryEventId,
    eligibleAmount: amount,
    contingencyRate,
    feeAmount,
    currency: claim.currency || 'USD',
    status: 'CALCULATED',
    createdAt: nowStr
  };

  const newTotalRecovered = (claim.recoveredAmount || 0) + amount;
  let newStatus = claim.status;

  if (newTotalRecovered >= claim.claimedAmount) {
    newStatus = 'RECOVERED';
  } else if (newTotalRecovered > 0) {
    newStatus = 'PARTIALLY_RECOVERED';
  }

  return {
    recoveryEvent,
    feeEvent,
    updatedClaim: {
      recoveredAmount: newTotalRecovered,
      status: newStatus,
      updatedAt: nowStr
    }
  };
}
