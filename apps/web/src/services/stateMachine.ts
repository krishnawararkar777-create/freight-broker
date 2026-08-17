import type { Claim, ClaimStatus, AuditEvent } from '../types/claim';

export const VALID_TRANSITIONS: Record<ClaimStatus, ClaimStatus[]> = {
  DRAFT: ['DOCUMENTS_PROCESSING', 'CLOSED'],
  DOCUMENTS_PROCESSING: ['NEEDS_INFORMATION', 'CLASSIFIED', 'CLOSED'],
  NEEDS_INFORMATION: ['DOCUMENTS_PROCESSING', 'CLASSIFIED', 'CLOSED'],
  CLASSIFIED: ['READY_FOR_REVIEW', 'NEEDS_INFORMATION', 'CLOSED'],
  READY_FOR_REVIEW: ['HUMAN_REVIEW', 'CLOSED'],
  HUMAN_REVIEW: ['APPROVED', 'NEEDS_INFORMATION', 'CLOSED'],
  APPROVED: ['SUBMITTED', 'HUMAN_REVIEW', 'CLOSED'],
  SUBMITTED: ['AWAITING_RESPONSE', 'FOLLOW_UP_DUE', 'CARRIER_RESPONDED', 'CLOSED'],
  AWAITING_RESPONSE: ['FOLLOW_UP_DUE', 'CARRIER_RESPONDED', 'CLOSED'],
  FOLLOW_UP_DUE: ['AWAITING_RESPONSE', 'CARRIER_RESPONDED', 'CLOSED'],
  CARRIER_RESPONDED: ['NEGOTIATION', 'APPROVED_FOR_PAYMENT', 'PARTIALLY_RECOVERED', 'RECOVERED', 'REJECTED', 'CLOSED'],
  NEGOTIATION: ['APPROVED_FOR_PAYMENT', 'PARTIALLY_RECOVERED', 'RECOVERED', 'REJECTED', 'CLOSED'],
  APPROVED_FOR_PAYMENT: ['PARTIALLY_RECOVERED', 'RECOVERED', 'CLOSED'],
  PARTIALLY_RECOVERED: ['RECOVERED', 'CLOSED', 'FOLLOW_UP_DUE'],
  RECOVERED: ['CLOSED'],
  REJECTED: ['NEGOTIATION', 'CLOSED'],
  CLOSED: ['DRAFT']
};

export interface StateTransitionResult {
  success: boolean;
  newStatus?: ClaimStatus;
  error?: string;
  auditEvent?: AuditEvent;
}

export function transitionClaimState(
  claim: Claim,
  targetStatus: ClaimStatus,
  actorType: 'AI' | 'HUMAN' | 'SYSTEM',
  actorId: string,
  reason?: string
): StateTransitionResult {
  const currentStatus = claim.status;

  // Rule 1: Check valid transition graph
  const allowedNextStates = VALID_TRANSITIONS[currentStatus] || [];
  if (!allowedNextStates.includes(targetStatus)) {
    return {
      success: false,
      error: `Invalid transition from ${currentStatus} to ${targetStatus}.`
    };
  }

  // Rule 2: CRITICAL MANDATE - Section 9 & 4 of Specification:
  // "AI cannot trigger -> SUBMITTED. This is a backend permission check, not a UI restriction."
  if (targetStatus === 'SUBMITTED') {
    if (actorType === 'AI') {
      return {
        success: false,
        error: 'CRITICAL CONTROL GUARD: Autonomous AI agent is strictly forbidden from triggering SUBMITTED state. Human review & sign-off required.'
      };
    }

    // Check human approval requirement
    if (claim.humanThresholdTriggered || claim.claimedAmount >= 5000) {
      if (!claim.isApprovedByHuman) {
        return {
          success: false,
          error: `CLAIM BLOCKED: Claim amount ($${claim.claimedAmount.toLocaleString()}) exceeds human threshold ($5,000). Elevated approval is required before submission.`
        };
      }
    } else if (!claim.isApprovedByHuman) {
      return {
        success: false,
        error: 'CLAIM BLOCKED: Claim must be explicitly reviewed and approved by a human operator before external carrier submission.'
      };
    }
  }

  // Generate audit trail
  const auditEvent: AuditEvent = {
    id: `AUD-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
    organizationId: claim.organizationId,
    claimId: claim.id,
    actorType,
    actorId,
    action: `STATUS_CHANGE: ${currentStatus} -> ${targetStatus}`,
    entityType: 'Claim',
    entityId: claim.id,
    beforeJson: { status: currentStatus, isApprovedByHuman: claim.isApprovedByHuman },
    afterJson: { status: targetStatus, isApprovedByHuman: claim.isApprovedByHuman },
    reason: reason || `Transitioned state to ${targetStatus} by ${actorType} (${actorId})`,
    createdAt: new Date().toISOString()
  };

  return {
    success: true,
    newStatus: targetStatus,
    auditEvent
  };
}
