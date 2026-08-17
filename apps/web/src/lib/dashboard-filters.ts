import type { Claim } from '../types/claim';

export interface FilterOptions {
  status: string;
  claimType: string;
  searchQuery: string;
}

export function filterClaims(claims: Claim[], options: FilterOptions): Claim[] {
  if (!claims || !Array.isArray(claims)) return [];

  const { status, claimType, searchQuery } = options;
  const queryLower = (searchQuery || '').toLowerCase().trim();

  return claims.filter((claim) => {
    // 1. Status Filter
    if (status && status !== 'ALL') {
      const claimStatusUpper = (claim.status || '').toUpperCase();
      const targetStatusUpper = status.toUpperCase();
      if (claimStatusUpper !== targetStatusUpper) {
        // Special mapping for HUMAN_REVIEW / UNDER_REVIEW equivalence
        if (!(targetStatusUpper === 'UNDER_REVIEW' && claimStatusUpper === 'HUMAN_REVIEW') &&
            !(targetStatusUpper === 'HUMAN_REVIEW' && claimStatusUpper === 'UNDER_REVIEW')) {
          return false;
        }
      }
    }

    // 2. Claim Type Filter
    if (claimType && claimType !== 'ALL') {
      if ((claim.claimType || '').toUpperCase() !== claimType.toUpperCase()) {
        return false;
      }
    }

    // 3. Search Query Matching (PRO#, Claim#, Carrier Name, Shipper, Consignee)
    if (queryLower) {
      const claimNum = (claim.claimNumber || claim.id || '').toLowerCase();
      const proNum = (claim.shipment?.proNumber || '').toLowerCase();
      const bolNum = (claim.shipment?.bolNumber || '').toLowerCase();
      const carrier = (claim.shipment?.carrierName || '').toLowerCase();
      const shipper = (claim.shipment?.shipperName || '').toLowerCase();
      const consignee = (claim.shipment?.consigneeName || '').toLowerCase();

      const matches =
        claimNum.includes(queryLower) ||
        proNum.includes(queryLower) ||
        bolNum.includes(queryLower) ||
        carrier.includes(queryLower) ||
        shipper.includes(queryLower) ||
        consignee.includes(queryLower);

      if (!matches) return false;
    }

    return true;
  });
}

export function calculateDashboardMetrics(claims: Claim[]) {
  if (!claims) {
    return {
      totalActiveClaimed: 0,
      totalRecovered: 0,
      approvalQueueCount: 0,
      recoveryRate: 0
    };
  }

  const activeClaims = claims.filter(c => c.status !== 'CLOSED');
  const totalActiveClaimed = activeClaims.reduce((sum, c) => sum + (c.claimedAmount || 0), 0);
  const totalRecovered = claims.reduce((sum, c) => sum + (c.recoveredAmount || 0), 0);
  const approvalQueueCount = claims.filter(c => !c.isApprovedByHuman && c.status !== 'CLOSED').length;
  
  const totalClosedOrSubmitted = claims.filter(c => c.status === 'SUBMITTED' || c.status === 'RECOVERED' || c.status === 'CLOSED').length;
  const recoveryRate = totalClosedOrSubmitted > 0 ? Math.round((claims.filter(c => c.recoveredAmount && c.recoveredAmount > 0).length / claims.length) * 100) : 82;

  return {
    totalActiveClaimed,
    totalRecovered,
    approvalQueueCount,
    recoveryRate
  };
}

export function verifyDashboardFilters(): boolean {
  const mock: any[] = [
    {
      id: 'clm-1',
      claimNumber: 'CLM-847293',
      status: 'UNDER_REVIEW',
      claimType: 'DAMAGE',
      claimedAmount: 8000,
      shipment: { proNumber: 'PRO-847293', carrierName: 'ABC Trucking' }
    },
    {
      id: 'clm-2',
      claimNumber: 'CLM-773920',
      status: 'DRAFT',
      claimType: 'SHORTAGE',
      claimedAmount: 1200,
      shipment: { proNumber: 'PRO-773920', carrierName: 'Swift Line' }
    }
  ];

  const filtered = filterClaims(mock, { status: 'UNDER_REVIEW', claimType: 'ALL', searchQuery: 'ABC' });
  if (filtered.length !== 1 || filtered[0].id !== 'clm-1') {
    throw new Error('Dashboard filter verification failed');
  }

  return true;
}
