export interface BoundingBox {
  page_number: number;
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
}

export interface DocumentEvidenceItem {
  id: string;
  document_id: string;
  field_name: string;
  page_number: number;
  bbox_json?: BoundingBox | null;
  source_text?: string | null;
  confidence: number;
}

export function findMatchingEvidence(
  fieldName: string,
  evidenceList: DocumentEvidenceItem[]
): DocumentEvidenceItem | undefined {
  if (!fieldName || !evidenceList) return undefined;
  return evidenceList.find(ev => ev.field_name === fieldName);
}

export function formatCitation(documentType: string, pageNumber: number = 1): string {
  const docAbbr = documentType.toUpperCase();
  return `[${docAbbr} p.${pageNumber}]`;
}

// Self-contained verification assertion helper
export function verifySyncLogic(): boolean {
  const sampleEvidence: DocumentEvidenceItem[] = [
    {
      id: 'evd-1',
      document_id: 'doc-1',
      field_name: 'carrier_name',
      page_number: 1,
      bbox_json: { page_number: 1, x_min: 0.1, y_min: 0.1, x_max: 0.4, y_max: 0.15 },
      source_text: 'ABC TRUCKING',
      confidence: 0.98
    }
  ];
  const matched = findMatchingEvidence('carrier_name', sampleEvidence);
  if (!matched || matched.id !== 'evd-1') {
    throw new Error('Sync logic verification failed');
  }
  if (formatCitation('bol', 1) !== '[BOL p.1]') {
    throw new Error('Citation formatting verification failed');
  }
  return true;
}
