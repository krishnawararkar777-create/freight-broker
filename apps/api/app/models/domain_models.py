import datetime
from typing import Optional
from sqlalchemy import (
    String, Text, Float, Integer, Boolean, DateTime, ForeignKey, JSON, Index, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.session import Base

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(32), default="broker")  # broker|3pl|shipper|other
    status: Mapped[str] = mapped_column(String(32), default="active")
    timezone: Mapped[str] = mapped_column(String(64), default="America/New_York")
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    contingency_rate: Mapped[float] = mapped_column(Float, default=0.20)
    high_value_threshold: Mapped[float] = mapped_column(Float, default=5000.0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(64), default="Claims Manager")
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class CustomerPolicy(Base):
    __tablename__ = "customer_policies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), nullable=False, index=True)
    high_value_threshold: Mapped[float] = mapped_column(Float, default=5000.0)
    approval_policy_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    contingency_rate: Mapped[float] = mapped_column(Float, default=0.20)
    communication_policy: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    follow_up_policy: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="America/New_York")
    effective_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Carrier(Base):
    __tablename__ = "carriers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    aliases: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    mc_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    contact_channels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class CarrierRuleSet(Base):
    __tablename__ = "carrier_rule_sets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    carrier_id: Mapped[str] = mapped_column(String(64), ForeignKey("carriers.id"), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    effective_from: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    effective_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rule_status: Mapped[str] = mapped_column(String(32), default="active")
    source_reference: Mapped[str] = mapped_column(Text, nullable=False)
    verified_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class CarrierClaimRule(Base):
    __tablename__ = "carrier_claim_rules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    carrier_rule_set_id: Mapped[str] = mapped_column(String(64), ForeignKey("carrier_rule_sets.id"), nullable=False, index=True)
    claim_type: Mapped[str] = mapped_column(String(64), default="Cargo Damage")
    filing_window_type: Mapped[str] = mapped_column(String(64), default="Carmack")
    filing_window_value: Mapped[int] = mapped_column(Integer, default=9)
    filing_window_unit: Mapped[str] = mapped_column(String(32), default="months")
    required_document_type: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    submission_channel: Mapped[str] = mapped_column(String(64), default="email")
    special_rule_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), nullable=False, index=True)
    external_reference: Mapped[str] = mapped_column(String(128), index=True)
    bol_number: Mapped[str] = mapped_column(String(128), index=True)
    carrier_id: Mapped[str] = mapped_column(String(64), ForeignKey("carriers.id"), nullable=False, index=True)
    shipper_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    consignee_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    origin: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    destination: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pickup_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    declared_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    commodity: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), nullable=False, index=True)
    shipment_id: Mapped[str] = mapped_column(String(64), ForeignKey("shipments.id"), nullable=False, index=True)
    claim_type: Mapped[str] = mapped_column(String(64), default="Cargo Damage")  # Cargo Damage|Shortage|Lost Cargo
    status: Mapped[str] = mapped_column(String(64), default="DRAFT", index=True)  # DRAFT|UNDER_REVIEW|APPROVED|SUBMITTED|CLOSED
    lifecycle_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    claimed_amount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    approved_claim_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    deadline_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    concealed_deadline_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    lawsuit_deadline_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    human_threshold_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    elevated_approval_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    is_approved_by_human: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by_user_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("users.id"), nullable=True)
    reimbursement_mode: Mapped[str] = mapped_column(String(64), default="CHECK")
    owner_user_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    submitted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), nullable=False, index=True)
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("claims.id"), nullable=False, index=True)
    shipment_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("shipments.id"), nullable=True)
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)  # BOL|POD|Invoice|Photo
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), default="application/pdf")
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    extraction_status: Mapped[str] = mapped_column(String(32), default="uploaded")
    parser_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    uploaded_by: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DocumentEvidence(Base):
    __tablename__ = "document_evidence"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(64), ForeignKey("documents.id"), nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(Integer, default=1)
    bbox_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    source_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    field_name: Mapped[str] = mapped_column(String(128), nullable=False)
    normalized_value_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    extraction_method: Mapped[str] = mapped_column(String(64), default="LocalPdfParser")
    model_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    confidence: Mapped[float] = mapped_column(Float, default=1.0)


class ClaimFact(Base):
    __tablename__ = "claim_facts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("claims.id"), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    value_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    source_document_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("documents.id"), nullable=True)
    source_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    verification_status: Mapped[str] = mapped_column(String(32), default="extracted")  # extracted|edited_by_human|verified
    original_value_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    edited_by_user_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("users.id"), nullable=True)
    edited_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    edit_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ClaimRequirement(Base):
    __tablename__ = "claim_requirements"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("claims.id"), nullable=False, index=True)
    requirement_type: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_rule_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("carrier_claim_rules.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="missing")  # met|missing|unknown|waived
    evidence_document_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("documents.id"), nullable=True)


class ClaimSubmission(Base):
    __tablename__ = "claim_submissions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("claims.id"), nullable=False, index=True)
    submission_channel: Mapped[str] = mapped_column(String(64), default="email")
    submitted_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    external_reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="SUBMITTED")
    submitted_by: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), nullable=False)


class Communication(Base):
    __tablename__ = "communications"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("claims.id"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(32), default="email")
    direction: Mapped[str] = mapped_column(String(32), default="outbound")
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    draft_status: Mapped[str] = mapped_column(String(32), default="draft")
    approved_by: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("users.id"), nullable=True)
    sent_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_document_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("documents.id"), nullable=True)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("claims.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    owner_user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), nullable=False)
    due_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    priority: Mapped[str] = mapped_column(String(32), default="normal")
    created_by: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), nullable=False)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class RecoveryEvent(Base):
    __tablename__ = "recovery_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("claims.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    received_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    payment_reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    payer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    evidence_document_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("documents.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="recorded")
    created_by: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), nullable=False)


