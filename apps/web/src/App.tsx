import { useState } from 'react';
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

export function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'review' | 'ledger' | 'rules' | 'audit'>('dashboard');
  const [claims, setClaims] = useState<Claim[]>(mockClaims);
  const [selectedClaimId, setSelectedClaimId] = useState<string>('clm-847293');
  const [recoveryEvents, setRecoveryEvents] = useState<RecoveryEvent[]>(mockRecoveryEvents);
  const [feeEvents, setFeeEvents] = useState<FeeEvent[]>(mockFeeEvents);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>(mockAuditEvents);

  const [isUploadModalOpen, setIsUploadModalOpen] = useState<boolean>(false);
  const [isRecoveryModalOpen, setIsRecoveryModalOpen] = useState<boolean>(false);
  const [claimForRecoveryModal, setClaimForRecoveryModal] = useState<Claim | null>(null);

  const selectedClaim = claims.find(c => c.id === selectedClaimId) || claims[0];

  const handleSelectClaim = (claimId: string) => {
    setSelectedClaimId(claimId);
    setActiveTab('review');
  };

  const handleUpdateClaim = (updatedClaim: Claim) => {
    setClaims(prev => prev.map(c => c.id === updatedClaim.id ? updatedClaim : c));
  };

  const handleAddClaim = (newClaim: Claim) => {
    setClaims(prev => [newClaim, ...prev]);
    setSelectedClaimId(newClaim.id);
    setActiveTab('review');

    const newAudit: AuditEvent = {
      id: `aud-${Date.now()}`,
      organizationId: mockOrg.id,
      claimId: newClaim.id,
      actorType: 'AI',
      actorId: 'Algolyra-Extraction-Worker-v4',
      action: 'CLAIM_INGESTED_VIA_DOCUMENT_OCR',
      entityType: 'Claim',
      entityId: newClaim.id,
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
      organizationId: mockOrg.id,
      claimId: updatedClaim.id,
      actorType: 'HUMAN',
      actorId: 'usr-1 (Sarah Jenkins)',
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
        org={mockOrg}
        onOpenUpload={() => setIsUploadModalOpen(true)}
        selectedClaimNumber={selectedClaim?.claimNumber}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'dashboard' && (
          <DashboardView
            claims={claims}
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
            claims={claims}
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
        Algolyra Operating Layer (v4) — Evidence-Grounded Freight Claims Platform | $0 Fee on $0 Recovered
      </footer>
    </div>
  );
}

export default App;
