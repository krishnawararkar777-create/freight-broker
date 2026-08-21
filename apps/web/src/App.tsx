import { useState, useMemo, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginView } from './components/LoginView';
import { Navbar } from './components/Navbar';
import { DashboardView } from './components/DashboardView';
import { HumanReviewWorkspace } from './components/HumanReviewWorkspace';
import { RecoveryLedgerView } from './components/RecoveryLedgerView';
import { CarrierRulesView } from './components/CarrierRulesView';
import { AuditLogView } from './components/AuditLogView';
import { DocumentUploadModal } from './components/DocumentUploadModal';
import { RecordRecoveryModal } from './components/RecordRecoveryModal';

import { mockOrg, mockClaims, mockCarrierRuleSets, mockRecoveryEvents, mockFeeEvents, mockAuditEvents } from './data/mockClaims';
import type { Claim, RecoveryEvent, FeeEvent, AuditEvent } from './types/claim';
import { ShieldCheck } from 'lucide-react';

function MainApp() {
  const { session, loading, userProfile, org, role, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<'dashboard' | 'review' | 'ledger' | 'rules' | 'audit'>('dashboard');
  const [claims, setClaims] = useState<Claim[]>(mockClaims);
  const [selectedClaimId, setSelectedClaimId] = useState<string>('clm-847293');
  const [recoveryEvents, setRecoveryEvents] = useState<RecoveryEvent[]>(mockRecoveryEvents);
  const [feeEvents, setFeeEvents] = useState<FeeEvent[]>(mockFeeEvents);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>(mockAuditEvents);

  const [isUploadModalOpen, setIsUploadModalOpen] = useState<boolean>(false);
  const [isRecoveryModalOpen, setIsRecoveryModalOpen] = useState<boolean>(false);
  const [claimForRecoveryModal, setClaimForRecoveryModal] = useState<Claim | null>(null);

  // Live polling sync with FastAPI backend GET /api/claims
  useEffect(() => {
    const fetchLiveClaims = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/claims');
        if (res.ok) {
          const liveClaimsData = await res.json();
          setClaims(prev => {
            const prevMap = new Map(prev.map(c => [c.id, c]));
            liveClaimsData.forEach((lc: any) => {
              if (!prevMap.has(lc.id)) {
                const formattedClaim: Claim = {
                  id: lc.id,
                  organizationId: lc.organization_id || 'org-apex-001',
                  shipmentId: lc.shipment_id || `shp-${lc.id}`,
                  claimNumber: lc.claim_number || lc.id.toUpperCase(),
                  claimType: (lc.claim_type === 'Cargo Damage' ? 'DAMAGE' : lc.claim_type) as any,
                  status: lc.status || 'DRAFT',
                  claimedAmount: lc.claimed_amount || 8000,
                  currency: 'USD',
                  recoveredAmount: 0,
                  deadlineAt: lc.deadline_at || '2027-05-20T00:00:00Z',
                  concealedDeadlineAt: lc.concealed_deadline_at || '2026-08-25T00:00:00Z',
                  lawsuitDeadlineAt: lc.lawsuit_deadline_at || '2028-08-21T00:00:00Z',
                  humanThresholdTriggered: (lc.claimed_amount || 8000) >= 5000,
                  approvalLevelRequired: 1,
                  isApprovedByHuman: lc.is_approved_by_human || false,
                  ownerUserId: 'usr-1',
                  createdAt: lc.created_at || new Date().toISOString(),
                  updatedAt: new Date().toISOString(),
                  readinessScore: 92,
                  readinessExplanations: [
                    `✓ EDI / TMS Ingestion synced: Carrier ${lc.carrier_name || 'FXFE'}`,
                    `✓ Delivery Date locked: ${lc.delivery_date || '2026-08-20'}`,
                    `✓ Carmack 9-month statutory clock active (${(lc.deadline_at || '2027-05-20').split('T')[0]})`
                  ],
                  shipment: {
                    id: lc.shipment_id || `shp-${lc.id}`,
                    organizationId: lc.organization_id || 'org-apex-001',
                    externalReference: `REF-${lc.pro_number || '847293'}`,
                    bolNumber: lc.bol_number || 'BOL-847293',
                    proNumber: lc.pro_number || 'PRO-847293',
                    carrierId: 'car-fxfe',
                    carrierName: lc.carrier_name || 'FXFE (FedEx Freight)',
                    shipperName: 'TechComponents Corp',
                    consigneeName: 'Metro Logistics Distribution',
                    origin: 'Los Angeles, CA',
                    destination: 'Chicago, IL',
                    pickupDate: '2026-08-15',
                    deliveryDate: lc.delivery_date || '2026-08-20',
                    declaredValue: lc.claimed_amount || 8000,
                    currency: 'USD',
                    commodity: 'High-Precision Microcontrollers',
                    quantity: 10,
                    weightLbs: 4500
                  },
                  documents: [
                    {
                      id: `doc-${lc.id}-1`,
                      organizationId: 'org-apex-001',
                      claimId: lc.id,
                      shipmentId: `shp-${lc.id}`,
                      documentType: 'BOL',
                      filename: 'bol_mcleod_live_501.pdf',
                      mimeType: 'application/pdf',
                      storageUrl: 'https://mcleod.mock.tms/docs/bol_mcleod_live_501.pdf',
                      sha256: 'a1b2c3d4e5f6',
                      pageCount: 1,
                      extractionStatus: 'EXTRACTED',
                      uploadedAt: new Date().toISOString(),
                      evidences: []
                    }
                  ],
                  facts: [],
                  requirements: []
                };
                prevMap.set(lc.id, formattedClaim);
              }
            });
            return Array.from(prevMap.values());
          });
        }
      } catch (e) {
        // Backend API offline fallback
      }
    };

    fetchLiveClaims();
    const interval = setInterval(fetchLiveClaims, 3000);
    return () => clearInterval(interval);
  }, []);

  // Filter claims & ledger events by tenant Organization ID for strict multi-tenancy
  const tenantClaims = useMemo(() => {
    if (!org) return claims;
    // If Swift Line Logistics (Org B / User B)
    if (org.id === 'org-swift-002') {
      return claims.filter(c => c.organizationId === 'org-swift-002' || c.shipment?.carrierName === 'Swift Line Logistics' || c.shipment?.carrierId === 'car-swift');
    }
    // If Apex Freight Brokers (Org A / User A / default custom users)
    return claims.filter(c => c.organizationId !== 'org-swift-002' && c.shipment?.carrierName !== 'Swift Line Logistics');
  }, [claims, org]);

  const selectedClaim = tenantClaims.find(c => c.id === selectedClaimId) || tenantClaims[0];

  // 1. Route Protection & Loading State Guard
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center text-slate-100 font-sans">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-xl shadow-cyan-500/30 animate-bounce mb-4">
          <ShieldCheck className="w-7 h-7 text-white" />
        </div>
        <div className="text-sm font-semibold tracking-wide text-cyan-400 font-mono animate-pulse">
          VERIFYING SUPABASE AUTH SESSION...
        </div>
      </div>
    );
  }

  // 2. Strict Unauthenticated Redirect -> Login Screen
  if (!session || !userProfile) {
    return <LoginView />;
  }

  const handleSelectClaim = (claimId: string) => {
    setSelectedClaimId(claimId);
    setActiveTab('review');
  };

  const handleUpdateClaim = (updatedClaim: Claim) => {
    setClaims(prev => prev.map(c => c.id === updatedClaim.id ? updatedClaim : c));
  };

  const handleAddClaim = (newClaim: Claim) => {
    const tenantScopedClaim = { ...newClaim, organizationId: org?.id || 'org-apex-001' };
    setClaims(prev => [tenantScopedClaim, ...prev]);
    setSelectedClaimId(tenantScopedClaim.id);
    setActiveTab('review');

    const newAudit: AuditEvent = {
      id: `aud-${Date.now()}`,
      organizationId: org?.id || mockOrg.id,
      claimId: tenantScopedClaim.id,
      actorType: 'AI',
      actorId: 'Algolyra-Extraction-Worker-v4',
      action: 'CLAIM_INGESTED_VIA_DOCUMENT_OCR',
      entityType: 'Claim',
      entityId: tenantScopedClaim.id,
      createdAt: new Date().toISOString()
    };
    setAuditEvents(prev => [newAudit, ...prev]);
  };

  const handleOpenRecoveryModal = (claim: Claim) => {
    setClaimForRecoveryModal(claim);
    setIsRecoveryModalOpen(true);
  };

  const handleRecordRecovery = (updatedClaim: Claim, recoveryEvent: RecoveryEvent, feeEvent: FeeEvent) => {
    handleUpdateClaim(updatedClaim);
    setRecoveryEvents(prev => [recoveryEvent, ...prev]);
    setFeeEvents(prev => [feeEvent, ...prev]);

    const newAudit: AuditEvent = {
      id: `aud-rec-${Date.now()}`,
      organizationId: org?.id || mockOrg.id,
      claimId: updatedClaim.id,
      actorType: 'HUMAN',
      actorId: `${userProfile.id} (${userProfile.name})`,
      action: 'RECORDED_CARRIER_SETTLEMENT',
      entityType: 'RecoveryEvent',
      entityId: recoveryEvent.id,
      afterJson: { amount: recoveryEvent.amount, feeAmount: feeEvent.feeAmount },
      createdAt: new Date().toISOString()
    };
    setAuditEvents(prev => [newAudit, ...prev]);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased selection:bg-cyan-500 selection:text-slate-950">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        org={org}
        role={role}
        userProfile={userProfile}
        onLogout={logout}
        onOpenUpload={() => setIsUploadModalOpen(true)}
        selectedClaimNumber={selectedClaim?.claimNumber}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'dashboard' && (
          <DashboardView
            claims={tenantClaims}
            onSelectClaim={handleSelectClaim}
            onOpenUpload={() => setIsUploadModalOpen(true)}
          />
        )}

        {activeTab === 'review' && selectedClaim && (
          <HumanReviewWorkspace
            claim={selectedClaim}
            onUpdateClaim={handleUpdateClaim}
            onBackToDashboard={() => setActiveTab('dashboard')}
            onRecordRecoveryModal={handleOpenRecoveryModal}
          />
        )}

        {activeTab === 'ledger' && (
          <RecoveryLedgerView
            claims={tenantClaims}
            recoveryEvents={recoveryEvents}
            feeEvents={feeEvents}
          />
        )}

        {activeTab === 'rules' && (
          <CarrierRulesView
            ruleSets={mockCarrierRuleSets}
          />
        )}

        {activeTab === 'audit' && (
          <AuditLogView
            auditEvents={auditEvents}
          />
        )}
      </main>

      <DocumentUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onAddClaim={handleAddClaim}
      />

      <RecordRecoveryModal
        claim={claimForRecoveryModal}
        isOpen={isRecoveryModalOpen}
        onClose={() => setIsRecoveryModalOpen(false)}
        onRecordRecovery={handleRecordRecovery}
      />

      <footer className="border-t border-slate-900 bg-slate-950/80 py-6 text-center text-xs text-slate-500 font-mono">
        Algolyra Operating Layer (v4) — Multi-Tenant Supabase Auth Enabled | Active Tenant: <span className="text-cyan-400 font-bold">{org?.name}</span> ({role})
      </footer>
    </div>
  );
}

export function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}

export default App;
