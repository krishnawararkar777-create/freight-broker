import React, { useState, useRef } from 'react';
import type { Claim } from '../types/claim';
import { Upload, CheckCircle2, Loader2, X, FileText, Check } from 'lucide-react';

interface DocumentUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddClaim: (newClaim: Claim) => void;
}

export const DocumentUploadModal: React.FC<DocumentUploadModalProps> = ({ isOpen, onClose, onAddClaim }) => {
  const [step, setStep] = useState<'upload' | 'parsing' | 'extracted'>('upload');
  const [proNumber, setProNumber] = useState('PRO-847293');
  const [carrierName, setCarrierName] = useState('ABC Trucking');
  const [claimedAmount, setClaimedAmount] = useState('8000');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const filesArray = Array.from(e.target.files);
      setSelectedFiles(prev => [...prev, ...filesArray]);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const filesArray = Array.from(e.dataTransfer.files);
      setSelectedFiles(prev => [...prev, ...filesArray]);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleSimulateExtraction = () => {
    setStep('parsing');

    setTimeout(() => {
      setStep('extracted');

      const claimId = `clm-${Date.now()}`;
      const shipmentId = `shp-${Date.now()}`;

      const newClaim: Claim = {
        id: claimId,
        organizationId: 'org-apex',
        shipmentId: shipmentId,
        claimNumber: `CLM-${proNumber.replace('PRO-', '')}`,
        claimType: 'DAMAGE',
        status: 'HUMAN_REVIEW',
        claimedAmount: Number(claimedAmount) || 8000,
        currency: 'USD',
        recoveredAmount: 0,
        deadlineAt: '2027-05-17T00:00:00Z',
        humanThresholdTriggered: Number(claimedAmount) >= 5000,
        approvalLevelRequired: Number(claimedAmount) >= 5000 ? 2 : 1,
        isApprovedByHuman: false,
        ownerUserId: 'usr-1',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        readinessScore: 94,
        readinessExplanations: [
          '✓ Bill of Lading (BOL-847293) verified & linked',
          '✓ Proof of Delivery (POD) exception notation extracted',
          '✓ Invoice total & affected damaged items valuation matched ($8,000)',
          '✓ Deadline safe: Carmack statutory limit active (May 17, 2027)'
        ],
        shipment: {
          id: shipmentId,
          organizationId: 'org-apex',
          externalReference: `REF-${proNumber}`,
          bolNumber: `BOL-${proNumber.replace('PRO-', '')}`,
          proNumber: proNumber,
          carrierId: 'car-abc',
          carrierName: carrierName,
          shipperName: 'Meridian Electronics Distributors',
          consigneeName: 'Riverside Retail Store #14',
          origin: 'Los Angeles, CA',
          destination: 'Chicago, IL',
          pickupDate: '2026-08-10',
          deliveryDate: '2026-08-17',
          declaredValue: Number(claimedAmount) || 8000,
          currency: 'USD',
          commodity: 'Precision Electronics',
          quantity: 10,
          weightLbs: 4500
        },
        documents: selectedFiles.length > 0 ? selectedFiles.map((file, idx) => {
          const fileNameLower = file.name.toLowerCase();
          const isImage = file.type.startsWith('image/') || fileNameLower.endsWith('.png') || fileNameLower.endsWith('.jpg') || fileNameLower.endsWith('.jpeg') || fileNameLower.includes('photo') || fileNameLower.includes('damage') || fileNameLower.includes('img');
          const isPod = fileNameLower.includes('pod');
          
          const docType = isImage ? 'DAMAGE_PHOTO' as const : (isPod ? 'POD' as const : 'BOL' as const);

          let evidences = [
            { id: `ev-${idx}-1`, documentId: `doc-${idx}`, pageNumber: 1, fieldName: 'bolNumber', sourceText: 'BOL NUMBER: BOL-847293', confidence: 0.98 },
            { id: `ev-${idx}-2`, documentId: `doc-${idx}`, pageNumber: 1, fieldName: 'proNumber', sourceText: `PRO NUMBER: ${proNumber}`, confidence: 0.98 },
            { id: `ev-${idx}-3`, documentId: `doc-${idx}`, pageNumber: 1, fieldName: 'poNumber', sourceText: 'PO / REFERENCE: PO-55210', confidence: 0.96 },
            { id: `ev-${idx}-4`, documentId: `doc-${idx}`, pageNumber: 1, fieldName: 'pickupDate', sourceText: 'PICKUP DATE: 2026-08-10', confidence: 0.97 },
            { id: `ev-${idx}-5`, documentId: `doc-${idx}`, pageNumber: 1, fieldName: 'shipperName', sourceText: 'SHIPPER: Meridian Electronics Distributors (Los Angeles, CA)', confidence: 0.97 },
            { id: `ev-${idx}-6`, documentId: `doc-${idx}`, pageNumber: 1, fieldName: 'consigneeName', sourceText: 'CONSIGNEE: Riverside Retail Store #14 (Chicago, IL)', confidence: 0.96 },
            { id: `ev-${idx}-7`, documentId: `doc-${idx}`, pageNumber: 1, fieldName: 'declaredValue', sourceText: `DECLARED VALUE: $${claimedAmount}`, confidence: 0.98 }
          ];

          if (isImage) {
            evidences = [
              { id: `ev-img-${idx}-1`, documentId: `doc-${idx}`, pageNumber: 1, fieldName: 'damageNotation', sourceText: 'VISUAL OCR: Crushed pallet corner and puncture impact on side panel', confidence: 0.97 },
              { id: `ev-img-${idx}-2`, documentId: `doc-${idx}`, pageNumber: 1, fieldName: 'photoTimestamp', sourceText: 'EXIF TIMESTAMP: 2026-08-17 14:15:00 EST', confidence: 0.99 },
              { id: `ev-img-${idx}-3`, documentId: `doc-${idx}`, pageNumber: 1, fieldName: 'damageSeverity', sourceText: 'AI SEVERITY SCORE: HIGH — Physical Pallet Crushing Detected', confidence: 0.95 }
            ];
          } else if (isPod) {
            evidences = [
              { id: `ev-${idx}-1`, documentId: `doc-${idx}`, pageNumber: 1, fieldName: 'podReference', sourceText: 'REFERENCE: POD-2026-0817-001', confidence: 0.98 },
              { id: `ev-${idx}-2`, documentId: `doc-${idx}`, pageNumber: 1, fieldName: 'deliveryDate', sourceText: 'DELIVERY DATE: AUGUST 17, 2026', confidence: 0.99 },
              { id: `ev-${idx}-3`, documentId: `doc-${idx}`, pageNumber: 1, fieldName: 'deliveredItemsManifest', sourceText: '3x Office Chair ($360), 2x Standing Desk ($500), 1x Monitor ($180)', confidence: 0.96 },
              { id: `ev-${idx}-4`, documentId: `doc-${idx}`, pageNumber: 1, fieldName: 'totalDeliveredValue', sourceText: 'TOTAL DELIVERED VALUE: $1,040.00', confidence: 0.99 }
            ];
          }

          return {
            id: `doc-${idx + 1}-${Date.now()}`,
            organizationId: 'org-apex',
            claimId: claimId,
            shipmentId: shipmentId,
            documentType: docType,
            filename: file.name,
            mimeType: file.type || (isImage ? 'image/jpeg' : 'application/pdf'),
            storageUrl: URL.createObjectURL(file),
            sha256: `sha256-${Math.random().toString(36).substring(2)}`,
            pageCount: 1,
            extractionStatus: 'EXTRACTED' as const,
            uploadedAt: new Date().toISOString(),
            evidences
          };
        }) : [
          {
            id: `doc-1-${Date.now()}`,
            organizationId: 'org-apex',
            claimId: claimId,
            shipmentId: shipmentId,
            documentType: 'BOL',
            filename: `BOL_${proNumber}.pdf`,
            mimeType: 'application/pdf',
            storageUrl: '',
            sha256: 'a1b2c3d4e5f67890',
            pageCount: 1,
            extractionStatus: 'EXTRACTED',
            uploadedAt: new Date().toISOString(),
            evidences: [
              { id: 'ev-new-1', documentId: 'doc-1', pageNumber: 1, fieldName: 'proNumber', sourceText: `PRO #: ${proNumber}`, confidence: 0.98 }
            ]
          },
          {
            id: `doc-2-${Date.now()}`,
            organizationId: 'org-apex',
            claimId: claimId,
            shipmentId: shipmentId,
            documentType: 'POD',
            filename: `POD_${proNumber}.pdf`,
            mimeType: 'application/pdf',
            storageUrl: '',
            sha256: 'f6e5d4c3b2a10987',
            pageCount: 1,
            extractionStatus: 'EXTRACTED',
            uploadedAt: new Date().toISOString(),
            evidences: [
              { id: 'ev-new-2', documentId: 'doc-2', pageNumber: 1, fieldName: 'damageNotation', sourceText: '2 pallets crushed & damaged at rear door', confidence: 0.95 }
            ]
          }
        ],
        facts: [
          { id: 'f-new-1', claimId: claimId, fieldName: 'proNumber', displayName: 'PRO Number', valueJson: proNumber, confidence: 0.98, verificationStatus: 'VERIFIED' },
          { id: 'f-new-2', claimId: claimId, fieldName: 'carrierName', displayName: 'Carrier Name', valueJson: carrierName, confidence: 0.96, verificationStatus: 'VERIFIED' },
          { id: 'f-new-3', claimId: claimId, fieldName: 'claimedAmount', displayName: 'Claimed Amount', valueJson: Number(claimedAmount), confidence: 0.95, verificationStatus: 'VERIFIED' },
          { id: 'f-new-4', claimId: claimId, fieldName: 'shipperName', displayName: 'Shipper Name', valueJson: 'Meridian Electronics Distributors', confidence: 0.97, verificationStatus: 'VERIFIED' },
          { id: 'f-new-5', claimId: claimId, fieldName: 'consigneeName', displayName: 'Consignee Name', valueJson: 'Riverside Retail Store #14', confidence: 0.96, verificationStatus: 'VERIFIED' }
        ],
        packageDraft: {
          id: `pkg-${Date.now()}`,
          claimId: claimId,
          coverSummary: `FORMAL CARGO CLAIM DEMAND — ${proNumber}`,
          narrativeText: `To Claims Dept, ${carrierName}:\n\nPursuant to 49 U.S.C. § 14706 (Carmack Amendment) [49 U.S.C. § 14706 (Carmack Amendment)] and NMFC Item 300105 [NMFC Item 300105], please accept this formal written cargo claim for shipment ${proNumber} [BOL p.1]. Delivered on 2026-08-17 [POD p.1]. Total damages claimed: $${claimedAmount} [INV-90210].`,
          chronologyText: 'Pickup 08/10/2026 | Delivery 08/17/2026',
          amountClaimedCalculated: Number(claimedAmount),
          amountCalculationBreakdown: `$${claimedAmount} damaged value verified from invoice`,
          evidenceChecklistText: '✓ BOL\n✓ POD Exception\n✓ Invoice',
          generatedAt: new Date().toISOString(),
          modelName: 'Algolyra-Drafting-v4',
          modelVersion: '4.2.1-grounded'
        }
      };

      onAddClaim(newClaim);
    }, 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5 animate-scale-up">
        <div className="flex justify-between items-center border-b border-slate-800 pb-3">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Upload className="w-5 h-5 text-cyan-400" /> Ingest Freight Claim Documents
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {step === 'upload' && (
          <div className="space-y-4">
            <input
              type="file"
              ref={fileInputRef}
              multiple
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={handleFileSelect}
              className="hidden"
            />

            <div
              onClick={() => fileInputRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              className="border-2 border-dashed border-slate-700 hover:border-cyan-400 bg-slate-950 p-8 rounded-xl text-center cursor-pointer transition-colors space-y-2 group"
            >
              <Upload className="w-10 h-10 text-cyan-400 group-hover:scale-110 transition-transform mx-auto" />
              <div className="text-sm font-bold text-white">Click to browse or Drag & Drop BOL, POD, Invoice</div>
              <div className="text-xs text-slate-400">PDF, PNG, JPG accepted (Automated OCR & Fact Grounding)</div>
            </div>

            {selectedFiles.length > 0 && (
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1.5">
                <div className="text-xs font-bold text-cyan-400 flex items-center gap-1">
                  <Check className="w-3.5 h-3.5" /> Selected {selectedFiles.length} File(s) for Intake:
                </div>
                <div className="space-y-1">
                  {selectedFiles.map((file, idx) => (
                    <div key={idx} className="text-xs font-mono text-slate-200 flex items-center gap-1.5 bg-slate-900 px-2.5 py-1 rounded border border-slate-800">
                      <FileText className="w-3.5 h-3.5 text-slate-400" />
                      <span className="truncate">{file.name}</span>
                      <span className="text-[10px] text-slate-500 ml-auto">{(file.size / 1024).toFixed(0)} KB</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="space-y-3 pt-1">
              <div>
                <label className="text-xs text-slate-300 font-mono block">PRO Number</label>
                <input
                  type="text"
                  value={proNumber}
                  onChange={(e) => setProNumber(e.target.value)}
                  className="w-full bg-slate-950 text-white text-xs px-3 py-2 rounded-lg border border-slate-700 focus:border-cyan-400 outline-none font-mono"
                />
              </div>

              <div>
                <label className="text-xs text-slate-300 font-mono block">Carrier Name</label>
                <input
                  type="text"
                  value={carrierName}
                  onChange={(e) => setCarrierName(e.target.value)}
                  className="w-full bg-slate-950 text-white text-xs px-3 py-2 rounded-lg border border-slate-700 focus:border-cyan-400 outline-none"
                />
              </div>

              <div>
                <label className="text-xs text-slate-300 font-mono block">Claimed Amount ($)</label>
                <input
                  type="number"
                  value={claimedAmount}
                  onChange={(e) => setClaimedAmount(e.target.value)}
                  className="w-full bg-slate-950 text-white text-xs px-3 py-2 rounded-lg border border-slate-700 focus:border-cyan-400 outline-none font-mono"
                />
              </div>
            </div>

            <button
              onClick={handleSimulateExtraction}
              className="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-extrabold py-2.5 rounded-xl text-sm transition-all shadow-lg shadow-cyan-500/20"
            >
              Run AI OCR & Evidence Extraction Pipeline
            </button>
          </div>
        )}

        {step === 'parsing' && (
          <div className="py-12 text-center space-y-4">
            <Loader2 className="w-12 h-12 text-cyan-400 animate-spin mx-auto" />
            <div>
              <div className="text-base font-bold text-white">Extracting Facts & Grounding Evidence...</div>
              <div className="text-xs text-slate-400 mt-1">
                Parsing BOL, POD notation, Invoice values, and verifying Carmack deadlines
              </div>
            </div>
          </div>
        )}

        {step === 'extracted' && (
          <div className="py-6 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-emerald-500/10 border-2 border-emerald-400 flex items-center justify-center mx-auto text-emerald-400">
              <CheckCircle2 className="w-7 h-7" />
            </div>
            <div>
              <div className="text-base font-bold text-white">Claim Ingested Successfully!</div>
              <div className="text-xs text-slate-400 mt-1">
                Readiness score: 94%. Placed into Human Review Queue with Server-Side Guard.
              </div>
            </div>
            <button
              onClick={onClose}
              className="bg-cyan-500 text-slate-950 px-6 py-2 rounded-xl font-bold text-xs"
            >
              Go to Human Review Workspace
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
