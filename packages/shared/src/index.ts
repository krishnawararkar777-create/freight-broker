export interface HealthStatus {
  status: string;
  app: string;
  version: string;
  environment: string;
}

export type ClaimType = 'CARGO_DAMAGE' | 'SHORTAGE' | 'LOST_CARGO';
export type ClaimStatus = 'DRAFT' | 'UNDER_REVIEW' | 'APPROVED' | 'SUBMITTED';
