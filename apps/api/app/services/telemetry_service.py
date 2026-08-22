import os
import sys
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.models.telemetry_model import APITelemetryLog
from app.models.domain_models import Document, DocumentEvidence, ClaimFact, AuditEvent


class TelemetryService:
    """
    Production Telemetry Service for calculating system performance,
    API latency percentiles, OCR extraction accuracy across all 3 parsers,
    and human-in-the-loop edit diff analytics.
    """

    @staticmethod
    def _calculate_percentile(values: List[float], percentile: float) -> float:
        """Deterministic percentile calculation with linear interpolation."""
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        k = (len(sorted_vals) - 1) * (percentile / 100.0)
        f = int(k)
        c = min(f + 1, len(sorted_vals) - 1)
        d = k - f
        return round(sorted_vals[f] + d * (sorted_vals[c] - sorted_vals[f]), 2)

    def get_api_metrics(
        self,
        db: Session,
        org_id: Optional[str] = None,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Calculates request counts, error rates, and P50/P95/P99 latency percentiles."""
        query = db.query(APITelemetryLog)
        if org_id:
            query = query.filter(APITelemetryLog.organization_id == org_id)

        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=time_window_hours)
        query = query.filter(APITelemetryLog.created_at >= cutoff)

        logs: List[APITelemetryLog] = query.all()
        total_requests = len(logs)

        if total_requests == 0:
            return {
                "total_requests": 0,
                "successful_requests": 0,
                "error_requests": 0,
                "error_rate_pct": 0.0,
                "avg_latency_ms": 0.0,
                "p50_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
                "status_code_distribution": {},
                "heavy_endpoints": {},
            }

        latencies = [log.latency_ms for log in logs]
        successful_requests = sum(1 for log in logs if log.status_code < 400)
        error_requests = total_requests - successful_requests
        error_rate_pct = round((error_requests / total_requests) * 100.0, 2)
        avg_latency = round(sum(latencies) / total_requests, 2)

        # Status code breakdown
        status_dist: Dict[int, int] = {}
        for log in logs:
            status_dist[log.status_code] = status_dist.get(log.status_code, 0) + 1

        # Heavy processing endpoints breakdown
        heavy_paths = ["/documents/upload", "/edi/", "/tms/", "/package", "/rebuttal"]
        heavy_endpoints: Dict[str, Any] = {}
        for h_key in heavy_paths:
            matching_logs = [log for log in logs if h_key in log.endpoint_path]
            if matching_logs:
                m_latencies = [m.latency_ms for m in matching_logs]
                heavy_endpoints[h_key] = {
                    "count": len(matching_logs),
                    "avg_latency_ms": round(sum(m_latencies) / len(matching_logs), 2),
                    "p95_latency_ms": self._calculate_percentile(m_latencies, 95.0),
                }

        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "error_requests": error_requests,
            "error_rate_pct": error_rate_pct,
            "avg_latency_ms": avg_latency,
            "p50_latency_ms": self._calculate_percentile(latencies, 50.0),
            "p95_latency_ms": self._calculate_percentile(latencies, 95.0),
            "p99_latency_ms": self._calculate_percentile(latencies, 99.0),
            "status_code_distribution": status_dist,
            "heavy_endpoints": heavy_endpoints,
        }

    def get_extraction_accuracy(
        self,
        db: Session,
        org_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Computes extraction accuracy rates per document type and per parser type
        (tracking LocalPdfParser, PaddlePdfParser, and LlmVisionParser).
        """
        ev_query = db.query(DocumentEvidence)
        doc_query = db.query(Document)

        if org_id:
            doc_query = doc_query.filter(Document.organization_id == org_id)
            doc_ids = [d.id for d in doc_query.all()]
            ev_query = ev_query.filter(DocumentEvidence.document_id.in_(doc_ids))

        evidences: List[DocumentEvidence] = ev_query.all()
        documents: List[Document] = doc_query.all()

        total_docs = len(documents)
        processed_docs = sum(1 for d in documents if d.extraction_status == "processed")
        schema_pass_rate = round((processed_docs / total_docs * 100.0), 2) if total_docs > 0 else 100.0

        # Parser breakdown initialization for all 3 supported parsers
        parser_stats: Dict[str, Dict[str, Any]] = {
            "LocalPdfParser": {"field_count": 0, "high_confidence": 0, "confidences": []},
            "PaddlePdfParser": {"field_count": 0, "high_confidence": 0, "confidences": []},
            "LlmVisionParser": {"field_count": 0, "high_confidence": 0, "confidences": []},
        }

        # Document type breakdown
        doc_type_map = {d.id: d.document_type for d in documents}
        doc_type_stats: Dict[str, Dict[str, Any]] = {}

        for ev in evidences:
            method = ev.extraction_method or "LocalPdfParser"
            # Normalize parser name to standard taxonomy
            if "Paddle" in method or "PP-OCR" in method:
                canonical_parser = "PaddlePdfParser"
            elif "Vision" in method or "LLM" in method or "VLM" in method:
                canonical_parser = "LlmVisionParser"
            else:
                canonical_parser = "LocalPdfParser"

            if canonical_parser not in parser_stats:
                parser_stats[canonical_parser] = {"field_count": 0, "high_confidence": 0, "confidences": []}

            parser_stats[canonical_parser]["field_count"] += 1
            parser_stats[canonical_parser]["confidences"].append(ev.confidence or 0.0)
            if (ev.confidence or 0.0) >= 0.85:
                parser_stats[canonical_parser]["high_confidence"] += 1

            # Document type grouping
            dtype = doc_type_map.get(ev.document_id, "OTHER")
            if dtype not in doc_type_stats:
                doc_type_stats[dtype] = {"total_fields": 0, "high_confidence_fields": 0, "confidences": []}
            doc_type_stats[dtype]["total_fields"] += 1
            doc_type_stats[dtype]["confidences"].append(ev.confidence or 0.0)
            if (ev.confidence or 0.0) >= 0.85:
                doc_type_stats[dtype]["high_confidence_fields"] += 1

        # Format parser results
        by_parser: Dict[str, Any] = {}
        for p_name, stats in parser_stats.items():
            cnt = stats["field_count"]
            avg_conf = round(sum(stats["confidences"]) / cnt, 3) if cnt > 0 else 0.0
            acc_pct = round((stats["high_confidence"] / cnt) * 100.0, 2) if cnt > 0 else 100.0
            by_parser[p_name] = {
                "field_count": cnt,
                "avg_confidence": avg_conf,
                "accuracy_rate_pct": acc_pct,
            }

        # Format document type results
        by_doc_type: Dict[str, Any] = {}
        for dtype, stats in doc_type_stats.items():
            cnt = stats["total_fields"]
            avg_conf = round(sum(stats["confidences"]) / cnt, 3) if cnt > 0 else 0.0
            acc_pct = round((stats["high_confidence_fields"] / cnt) * 100.0, 2) if cnt > 0 else 100.0
            by_doc_type[dtype] = {
                "total_fields": cnt,
                "avg_confidence": avg_conf,
                "accuracy_rate_pct": acc_pct,
            }

        return {
            "total_documents": total_docs,
            "processed_documents": processed_docs,
            "schema_validation_pass_rate_pct": schema_pass_rate,
            "total_extracted_fields": len(evidences),
            "by_parser": by_parser,
            "by_document_type": by_doc_type,
        }

    def get_human_edit_diffs(
        self,
        db: Session,
        org_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyzes human fact edits from claim_facts and audit_events,
        measuring intervention frequencies and numeric deltas.
        """
        facts_query = db.query(ClaimFact)
        all_facts: List[ClaimFact] = facts_query.all()
        total_facts = len(all_facts)

        edited_facts = [f for f in all_facts if f.verification_status == "edited_by_human"]
        edited_count = len(edited_facts)

        intervention_rate = round((edited_count / total_facts * 100.0), 2) if total_facts > 0 else 0.0

        # Frequency breakdown by field
        field_frequencies: Dict[str, int] = {}
        for f in edited_facts:
            field_frequencies[f.field_name] = field_frequencies.get(f.field_name, 0) + 1

        # Audit events diffs
        audit_query = db.query(AuditEvent).filter(
            AuditEvent.action.in_(["FACT_EDITED_BY_HUMAN", "FACT_UPDATED", "FACT_OVERRIDDEN"])
        )
        if org_id:
            audit_query = audit_query.filter(AuditEvent.organization_id == org_id)

        audit_events: List[AuditEvent] = audit_query.all()

        return {
            "total_facts": total_facts,
            "edited_facts_count": edited_count,
            "human_intervention_rate_pct": intervention_rate,
            "field_edit_frequencies": field_frequencies,
            "total_audit_edit_events": len(audit_events),
        }
