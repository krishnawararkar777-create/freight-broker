export type OrganizationType = 'broker' | '3pl' | 'shipper' | 'other';

export interface Organization {
  id: string;
  name: string;
  type: OrganizationType;
  contingencyRate: number; // e.g. 0.20 for 20%
  highValueThreshold: number; // e.g. 5000 ($5,000)
  currency: string;
  timezone: string;
}

export interface User {
  id: string;
  organizationId: string;
  name: string;
  email: string;
  role: 'Admin' | 'Claims Manager' | 'Claims Operator' | 'Senior Approver' | 'Finance' | 'Read-only';
}

export interface Shipment {
  id: string;
  organizationId: string;
  externalReference: string;
  bolNumber: string;
  proNumber: string;
  carrierId: string;
  carrierName: string;
  shipperName: string;
  consigneeName: string;
  origin: string;
  destination: string;
  pickupDate: string; // ISO format
  deliveryDate: string; // ISO format
  declaredValue: number;
  currency: string;
  commodity: string;
  quantity: number;
  weightLbs: number;
}

export type DocumentType = 
  | 'BOL' 
  | 'POD' 
  | 'COMMERCIAL_INVOICE' 
  | 'DAMAGE_PHOTO' 
  | 'INSPECTION_REPORT' 
  | 'CARRIER_CORRESPONDENCE'
  | 'RATE_CONFIRMATION';

export interface BoundingBox {
  x: number; // percentage 0-100
  y: number; // percentage 0-100
  width: number;
  height: number;
}

export interface DocumentEvidence {
  id: string;
  documentId: string;
  pageNumber: number;
  sourceText: string;
  fieldName: string;
  confidence: number;
  bbox?: BoundingBox;
}

export interface ClaimDocument {
  id: string;
  organizationId: string;
  claimId: string;
  shipmentId: string;
  documentType: DocumentType;
  filename: string;
  mimeType: string;
  storageUrl: string;
  sha256: string;
  pageCount: number;
  extractionStatus: 'PENDING' | 'EXTRACTED' | 'FAILED' | 'NEEDS_VERIFICATION';
  uploadedAt: string;
  evidences: DocumentEvidence[];
}

export interface ClaimFact {
  id: string;
  claimId: string;
  fieldName: string;
  displayName: string;
  valueJson: any;
  sourceDocumentId?: string;
  sourceDocumentName?: string;
  pageNumber?: number;
  sourceText?: string;
  confidence: number;
  verificationStatus: 'VERIFIED' | 'PROBABLE' | 'UNVERIFIED' | 'EDITED_BY_HUMAN';
  originalValueJson?: any;
  editedByUserId?: string;
  editedAt?: string;
  editReason?: string;
}

export type ClaimType = 'DAMAGE' | 'SHORTAGE' | 'LOSS' | 'THEFT' | 'DEMURRAGE_DETENTION';

export type ClaimStatus =
  | 'DRAFT'
  | 'DOCUMENTS_PROCESSING'
  | 'NEEDS_INFORMATION'
  | 'CLASSIFIED'
  | 'READY_FOR_REVIEW'
  | 'HUMAN_REVIEW'
  | 'APPROVED'
  | 'SUBMITTED'
  | 'AWAITING_RESPONSE'
  | 'FOLLOW_UP_DUE'
  | 'CARRIER_RESPONDED'
  | 'NEGOTIATION'
  | 'APPROVED_FOR_PAYMENT'
  | 'PARTIALLY_RECOVERED'
  | 'RECOVERED'
  | 'REJECTED'
  | 'CLOSED';

export interface CarrierRuleSet {
  id: string;
  carrierId: string;
  carrierName: string;
  version: string;
  effectiveFrom: string;
  effectiveTo?: string;
  carmackFilingWindowMonths: number; // default 9
  concealedDamageNoticeDays: number; // default 5 (or 2-5 business days)
  postDenialLawsuitYears: number; // 2 years + 1 day
  requiredDocuments: DocumentType[];
  submissionChannel: 'EMAIL' | 'PORTAL' | 'EDI' | 'MAIL';
  submissionTarget: string; // e.g. claims@abctrucking.com
  sourceCitation: string;
  lastVerifiedAt: string;
  verifiedBy: string;
}

export interface ClaimRequirementCheck {
  id: string;
  requirementType: string;
  description: string;
  status: 'MET' | 'MISSING' | 'UNKNOWN' | 'WAIVED';
  evidenceDocumentId?: string;
}

export interface Contradiction {
  id: string;
  field1: string;
  field2: string;
  description: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  resolved: boolean;
}

export interface ClaimPackageDraft {
  id: string;
  claimId: string;
  narrativeText: string; // ground citations included like [POD p.1]
  coverSummary: string;
  chronologyText: string;
  amountClaimedCalculated: number;
  amountCalculationBreakdown: string;
  evidenceChecklistText: string;
  generatedAt: string;
  modelName: string;
  modelVersion: string;
}

export interface Claim {
  id: string;
  organizationId: string;
  shipmentId: string;
  claimNumber: string; // e.g. CLM-847293
  claimType: ClaimType;
  status: ClaimStatus;
  claimedAmount: number;
  currency: string;
  approvedClaimAmount?: number;
  recoveredAmount: number;
  deadlineAt: string; // Statutory Carmack deadline
  concealedDeadlineAt?: string;
  lawsuitDeadlineAt?: string; // 2 years + 1 day post denial
  humanThresholdTriggered: boolean; // if > threshold ($5,000)
  approvalLevelRequired: 0 | 1 | 2 | 3;
  isApprovedByHuman: boolean;
  approvedByUserId?: string;
  approvedAt?: string;
  submittedAt?: string;
  submissionReference?: string;
  ownerUserId: string;
  createdAt: string;
  updatedAt: string;
  
  // Derived / Populated
  shipment?: Shipment;
  documents?: ClaimDocument[];
  facts?: ClaimFact[];
  requirements?: ClaimRequirementCheck[];
  contradictions?: Contradiction[];
  packageDraft?: ClaimPackageDraft;
  readinessScore?: number;
  readinessExplanations?: string[];
  carrierRuleSet?: CarrierRuleSet;
}

export interface RecoveryEvent {
  id: string;
  claimId: string;
  amount: number;
  currency: string;
  receivedAt: string;
  paymentReference: string;
  payer: string;
  evidenceDocumentId?: string;
  status: 'PENDING_CLEARANCE' | 'CONFIRMED' | 'DISPUTED';
  createdAt: string;
}

export interface FeeEvent {
  id: string;
  claimId: string;
  recoveryEventId: string;
  eligibleAmount: number;
  contingencyRate: number;
  feeAmount: number;
  currency: string;
  status: 'CALCULATED' | 'INVOICED' | 'PAID';
  invoiceId?: string;
  createdAt: string;
}

export interface AuditEvent {
  id: string;
  organizationId: string;
  claimId?: string;
  actorType: 'AI' | 'HUMAN' | 'SYSTEM';
  actorId: string; // user id or model name
  action: string;
  entityType: string;
  entityId: string;
  beforeJson?: any;
  afterJson?: any;
  reason?: string;
  createdAt: string;
}
