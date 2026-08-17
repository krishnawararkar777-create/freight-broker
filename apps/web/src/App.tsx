import { useState, useMemo } from 'react';
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

  // Filter claims & ledger events by tenant Organization ID for strict multi-tenancy
  const tenantClaims = useMemo(() => {
    if (!org) return [];
    // If Apex Freight Brokers, show Apex claims. If Swift Line Logistics, show Swift claims.
    if (org.id === 'org-swift-002') {
      return claims.filter(c => c.shipment?.carrierName === 'Swift Line Logistics' || c.shipment?.carrierId === 'car-002' || c.organizationId === 'org-swift-002');
    }
    return claims.filter(c => c.organizationId === 'org-apex-001' || !c.organizationId);
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
