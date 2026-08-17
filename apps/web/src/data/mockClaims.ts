import type { Claim, Organization, User, CarrierRuleSet, RecoveryEvent, FeeEvent, AuditEvent } from '../types/claim';

export const mockOrg: Organization = {
  id: 'org-1',
  name: 'Apex Freight Brokers (3PL)',
  type: 'broker',
  contingencyRate: 0.20,
  highValueThreshold: 5000,
  currency: 'USD',
  timezone: 'America/Chicago'
};

export const mockUsers: User[] = [
  { id: 'usr-1', organizationId: 'org-1', name: 'Sarah Jenkins', email: 'sarah@apexfreight.com', role: 'Claims Manager' },
  { id: 'usr-2', organizationId: 'org-1', name: 'David Miller', email: 'david@apexfreight.com', role: 'Senior Approver' },
  { id: 'usr-3', organizationId: 'org-1', name: 'Alex Rivera', email: 'alex@apexfreight.com', role: 'Claims Operator' }
];

export const mockCarrierRuleSets: Record<string, CarrierRuleSet> = {
  'ABC Trucking': {
    id: 'crs-1',
    carrierId: 'car-abc',
    carrierName: 'ABC Trucking',
    version: '2026.1',
    effectiveFrom: '2026-01-01',
    carmackFilingWindowMonths: 9,
    concealedDamageNoticeDays: 5,
    postDenialLawsuitYears: 2,
    requiredDocuments: ['BOL', 'POD', 'COMMERCIAL_INVOICE', 'DAMAGE_PHOTO'],
    submissionChannel: 'EMAIL',
    submissionTarget: 'claims@abctrucking.com',
    sourceCitation: 'ABC Freight Tariff 100-A Item 450 (Verified 2026-02-10)',
    lastVerifiedAt: '2026-02-10',
    verifiedBy: 'Legal Compliance Ops'
  },
  'Swift Line Logistics': {
    id: 'crs-2',
    carrierId: 'car-swift',
    carrierName: 'Swift Line Logistics',
    version: '2025.4',
    effectiveFrom: '2025-10-01',
    carmackFilingWindowMonths: 9,
    concealedDamageNoticeDays: 3,
    postDenialLawsuitYears: 2,
    requiredDocuments: ['BOL', 'POD', 'COMMERCIAL_INVOICE'],
    submissionChannel: 'EMAIL',
    submissionTarget: 'cargo-claims@swiftline.com',
    sourceCitation: 'DEMO DATA — UNVERIFIED',
    lastVerifiedAt: '2025-11-15',
    verifiedBy: 'Unverified Demo Source'
  },
  'Midwest Freight Co.': {
    id: 'crs-3',
    carrierId: 'car-midwest',
    carrierName: 'Midwest Freight Co.',
    version: '2026.2',
    effectiveFrom: '2026-01-15',
    carmackFilingWindowMonths: 9,
    concealedDamageNoticeDays: 5,
    postDenialLawsuitYears: 2,
    requiredDocuments: ['BOL', 'POD', 'COMMERCIAL_INVOICE', 'INSPECTION_REPORT'],
    submissionChannel: 'PORTAL',
    submissionTarget: 'https://claims.midwestfreight.com/submit',
    sourceCitation: 'Midwest Carrier Agreement 2026',
    lastVerifiedAt: '2026-01-20',
    verifiedBy: 'Legal Compliance Ops'
  }
};