class FeeEvent(Base):
    __tablename__ = "fee_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("claims.id"), nullable=False, index=True)
    recovery_event_id: Mapped[str] = mapped_column(String(64), ForeignKey("recovery_events.id"), nullable=False, index=True)
    eligible_amount: Mapped[float] = mapped_column(Float, nullable=False)
    contingency_rate: Mapped[float] = mapped_column(Float, default=0.20)
    fee_amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[str] = mapped_column(String(32), default="unbilled")
    invoice_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), nullable=False, index=True)
    invoice_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    issue_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    due_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    tax: Mapped[float] = mapped_column(Float, default=0.0)
    total: Mapped[float] = mapped_column(Float, nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), nullable=False, index=True)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)  # HUMAN|AI|SYSTEM
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    before_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    after_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CarrierResponse(Base):
    __tablename__ = "carrier_responses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("claims.id"), nullable=False, index=True)
    document_id: Mapped[str] = mapped_column(String(64), ForeignKey("documents.id"), nullable=False, index=True)
    decision_type: Mapped[str] = mapped_column(String(64), nullable=False)  # ACCEPTANCE|PARTIAL_SETTLEMENT|DENIAL|INSPECTION_REQUEST
    carrier_claim_reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    offer_amount: Mapped[float] = mapped_column(Float, default=0.0)
    disputed_amount: Mapped[float] = mapped_column(Float, default=0.0)
    denial_reasons_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SalvageRecord(Base):
    __tablename__ = "salvage_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("claims.id"), nullable=False, unique=True, index=True)
    organization_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), nullable=False, index=True)
    commodity_category: Mapped[str] = mapped_column(String(64), nullable=False)
    damage_severity_score: Mapped[float] = mapped_column(Float, default=0.5)
    gross_invoice_value: Mapped[float] = mapped_column(Float, nullable=False)
    salvage_rate: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_salvage_value: Mapped[float] = mapped_column(Float, default=0.0)
    realized_salvage_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    net_claimed_amount: Mapped[float] = mapped_column(Float, nullable=False)
    disposition_status: Mapped[str] = mapped_column(String(32), default="PENDING_INSPECTION")  # DESTROYED|RETAINED_FOR_SALVAGE|SOLD_BY_CONSIGNEE|PENDING_INSPECTION
    disposition_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    storage_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    evidence_document_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("documents.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CarrierRiskFacts(Base):
    __tablename__ = "carrier_risk_facts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    carrier_id: Mapped[str] = mapped_column(String(64), ForeignKey("carriers.id"), nullable=False, unique=True, index=True)
    dot_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    mc_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dba_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    authority_status: Mapped[str] = mapped_column(String(32), default="ACTIVE")  # ACTIVE|INACTIVE|REVOKED|NONE
    common_authority_status: Mapped[Optional[str]] = mapped_column(String(32), default="ACTIVE")
    contract_authority_status: Mapped[Optional[str]] = mapped_column(String(32), default="ACTIVE")
    bipd_insurance_on_file: Mapped[float] = mapped_column(Float, default=1000000.0)
    cargo_insurance_on_file: Mapped[float] = mapped_column(Float, default=100000.0)
    cargo_policy_active: Mapped[bool] = mapped_column(Boolean, default=True)
    cargo_form_type: Mapped[Optional[str]] = mapped_column(String(32), default="BMC-34")  # BMC-34|BMC-91X
    insurance_effective_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    insurance_cancellation_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    safety_rating: Mapped[Optional[str]] = mapped_column(String(32), default="SATISFACTORY")  # SATISFACTORY|CONDITIONAL|UNSATISFACTORY|NOT_RATED
    out_of_service_rate_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_fmcsa_sync_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    raw_safer_data_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LegalEscalationRecord(Base):
    __tablename__ = "legal_escalation_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("claims.id"), nullable=False, unique=True, index=True)
    organization_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), nullable=False, index=True)
    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    escalation_tier_rate: Mapped[float] = mapped_column(Float, default=0.30)  # 0.30 to 0.35
    escalated_by_user_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("users.id"), nullable=True)
    escalated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    escalation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    current_milestone: Mapped[str] = mapped_column(String(64), default="PRE_LITIGATION")  # PRE_LITIGATION|DEMAND_LETTER_SENT|REFERRED_TO_COUNSEL|LAWSUIT_FILED|SETTLED|JUDGMENT_ENTERED
    milestone_updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    assigned_counsel_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    counsel_firm: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    case_file_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CarrierContractClause(Base):
    __tablename__ = "carrier_contract_clauses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    carrier_id: Mapped[str] = mapped_column(String(64), ForeignKey("carriers.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), nullable=False, index=True)
    contract_type: Mapped[str] = mapped_column(String(32), default="BROKER_CARRIER_MSA")  # BROKER_CARRIER_MSA|CARRIER_RULES_TARIFF|RATE_CON_TERMS
    contract_reference: Mapped[str] = mapped_column(String(128), nullable=False)
    effective_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expiration_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    filing_window_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # e.g. 60, 90, 120, 180, 270
    concealed_notice_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # e.g. 5, 15
    lawsuit_window_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # e.g. 365, 730
    released_rate_cap_per_lb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_liability_cap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    supersedes_carrier_tariff: Mapped[bool] = mapped_column(Boolean, default=True)
    clause_text_excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


from app.models.telemetry_model import APITelemetryLog





