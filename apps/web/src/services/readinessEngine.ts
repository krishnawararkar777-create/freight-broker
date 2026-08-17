import type { Claim, ClaimDocument, Contradiction, ClaimRequirementCheck } from '../types/claim';

export interface ReadinessEvaluationResult {
  score: number; // 0 - 100
  status: 'READY' | 'BLOCKED' | 'ESCALATED';
  explanations: { met: string[]; missing: string[]; warnings: string[] };
  requirements: ClaimRequirementCheck[];
  contradictions: Contradiction[];
}

export function evaluateClaimReadiness(claim: Partial<Claim>): ReadinessEvaluationResult {
  const documents: ClaimDocument[] = claim.documents || [];
  const met: string[] = [];
  const missing: string[] = [];
  const warnings: string[] = [];
  const requirements: ClaimRequirementCheck[] = [];
  const contradictions: Contradiction[] = [];

  let totalPoints = 0;
  let earnedPoints = 0;

  // Check 1: Bill of Lading (BOL)
  totalPoints += 20;
  const bolDoc = documents.find(d => d.documentType === 'BOL');
  if (bolDoc) {
    earnedPoints += 20;
    met.push('Bill of Lading (BOL) verified & linked');
    requirements.push({
      id: 'req-bol',
      requirementType: 'Mandatory Document',
      description: 'Proof of tender & original shipment terms (BOL)',
      status: 'MET',
      evidenceDocumentId: bolDoc.id
    });
  } else {
    missing.push('Bill of Lading (BOL) missing');
    requirements.push({
      id: 'req-bol',
      requirementType: 'Mandatory Document',
      description: 'Proof of tender & original shipment terms (BOL)',
      status: 'MISSING'
    });
  }

  // Check 2: Proof of Delivery (POD)
  totalPoints += 25;
  const podDoc = documents.find(d => d.documentType === 'POD');
  if (podDoc) {
    const hasNotationEvidence = podDoc.evidences.some(
      e => e.fieldName.toLowerCase().includes('damage') || e.sourceText.toLowerCase().includes('damage') || e.sourceText.toLowerCase().includes('short')
    );
    if (hasNotationEvidence) {
      earnedPoints += 25;
      met.push('POD found with explicit delivery exception/damage notation');
      requirements.push({
        id: 'req-pod',
        requirementType: 'Mandatory Document',
        description: 'Proof of Delivery (POD) with exception notation',
        status: 'MET',
        evidenceDocumentId: podDoc.id
      });
    } else {
      earnedPoints += 10;
      warnings.push('POD uploaded, but missing explicit damage/shortage exception notation');
      requirements.push({
        id: 'req-pod',
        requirementType: 'Mandatory Document',
        description: 'Proof of Delivery (POD) with exception notation',
        status: 'UNKNOWN',
        evidenceDocumentId: podDoc.id
      });
    }
  } else {
    missing.push('Proof of Delivery (POD) missing');
    requirements.push({
      id: 'req-pod',
      requirementType: 'Mandatory Document',
      description: 'Proof of Delivery (POD) with exception notation',
      status: 'MISSING'
    });
  }

  // Check 3: Commercial Invoice
  totalPoints += 25;
  const invoiceDoc = documents.find(d => d.documentType === 'COMMERCIAL_INVOICE');
  if (invoiceDoc) {
    earnedPoints += 25;
    met.push('Commercial Invoice / Proof of Value verified');
    requirements.push({
      id: 'req-inv',
      requirementType: 'Proof of Value',
      description: 'Vendor/Commercial Invoice supporting claim amount',
      status: 'MET',
      evidenceDocumentId: invoiceDoc.id
    });
  } else {
    missing.push('Commercial Invoice / Proof of Value missing');
    requirements.push({
      id: 'req-inv',
      requirementType: 'Proof of Value',
      description: 'Vendor/Commercial Invoice supporting claim amount',
      status: 'MISSING'
    });
  }

  // Check 4: Damage Photos
  totalPoints += 15;
  const photoDoc = documents.find(d => d.documentType === 'DAMAGE_PHOTO' || d.documentType === 'INSPECTION_REPORT');
  if (photoDoc) {
    earnedPoints += 15;
    met.push('Physical damage photos / Inspection report attached');
    requirements.push({
      id: 'req-photo',
      requirementType: 'Damage Proof',
      description: 'Clear photographic evidence of cargo damage',
      status: 'MET',
      evidenceDocumentId: photoDoc.id
    });
  } else {
    missing.push('Physical damage photos or inspection report missing');
    requirements.push({
      id: 'req-photo',
      requirementType: 'Damage Proof',
      description: 'Clear photographic evidence of cargo damage',
      status: 'MISSING'
    });
  }

  // Check 5: Claim Amount & Fact Grounding
  totalPoints += 15;
  if (claim.claimedAmount && claim.claimedAmount > 0) {
    earnedPoints += 15;
    met.push(`Claim amount supported ($${claim.claimedAmount.toLocaleString()})`);
  } else {
    missing.push('Claim amount uncalculated or unsupported');
  }

  // Check 6: Document Contradictions
  if (bolDoc && podDoc) {
    const bolPro = bolDoc.evidences.find(e => e.fieldName === 'proNumber' || e.fieldName === 'shipmentReference')?.sourceText;
    const podPro = podDoc.evidences.find(e => e.fieldName === 'proNumber' || e.fieldName === 'shipmentReference')?.sourceText;

    if (bolPro && podPro && bolPro.replace(/\D/g, '') !== podPro.replace(/\D/g, '')) {
      contradictions.push({
        id: 'c1',
        field1: 'BOL PRO Number',
        field2: 'POD PRO Number',
        description: `Mismatched PRO reference: BOL lists '${bolPro}' while POD lists '${podPro}'`,
        severity: 'HIGH',
        resolved: false
      });
      warnings.push(`Contradiction detected: BOL PRO (${bolPro}) != POD PRO (${podPro})`);
    }
  }

  const score = Math.round((earnedPoints / totalPoints) * 100);

  let status: 'READY' | 'BLOCKED' | 'ESCALATED' = 'READY';
  if (missing.length > 0 || contradictions.some(c => !c.resolved && c.severity === 'HIGH')) {
    status = 'BLOCKED';
  } else if ((claim.claimedAmount || 0) >= 5000) {
    status = 'ESCALATED';
  }

  return {
    score,
    status,
    explanations: { met, missing, warnings },
    requirements,
    contradictions
  };
}