export const mockClaims: Claim[] = [
  {
    id: 'clm-847293',
    organizationId: 'org-1',
    shipmentId: 'shp-847293',
    claimNumber: 'CLM-847293',
    claimType: 'DAMAGE',
    status: 'HUMAN_REVIEW',
    claimedAmount: 8000,
    currency: 'USD',
    recoveredAmount: 0,
    deadlineAt: '2026-09-15T00:00:00Z',
    concealedDeadlineAt: '2026-08-08T00:00:00Z',
    humanThresholdTriggered: true,
    approvalLevelRequired: 2,
    isApprovedByHuman: false,
    ownerUserId: 'usr-1',
    createdAt: '2026-08-04T10:15:00Z',
    updatedAt: '2026-08-14T11:00:00Z',
    readinessScore: 92,
    readinessExplanations: [
      '✓ Bill of Lading (BOL #BOL-847293) verified',
      '✓ Proof of Delivery (POD) found with notation "3 cartons damaged"',
      '✓ Commercial Invoice #INV-90210 ($20,000 total) verified',
      '✓ Damage calculation: 40% affected quantity = $8,000',
      '✓ Photographic proof of pallet impact attached',
      '✓ Deadline safe: 32 days remaining before Carmack limit'
    ],
    carrierRuleSet: mockCarrierRuleSets['ABC Trucking'],
    shipment: {
      id: 'shp-847293',
      organizationId: 'org-1',
      externalReference: 'REF-847293',
      bolNumber: 'BOL-847293',
      proNumber: 'PRO-847293',
      carrierId: 'car-abc',
      carrierName: 'ABC Trucking',
      shipperName: 'TechComponents Corp',
      consigneeName: 'Metro Logistics Distribution',
      origin: 'Chicago, IL',
      destination: 'Dallas, TX',
      pickupDate: '2025-12-10',
      deliveryDate: '2025-12-15',
      declaredValue: 20000,
      currency: 'USD',
      commodity: 'High-Precision Microcontrollers',
      quantity: 10,
      weightLbs: 4500
    },
    documents: [
      {
        id: 'doc-bol-1',
        organizationId: 'org-1',
        claimId: 'clm-847293',
        shipmentId: 'shp-847293',
        documentType: 'BOL',
        filename: 'Bill_of_Lading_847293.pdf',
        mimeType: 'application/pdf',
        storageUrl: 'https://storage.algolyra.com/docs/bol-847293.pdf',
        sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        pageCount: 1,
        extractionStatus: 'EXTRACTED',
        uploadedAt: '2026-08-04T10:16:00Z',
        evidences: [
          { id: 'ev-1', documentId: 'doc-bol-1', pageNumber: 1, fieldName: 'bolNumber', sourceText: 'BOL NUMBER: BOL-847293', confidence: 0.98, bbox: { x: 65, y: 12, width: 25, height: 4 } },
          { id: 'ev-2', documentId: 'doc-bol-1', pageNumber: 1, fieldName: 'proNumber', sourceText: 'PRO NUMBER: PRO-847293', confidence: 0.98, bbox: { x: 65, y: 18, width: 25, height: 4 } },
          { id: 'ev-3', documentId: 'doc-bol-1', pageNumber: 1, fieldName: 'poNumber', sourceText: 'PO / REFERENCE: PO-55210', confidence: 0.96, bbox: { x: 30, y: 12, width: 25, height: 4 } },
          { id: 'ev-4', documentId: 'doc-bol-1', pageNumber: 1, fieldName: 'pickupDate', sourceText: 'PICKUP DATE: 2026-08-10', confidence: 0.97, bbox: { x: 50, y: 12, width: 20, height: 4 } },
          { id: 'ev-5', documentId: 'doc-bol-1', pageNumber: 1, fieldName: 'shipperName', sourceText: 'SHIPPER: Meridian Electronics Distributors (Los Angeles, CA)', confidence: 0.97, bbox: { x: 10, y: 24, width: 40, height: 4 } },
          { id: 'ev-6', documentId: 'doc-bol-1', pageNumber: 1, fieldName: 'consigneeName', sourceText: 'CONSIGNEE: Riverside Retail Store #14 (Chicago, IL)', confidence: 0.96, bbox: { x: 45, y: 24, width: 40, height: 4 } },
          { id: 'ev-7', documentId: 'doc-bol-1', pageNumber: 1, fieldName: 'declaredValue', sourceText: 'DECLARED VALUE: $8000', confidence: 0.98, bbox: { x: 65, y: 30, width: 20, height: 4 } }
        ]
      },
      {
        id: 'doc-pod-1',
        organizationId: 'org-1',
        claimId: 'clm-847293',
        shipmentId: 'shp-847293',
        documentType: 'POD',
        filename: 'Proof_of_Delivery_847293.pdf',
        mimeType: 'application/pdf',
        storageUrl: 'https://storage.algolyra.com/docs/pod-847293.pdf',
        sha256: 'a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e',
        pageCount: 1,
        extractionStatus: 'EXTRACTED',
        uploadedAt: '2026-08-04T10:16:30Z',
        evidences: [
          { id: 'ev-pod-1', documentId: 'doc-pod-1', pageNumber: 1, fieldName: 'podReference', sourceText: 'REFERENCE: POD-2026-0817-001', confidence: 0.98, bbox: { x: 10, y: 15, width: 40, height: 4 } },
          { id: 'ev-pod-2', documentId: 'doc-pod-1', pageNumber: 1, fieldName: 'deliveryDate', sourceText: 'DELIVERY DATE: AUGUST 17, 2026', confidence: 0.99, bbox: { x: 60, y: 15, width: 35, height: 4 } },
          { id: 'ev-pod-3', documentId: 'doc-pod-1', pageNumber: 1, fieldName: 'deliveredItemsManifest', sourceText: '3x Office Chair ($360), 2x Standing Desk ($500), 1x Monitor ($180)', confidence: 0.96, bbox: { x: 10, y: 35, width: 80, height: 10 } },
          { id: 'ev-pod-4', documentId: 'doc-pod-1', pageNumber: 1, fieldName: 'totalDeliveredValue', sourceText: 'TOTAL DELIVERED VALUE: $1,040.00', confidence: 0.99, bbox: { x: 60, y: 55, width: 30, height: 5 } },
          { id: 'ev-pod-5', documentId: 'doc-pod-1', pageNumber: 1, fieldName: 'driverSignature', sourceText: 'Signed: Received in Good Order / Delivery Completed Aug 17, 2026', confidence: 0.94, bbox: { x: 10, y: 80, width: 80, height: 8 } }
        ]
      },
      {
        id: 'doc-inv-1',
        organizationId: 'org-1',
        claimId: 'clm-847293',
        shipmentId: 'shp-847293',
        documentType: 'COMMERCIAL_INVOICE',
        filename: 'Invoice_INV-90210.pdf',
        mimeType: 'application/pdf',
        storageUrl: 'https://storage.algolyra.com/docs/inv-90210.pdf',
        sha256: '8f4e5a91b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9',
        pageCount: 1,
        extractionStatus: 'EXTRACTED',
        uploadedAt: '2026-08-04T10:17:00Z',
        evidences: [
          { id: 'ev-7', documentId: 'doc-inv-1', pageNumber: 1, fieldName: 'invoiceTotal', sourceText: 'TOTAL AMOUNT: $20,000.00 USD', confidence: 0.99, bbox: { x: 65, y: 85, width: 25, height: 5 } },
          { id: 'ev-8', documentId: 'doc-inv-1', pageNumber: 1, fieldName: 'damagedItemsValuation', sourceText: '3 Pallets x $2,666.67 = $8,000.00 damaged value', confidence: 0.95, bbox: { x: 15, y: 50, width: 70, height: 6 } }
        ]
      },
      {
        id: 'doc-img-1',
        organizationId: 'org-1',
        claimId: 'clm-847293',
        shipmentId: 'shp-847293',
        documentType: 'DAMAGE_PHOTO',
        filename: 'Pallet_Damage_Photo1.jpg',
        mimeType: 'image/jpeg',
        storageUrl: 'https://storage.algolyra.com/docs/damage-847293.jpg',
        sha256: '11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff',
        pageCount: 1,
        extractionStatus: 'EXTRACTED',
        uploadedAt: '2026-08-04T10:17:30Z',
        evidences: [
          { id: 'ev-9', documentId: 'doc-img-1', pageNumber: 1, fieldName: 'visualDamageModel', sourceText: 'AI Vision Observation: Crushed outer corrugated packaging, visible impact compression on corner edge. Confidence: 0.88', confidence: 0.88, bbox: { x: 20, y: 20, width: 60, height: 60 } }
        ]
      }
    ],
    facts: [
      { id: 'f1', claimId: 'clm-847293', fieldName: 'proNumber', displayName: 'PRO Number', valueJson: 'PRO-847293', sourceDocumentId: 'doc-bol-1', sourceDocumentName: 'Bill_of_Lading_847293.pdf', pageNumber: 1, sourceText: 'PRO #: PRO-847293', confidence: 0.98, verificationStatus: 'VERIFIED' },
      { id: 'f2', claimId: 'clm-847293', fieldName: 'carrierName', displayName: 'Carrier Name', valueJson: 'ABC Trucking', sourceDocumentId: 'doc-bol-1', sourceDocumentName: 'Bill_of_Lading_847293.pdf', pageNumber: 1, sourceText: 'Carrier: ABC Trucking Inc', confidence: 0.96, verificationStatus: 'VERIFIED' },
      { id: 'f3', claimId: 'clm-847293', fieldName: 'deliveryDate', displayName: 'Delivery Date', valueJson: '2025-12-15', sourceDocumentId: 'doc-pod-1', sourceDocumentName: 'Proof_of_Delivery_847293.pdf', pageNumber: 1, sourceText: 'Delivered: 12/15/2025 14:30', confidence: 0.99, verificationStatus: 'VERIFIED' },
      { id: 'f4', claimId: 'clm-847293', fieldName: 'damageNotation', displayName: 'POD Exception Notation', valueJson: '3 cartons crushed & damaged at rear doors', sourceDocumentId: 'doc-pod-1', sourceDocumentName: 'Proof_of_Delivery_847293.pdf', pageNumber: 1, sourceText: 'SUBJECT TO INSPECTION - 3 cartons crushed & damaged', confidence: 0.94, verificationStatus: 'VERIFIED' },
      { id: 'f5', claimId: 'clm-847293', fieldName: 'invoiceTotal', displayName: 'Total Shipment Value', valueJson: 20000, sourceDocumentId: 'doc-inv-1', sourceDocumentName: 'Invoice_INV-90210.pdf', pageNumber: 1, sourceText: 'TOTAL AMOUNT: $20,000.00 USD', confidence: 0.99, verificationStatus: 'VERIFIED' },
      { id: 'f6', claimId: 'clm-847293', fieldName: 'claimedAmount', displayName: 'Claimed Amount', valueJson: 8000, sourceDocumentId: 'doc-inv-1', sourceDocumentName: 'Invoice_INV-90210.pdf', pageNumber: 1, sourceText: '3 Pallets x $2,666.67 = $8,000.00 damaged value', confidence: 0.95, verificationStatus: 'VERIFIED' }
    ],
    requirements: [
      { id: 'r1', requirementType: 'Mandatory Document', description: 'Bill of Lading (BOL)', status: 'MET', evidenceDocumentId: 'doc-bol-1' },
      { id: 'r2', requirementType: 'Mandatory Document', description: 'Proof of Delivery (POD) with Exception', status: 'MET', evidenceDocumentId: 'doc-pod-1' },
      { id: 'r3', requirementType: 'Proof of Value', description: 'Commercial Invoice', status: 'MET', evidenceDocumentId: 'doc-inv-1' },
      { id: 'r4', requirementType: 'Damage Proof', description: 'Photographic Damage Evidence', status: 'MET', evidenceDocumentId: 'doc-img-1' }
    ],
    contradictions: [],
    packageDraft: {
      id: 'pkg-847293',
      claimId: 'clm-847293',
      coverSummary: 'FORMAL CARGO CLAIM DEMAND — CLAIM #CLM-847293 (CARRIER: ABC TRUCKING)',
      narrativeText: `To Claims Department, ABC Trucking:\n\nPlease accept this formal written claim under 49 U.S.C. § 14706 (Carmack Amendment) for physical cargo damage occurring during transit on Shipment #847293.\n\nCHRONOLOGY & FACTUAL GROUNDING:\n1. On 12/10/2025, shipper TechComponents Corp tendered 10 pallets of High-Precision Microcontrollers (Declared Value: $20,000) to ABC Trucking under Bill of Lading #BOL-847293 [BOL p.1].\n2. On 12/15/2025, carrier delivered shipment #847293 to Metro Logistics Distribution [POD p.1].\n3. Consignee received shipment with explicit delivery exception noted on POD: "3 cartons crushed & damaged at rear doors" [POD p.1].\n4. Physical inspection and high-resolution photography confirm crushed outer corrugated packaging and structural impact damage to 3 pallets [Photo Evidence p.1].\n5. Commercial Invoice #INV-90210 establishes full shipment cost at $20,000.00 ($2,000/pallet). The direct financial loss for 3 destroyed pallets totals exactly $8,000.00 [Invoice p.1].\n\nDEMAND FOR SETTLEMENT:\nWe hereby demand full payment of $8,000.00 within 30 days of receipt of this package. Supporting documentation (BOL, signed POD, commercial invoice, damage photo index) is attached.`,
      chronologyText: '12/10/2025: Pickup | 12/15/2025: Delivery with POD exception | 08/04/2026: Evidence extraction & draft generated',
      amountClaimedCalculated: 8000,
      amountCalculationBreakdown: '$20,000 total invoice value x 40% damaged goods (3 pallets) = $8,000.00',
      evidenceChecklistText: '✓ BOL #BOL-847293\n✓ Signed POD with damage notation\n✓ Invoice #INV-90210\n✓ High-res damage photos',
      generatedAt: '2026-08-04T10:20:00Z',
      modelName: 'Algolyra-Drafting-v4',
      modelVersion: '4.2.1-grounded'
    }
  },

  {
    id: 'clm-910248',
    organizationId: 'org-1',
    shipmentId: 'shp-910248',
    claimNumber: 'CLM-910248',
    claimType: 'SHORTAGE',
    status: 'NEEDS_INFORMATION',
    claimedAmount: 4250,
    currency: 'USD',
    recoveredAmount: 0,
    deadlineAt: '2026-10-12T00:00:00Z',
    humanThresholdTriggered: false,
    approvalLevelRequired: 1,
    isApprovedByHuman: false,
    ownerUserId: 'usr-3',
    createdAt: '2026-08-01T09:00:00Z',
    updatedAt: '2026-08-10T14:20:00Z',
    readinessScore: 68,
    readinessExplanations: [
      '✓ Bill of Lading (BOL #BOL-910248) verified',
      '✓ Commercial Invoice #INV-55102 verified',
      '✗ Proof of Delivery (POD) uploaded, BUT missing explicit shortage notation from receiving clerk',
      '⚠️ AI Action: Requesting signed delivery receipt with shortage verification from consignee'
    ],
    carrierRuleSet: mockCarrierRuleSets['Swift Line Logistics'],
    shipment: {
      id: 'shp-910248',
      organizationId: 'org-1',
      externalReference: 'REF-910248',
      bolNumber: 'BOL-910248',
      proNumber: 'PRO-910248',
      carrierId: 'car-swift',
      carrierName: 'Swift Line Logistics',
      shipperName: 'Industrial Metals LLC',
      consigneeName: 'Midwest Fabricators Inc',
      origin: 'Cleveland, OH',
      destination: 'St. Louis, MO',
      pickupDate: '2026-01-10',
      deliveryDate: '2026-01-14',
      declaredValue: 12500,
      currency: 'USD',
      commodity: 'Aluminum Extrusions',
      quantity: 50,
      weightLbs: 12000
    },
    documents: [
      {
        id: 'doc-bol-2',
        organizationId: 'org-1',
        claimId: 'clm-910248',
        shipmentId: 'shp-910248',
        documentType: 'BOL',
        filename: 'BOL_910248.pdf',
        mimeType: 'application/pdf',
        storageUrl: 'https://storage.algolyra.com/docs/bol-910248.pdf',
        sha256: '910248hash123',
        pageCount: 1,
        extractionStatus: 'EXTRACTED',
        uploadedAt: '2026-08-01T09:05:00Z',
        evidences: [
          { id: 'ev-20', documentId: 'doc-bol-2', pageNumber: 1, fieldName: 'proNumber', sourceText: 'PRO: 910248', confidence: 0.99 }
        ]
      }
    ],
    facts: [
      { id: 'f20', claimId: 'clm-910248', fieldName: 'proNumber', displayName: 'PRO Number', valueJson: 'PRO-910248', sourceDocumentId: 'doc-bol-2', confidence: 0.99, verificationStatus: 'VERIFIED' }
    ]
  },

  {
    id: 'clm-773192',
    organizationId: 'org-1',
    shipmentId: 'shp-773192',
    claimNumber: 'CLM-773192',
    claimType: 'DAMAGE',
    status: 'PARTIALLY_RECOVERED',
    claimedAmount: 12400,
    currency: 'USD',
    recoveredAmount: 6000,
    deadlineAt: '2026-07-20T00:00:00Z',
    lawsuitDeadlineAt: '2028-04-15T00:00:00Z',
    humanThresholdTriggered: true,
    approvalLevelRequired: 2,
    isApprovedByHuman: true,
    approvedByUserId: 'usr-2',
    approvedAt: '2026-03-01T11:00:00Z',
    submittedAt: '2026-03-02T09:30:00Z',
    ownerUserId: 'usr-1',
    createdAt: '2026-02-15T08:00:00Z',
    updatedAt: '2026-04-14T16:00:00Z',
    readinessScore: 100,
    readinessExplanations: [
      '✓ Claim successfully submitted & settled with Midwest Freight Co.',
      '✓ Original Claim: $12,400 | Partial Settlement Recovered: $6,000.00',
      '✓ Algolyra Fee Event: $1,200.00 (20% contingency fee on recovered dollars)',
      '✓ Active Lawsuit Window: 2 years + 1 day remaining until April 15, 2028 for disputed balance ($6,400)'
    ],
    carrierRuleSet: mockCarrierRuleSets['Midwest Freight Co.'],
    shipment: {
      id: 'shp-773192',
      organizationId: 'org-1',
      externalReference: 'REF-773192',
      bolNumber: 'BOL-773192',
      proNumber: 'PRO-773192',
      carrierId: 'car-midwest',
      carrierName: 'Midwest Freight Co.',
      shipperName: 'Global Machinery Parts',
      consigneeName: 'Automotive Assemblies Midwest',
      origin: 'Detroit, MI',
      destination: 'Indianapolis, IN',
      pickupDate: '2025-10-10',
      deliveryDate: '2025-10-12',
      declaredValue: 25000,
      currency: 'USD',
      commodity: 'Hydraulic Cylinder Valves',
      quantity: 12,
      weightLbs: 8200
    }
  }
];

