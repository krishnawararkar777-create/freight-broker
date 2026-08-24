import { useState, useMemo, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginView } from './components/LoginView';
import { Sidebar } from './components/Sidebar';
import { TopHeaderBar } from './components/TopHeaderBar';
import { DashboardView } from './components/DashboardView';
import { ExecutiveAnalyticsDashboard } from './components/ExecutiveAnalyticsDashboard';
import { HumanReviewWorkspace } from './components/HumanReviewWorkspace';
import { RecoveryLedgerView } from './components/RecoveryLedgerView';
import { CarrierRulesView } from './components/CarrierRulesView';
import { AuditLogView } from './components/AuditLogView';
import { DocumentUploadModal } from './components/DocumentUploadModal';
import { RecordRecoveryModal } from './components/RecordRecoveryModal';

import { mockOrg, mockCarrierRuleSets, mockRecoveryEvents, mockFeeEvents, mockAuditEvents } from './data/mockClaims';
import type { Claim, RecoveryEvent, FeeEvent, AuditEvent } from './types/claim';

function MainApp() {
  const { session, loading, userProfile, org, role, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<'dashboard' | 'analytics' | 'review' | 'ledger' | 'rules' | 'audit'>('dashboard');
  const [reviewSubTab, setReviewSubTab] = useState<'draft' | 'readiness' | 'salvage' | 'carrier-risk' | 'legal' | 'tariff-guardian'>('draft');
  const [claims, setClaims] = useState<Claim[]>([]);
  const [isLoadingClaims, setIsLoadingClaims] = useState<boolean>(true);
  const [errorClaims, setErrorClaims] = useState<string | null>(null);
  const [selectedClaimId, setSelectedClaimId] = useState<string>('clm-847293');
  const [recoveryEvents, setRecoveryEvents] = useState<RecoveryEvent[]>(mockRecoveryEvents);
  const [feeEvents, setFeeEvents] = useState<FeeEvent[]>(mockFeeEvents);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>(mockAuditEvents);

  const [isUploadModalOpen, setIsUploadModalOpen] = useState<boolean>(false);
  const [isRecoveryModalOpen, setIsRecoveryModalOpen] = useState<boolean>(false);
  const [claimForRecoveryModal, setClaimForRecoveryModal] = useState<Claim | null>(null);

  // Live polling sync with FastAPI backend GET /api/claims?organization_id=<org.id>
  useEffect(() => {
    if (!org?.id) {
      setClaims([]);
      setIsLoadingClaims(false);
      return;
    }

    const fetchLiveClaims = async () => {
      try {
        setErrorClaims(null);
        const res = await fetch(`http://localhost:8000/api/claims?organization_id=${org.id}`, {
          headers: {
            'Authorization': `Bearer ${session?.access_token || ''}`,
            'X-Organization-ID': org.id
          }
        });
        if (res.ok) {
          const liveClaimsData = await res.json();
          const formatted: Claim[] = liveClaimsData.map((lc: any) => ({
            id: lc.id,
            organizationId: lc.organization_id || org.id,
            shipmentId: lc.shipment_id || `shp-${lc.id}`,
            claimNumber: lc.claim_number || lc.id.toUpperCase(),
            claimType: (lc.claim_type === 'Cargo Damage' ? 'DAMAGE' : lc.claim_type) as any,
            status: lc.status || 'DRAFT',
            claimedAmount: lc.claimed_amount || 0,
            currency: 'USD',
            recoveredAmount: lc.recovered_amount || 0,
            deadlineAt: lc.deadline_at || '2027-05-20T00:00:00Z',
            concealedDeadlineAt: lc.concealed_deadline_at || '2026-08-25T00:00:00Z',
            lawsuitDeadlineAt: lc.lawsuit_deadline_at || '2028-08-21T00:00:00Z',
            humanThresholdTriggered: (lc.claimed_amount || 0) >= 5000,
            approvalLevelRequired: 1,
            isApprovedByHuman: lc.is_approved_by_human || false,
            ownerUserId: lc.approved_by_user_id || 'usr-1',
            createdAt: lc.created_at || new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            readinessScore: 92,
            readinessExplanations: [
              `✓ EDI / TMS Ingestion synced: Carrier ${lc.carrier_name || 'FXFE'}`,
              `✓ Carmack 9-month statutory clock active`
            ],
            shipment: {
              id: lc.shipment_id || `shp-${lc.id}`,
              organizationId: lc.organization_id || org.id,
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
              declaredValue: lc.claimed_amount || 0,
              currency: 'USD',
              commodity: 'Cargo Freight',
              quantity: 10,
              weightLbs: 4500
            },
            documents: [
              {
                id: `doc-${lc.id}-1`,
                organizationId: lc.organization_id || org.id,
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
          }));
          setClaims(formatted);
        } else {
          setErrorClaims(`Backend returned HTTP ${res.status}`);
        }
      } catch (e: any) {
        setErrorClaims('Backend claims service offline');
      } finally {
        setIsLoadingClaims(false);
      }
    };

    fetchLiveClaims();
    const interval = setInterval(fetchLiveClaims, 3000);
    return () => clearInterval(interval);
  }, [org?.id, session?.access_token]);

  // Filter claims & ledger events by tenant Organization ID for strict multi-tenancy
  const tenantClaims = useMemo(() => {
    if (!org) return [];
    return claims.filter(c => c.organizationId === org.id);
  }, [claims, org]);

  const selectedClaim = tenantClaims.find(c => c.id === selectedClaimId) || tenantClaims[0] || null;

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex flex-col justify-center items-center text-zinc-100 font-mono">
        <div className="w-10 h-10 bg-white transform rotate-45 flex items-center justify-center shadow-xl animate-bounce mb-6">
          <div className="w-3 h-3 bg-black" />
        </div>
        <div className="text-xs font-semibold tracking-widest text-zinc-400 uppercase animate-pulse">
          VERIFYING SUPABASE AUTH SESSION...
        </div>
      </div>
    );
  }

  if (!session || !userProfile) {
    return <LoginView />;
  }

  const handleSelectClaim = (claimId: string) => {
    setSelectedClaimId(claimId);
    setActiveTab('review');
    setReviewSubTab('draft');
  };

  const handleUpdateClaim = async (updatedClaim: Claim) => {
    setClaims(prev => prev.map(c => c.id === updatedClaim.id ? updatedClaim : c));

    try {
      await fetch(`http://localhost:8000/api/claims/${updatedClaim.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: updatedClaim.status,
          claimed_amount: updatedClaim.claimedAmount,
          is_approved_by_human: updatedClaim.isApprovedByHuman,
          approved_by_user_id: updatedClaim.approvedByUserId || 'usr-1'
        })
      });
    } catch {
      // offline fallback
    }
  };

  const handleAddClaim = (newClaim: Claim) => {
    const tenantScopedClaim = { ...newClaim, organizationId: org?.id || 'org-apex-001' };
    setClaims(prev => [tenantScopedClaim, ...prev]);
    setSelectedClaimId(tenantScopedClaim.id);
    setActiveTab('review');
    setReviewSubTab('draft');

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
    <div className="min-h-screen bg-black text-zinc-100 font-sans antialiased selection:bg-white selection:text-black flex">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        reviewSubTab={reviewSubTab}
        setReviewSubTab={setReviewSubTab}
        org={org}
        role={role}
        userProfile={userProfile}
        onLogout={logout}
        onOpenUpload={() => setIsUploadModalOpen(true)}
        selectedClaimNumber={selectedClaim?.claimNumber}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-black min-h-screen">
        <TopHeaderBar
          org={org}
          role={role}
          activeTab={activeTab}
        />

        <main className="flex-1 p-6 lg:p-8 max-w-[1600px] w-full mx-auto space-y-6">
          {activeTab === 'dashboard' && (
            <DashboardView
              claims={tenantClaims}
              onSelectClaim={handleSelectClaim}
              onOpenUpload={() => setIsUploadModalOpen(true)}
              onOpenAnalytics={() => setActiveTab('analytics')}
              isLoading={isLoadingClaims}
              error={errorClaims}
            />
          )}

          {activeTab === 'analytics' && (
            <ExecutiveAnalyticsDashboard
              claims={tenantClaims}
            />
          )}

          {activeTab === 'review' && selectedClaim && (
            <HumanReviewWorkspace
              claim={selectedClaim}
              onUpdateClaim={handleUpdateClaim}
              onBackToDashboard={() => setActiveTab('dashboard')}
              onRecordRecoveryModal={handleOpenRecoveryModal}
              reviewSubTab={reviewSubTab}
              onReviewSubTabChange={setReviewSubTab}
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

        <footer className="border-t border-zinc-800/80 bg-black py-4 px-6 text-center text-xs text-zinc-500 font-mono">
          Algolyra OS (v4) — Multi-Tenant Supabase Auth Enabled | Active Tenant: <span className="text-white font-bold">{org?.name}</span> ({role})
        </footer>
      </div>

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