export const mockRecoveryEvents: RecoveryEvent[] = [
  {
    id: 'rec-101',
    claimId: 'clm-773192',
    amount: 6000,
    currency: 'USD',
    receivedAt: '2026-04-14T14:30:00Z',
    paymentReference: 'CHK-908124-MIDWEST',
    payer: 'Midwest Freight Co. Claims Department',
    status: 'CONFIRMED',
    createdAt: '2026-04-14T14:35:00Z'
  }
];

export const mockFeeEvents: FeeEvent[] = [
  {
    id: 'fee-101',
    claimId: 'clm-773192',
    recoveryEventId: 'rec-101',
    eligibleAmount: 6000,
    contingencyRate: 0.20,
    feeAmount: 1200,
    currency: 'USD',
    status: 'INVOICED',
    invoiceId: 'INV-ALG-2026-004',
    createdAt: '2026-04-14T14:36:00Z'
  }
];

export const mockAuditEvents: AuditEvent[] = [
  {
    id: 'aud-1',
    organizationId: 'org-1',
    claimId: 'clm-847293',
    actorType: 'AI',
    actorId: 'Algolyra-Extraction-Worker-v4',
    action: 'DOCUMENT_EXTRACTION_COMPLETED',
    entityType: 'Document',
    entityId: 'doc-pod-1',
    afterJson: { confidence: 0.96, extractedFieldsCount: 3 },
    createdAt: '2026-08-04T10:16:35Z'
  },
  {
    id: 'aud-2',
    organizationId: 'org-1',
    claimId: 'clm-847293',
    actorType: 'AI',
    actorId: 'Algolyra-Readiness-Engine',
    action: 'READINESS_SCORE_CALCULATED',
    entityType: 'Claim',
    entityId: 'clm-847293',
    afterJson: { score: 92, status: 'READY_FOR_REVIEW' },
    createdAt: '2026-08-04T10:18:00Z'
  },
  {
    id: 'aud-3',
    organizationId: 'org-1',
    claimId: 'clm-847293',
    actorType: 'AI',
    actorId: 'Algolyra-State-Machine-Guard',
    action: 'STATE_GUARD_CHECK',
    entityType: 'Claim',
    entityId: 'clm-847293',
    reason: 'Submission lock enforced: Human approval required for claim amount $8,000 > threshold $5,000',
    createdAt: '2026-08-04T10:18:01Z'
  }
];
