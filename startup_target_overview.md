# Marajet / Algolyra — Startup Target & Business Overview

This document outlines the core business vision, strategic market analysis, financial objectives, legal foundations, and high-yield operational blueprint for **Marajet (Algolyra)**. 

The primary business target of Marajet is to raise cargo claim acceptance rates from the industry baseline of **30%–50%** up to **90%–95%**, turning cargo claim recovery into an automated, high-yield revenue stream for uninsured and self-insured freight brokers and 3PLs.

---

# PART I: Reaching a 90–95% Cargo Claim Acceptance Rate: The Marajet High-Yield Blueprint

**Author:** Manus AI  
**Date:** August 12, 2026  

---

## 1. Executive Strategy for 90–95% Acceptance

Achieving a **90% to 95% cargo claim acceptance rate**—a dramatic leap from the industry baseline of 30% to 50%—requires shifting Marajet from a reactive filing tool into an **undeniable, evidentiary fortress**. In the freight logistics industry, motor carriers and their third-party adjusters rely on standard "deny and delay" playbooks. They reject claims not necessarily because the loss didn't occur, but because the submitted claim package fails to meet strict legal and technical thresholds, giving them a contractual pretext for denial.

To hit 90–95%, Marajet must systematically eliminate every legal, procedural, and evidentiary loophole carriers exploit. This is achieved by enforcing **three foundational pillars**:

1. **Absolute Prima Facie Compliance** under the Carmack Amendment (49 U.S.C. § 14706).
2. **Preemptive Defenses Against Common Carrier Denials** (concealed damage, packaging, salvage retention).
3. **Automated Evidence Verification Loops** that block incomplete or vulnerable claims from ever reaching a carrier's desk.

---

## 2. Legal Foundation: Mastering the Carmack Amendment "Prima Facie" Standard

Under federal law, establishing a **prima facie case** places the legal burden of proof entirely onto the motor carrier. Once a claimant establishes a prima facie case, the carrier is legally liable unless it can prove the damage was caused by one of five narrow statutory exceptions (Act of God, public enemy, act of the shipper, public authority, or inherent vice of the goods).

To guarantee acceptance, Marajet’s automated ingestion engine must verify that every claim package indisputably proves the three core elements of a prima facie case:

* **Element 1: Delivery of goods to the carrier in good condition.** Proved by a clean Bill of Lading (BOL) bearing no exception notations at origin.
* **Element 2: Arrival of goods at destination in damaged/shorted condition or non-arrival.** Proved by exception notes on the Proof of Delivery (POD) receipt or a formal shortage declaration signed by the consignee and driver.
* **Element 3: Exact amount of actual damages.** Proved by commercial invoices, wholesale replacement cost documentation, and repair/salvage invoices.

If any of these three elements are missing or weakly supported, Marajet’s completeness engine must hold the claim in an `EVIDENCE_INCOMPLETE` state, preventing submission until the broker resolves the gap.

---

## 3. Systematic Elimination of Carrier Denial Triggers

Carriers routinely issue denials based on specific recurring pretexts. Marajet must preemptively neutralize each one:

| Carrier Denial Pretext | Root Cause & Carrier Argument | Marajet Preemptive Countermeasure |
| :--- | :--- | :--- |
| **"Unclean POD / Failure to Note Exception"** | The delivery receipt (POD) was signed clean ("delivered in good condition") without noting damage or shortage. | **Ingestion Guard:** AI scan compares BOL quantity/condition against POD. If POD is clean but damage is claimed later, the system instantly flags a **Concealed Damage Protocol**, prompting immediate carrier inspection scheduling within the strict 5-to-15-day window. |
| **"Failure to Protect Salvage"** | The consignee discarded damaged goods or packaging, preventing the carrier from inspecting or recovering salvage value. | **Mandatory Photo & Retention Check:** The workflow blocks claim generation unless photographic evidence explicitly shows damaged goods *retained* in their original packaging, accompanied by a digital sign-off confirming salvage storage. |
| **"Improper Packaging / Shipper Negligence"** | Carrier claims damage resulted from poor palletization, inadequate cushioning, or lack of shrink-wrap. | **Pre-Transit Visual Verification:** Ingest historical pre-loading photos or packaging specifications. If packaging was deficient, Marajet alerts the broker before transit or builds an incontrovertible counter-argument establishing that the carrier accepted the freight with full knowledge of packaging state. |
| **"Missed Filing Deadline"** | Claim submitted past the 9-month statutory Carmack window or shorter carrier tariff deadlines. | **Deterministic Deadline Engine:** Automatically calculates the exact expiration date based on delivery timestamps and carrier-specific tariff rules, triggering automated submission at least 30 days prior to expiry. |

---

## 4. Advanced Evidence Standards (VLM, OCR, and Metadata)

To push acceptance into the 90–95% bracket, Marajet cannot rely on basic text extraction alone. It must deploy advanced multimodal AI and metadata verification:

* **Image Forensics & Damage Grounding:** When damage photos are uploaded, Marajet’s vision-language models (VLM) must extract not just "damage," but structured observations (e.g., *puncture tear on outer corrugated box, crushing vector from top-left, wetness staining*). Every visual claim must be tethered to specific image coordinates and timestamp metadata.
* **Chain-of-Custody Timestamp Cross-Referencing:** Marajet must cross-reference GPS timestamps on tracking updates, electronic logging device (ELD) records, and warehouse gate-in/gate-out logs to prove precisely when and where the damage or shortage occurred, stripping carriers of the defense that damage happened *after* delivery.
* **Structured Claim Formatting:** Instead of unstructured email narratives, Marajet must generate standardized, legally rigorous claim packets formatted identically to enterprise claims management systems (conforming to NMFC Item 300105 minimum filing requirements), including itemized invoice breakdowns, formal demand language, and direct references to 49 U.S.C. § 14706.

---

## 5. The Marajet 95% High-Acceptance Workflow Architecture

To operationalize this strategy, Marajet’s pipeline must execute the following sequential gates:

```
[1. Shipment Ingestion]
        ↓
[2. Automated Prima Facie Check]
    ├── Clean Origin BOL? (Yes/No)
    ├── Exception Noted on POD? (Yes/No -> If No, trigger Concealed Damage clock)
    └── Invoice / Valuation Matched? (Yes/No)
        ↓
[3. Regulatory & Tariff Deadline Lock]
    └── Compute Carmack 9-month window AND carrier tariff rules (whichever is shorter)
        ↓
[4. Salvage & Packaging Compliance Gate]
    └── Verify photographic proof of damaged goods retention & packaging integrity
        ↓
[5. AI Evidence-Grounded Package Generation]
    └── Compile structured NMFC-compliant claim package with verified provenance
        ↓
[6. Human Senior Review & Approval]
    └── Broker signs off on high-confidence package
        ↓
[7. Automated Submission & Carrier Tracking]
    └── Target: 90-95% Instant Carrier Acceptance on First Submission
```

---

## 6. References (Blueprint)

1. Algolyra / Marajet. *Master Implementation Plan (v4)*. Internal Product Specification, 2026.
2. CXTMS. *Freight Claims Management Goes Digital: How AI Is Transforming Logistics Recovery*, February 2026.
3. United States Code. *49 U.S.C. § 14706 - The Carmack Amendment*. Federal Motor Carrier Safety Regulations.
4. Cozen O'Connor. *Cargo Claims: Ocean, Marine, and Inland Marine Subrogation and Recovery*, 2025.
5. National Motor Freight Traffic Association (NMFTA). *National Motor Freight Classification (NMFC) Rules on Concealed Damage*.
6. National Motor Freight Classification (NMFC) Item 300105. *Minimum Filing Requirements for Freight Claims*.
7. Partnership Transportation. *5 Frustrating Reasons Your Freight Claim Was Denied*, July 2025.

---

# PART II: Strategic Market and Product Analysis: Marajet (Cargo Claims Recovery Platform)

**Author:** Manus AI  
**Date:** August 12, 2026  

---

## 1. Executive Summary & Product Understanding

Based on a thorough review of the Marajet/Algolyra master implementation blueprint, the core product thesis is clear: Marajet serves as the specialized operating and recovery layer for freight cargo claims, targeting uninsured and self-insured freight brokers and third-party logistics (3PL) providers. The business model is strictly contingency-based (15–20% of successfully recovered dollars, with a zero fee on unrecovered claims). Operationally, Marajet uses modular artificial intelligence to automate document-heavy tasks—such as extracting facts from Bills of Lading (BOL), Proof of Delivery (POD) receipts, invoices, and damage photos—while strictly enforcing human-in-the-loop oversight for all high-stakes decisions, deadlines, and financial commitments.

While the baseline product architecture correctly prioritizes evidence-grounded extraction, deterministic rules for deadlines, and server-side human approval, deep industry research reveals critical vulnerabilities and lucrative expansion vectors that can significantly increase Marajet’s market power, recovery rates, and top-line revenue.

---

## 2. The Most Expensive Major Problem in the Freight Claims Industry

The single most expensive and pervasive problem facing freight brokers, 3PLs, and shippers in the cargo claims industry is the **catastrophic decay of recovery yields driven by administrative friction, missed statutory deadlines, and uncollected documentation gaps**.

Historically, freight claims suffer from a dismal baseline recovery rate of **30% to 50%**, leaving billions of dollars in damaged, lost, or shorted freight written off annually. For uninsured and self-insured mid-market brokers handling hundreds of shipments a month, pursuing small-to-mid-sized claims ($400 to $5,000) is economically unviable through manual workflows. Staff spend hours chasing documents across disparate carrier portals, resulting in administrative write-offs averaging **$15,000 to $20,000 per broker annually** in unpursued recovery.

Under federal freight liability frameworks such as the **Carmack Amendment** (49 U.S.C. § 14706), claimants have a strict federal minimum of **nine months from the date of delivery** (or expected delivery) to file a formal, legally compliant claim against a motor carrier. However, motor carrier tariffs and standard bill of lading contracts frequently impose even shorter notice periods—such as 5 to 15 days for concealed damage or loss. When brokers miss these microscopic windows due to manual lag or incomplete paperwork, carrier liability is legally extinguished, turning recoverable losses into permanent financial liabilities.

### Problem Dimension & Impact Matrix

| Problem Dimension | Traditional Manual Process | Marajet Automated Approach | Financial Impact / Cost |
| :--- | :--- | :--- | :--- |
| **Filing Window Compliance** | Tracked via spreadsheets or memory; frequently missed past 9-month Carmack or 5-day carrier tariff windows. | Deterministic rule engine calculates hard deadlines instantly upon ingestion. | Prevents 100% of deadline-based claim rejections. |
| **Documentation Incompleteness** | Missing exception notes on delivery receipts or lost photos lead to instant carrier denial. | Automated completeness checker flags missing evidence before submission. | Elevates baseline recovery yields from 30–50% to 70–85%. |
| **Small-Claim Abandonment** | Claims under $5,000 cost more in labor to file than their expected payout, leading to total write-offs. | AI automation compresses per-claim processing cost to near-zero. | Unlocks $15,000–$20,000 in previously abandoned recovery per broker annually. |

---

## 3. Other Major Problems During the Claims Lifecycle

Beyond missed deadlines and documentation gaps, industry research highlights four severe operational failure points that routinely sabotage cargo claims:

### A. Concealed Damage and the 5-Day Notification Trap
Concealed damage—where cargo is delivered intact on the outside but found damaged upon uncrating—is one of the most heavily contested claim types. Most motor carrier tariffs require written notice of concealed damage within **two to five business days** of delivery. Consignees frequently fail to notify brokers within this window, and carriers routinely deny liability under standard freight classification rules.

### B. Failure to Retain Damaged Freight (Salvage Duty)
Under established cargo claims law and freight governance (such as National Motor Freight Classification guidelines), the claimant and consignee have a legal duty to **mitigate damages and retain damaged goods** for carrier inspection. If a warehouse or consignee discards damaged freight before the carrier inspects it or waives inspection, carriers issue an immediate, unappealable denial based on "failure to protect salvage".

### C. Double-Brokering and Carrier Identity Mismatch
With the surge in fraudulent double-brokering schemes across North American freight markets, brokers often file claims against the "interline" or ghost carrier listed on the rate confirmation, only to discover that the physical transport was performed by an unverified third party whose active cargo insurance policy excludes the hauled commodity or has lapsed.

### D. Packaging vs. Carrier Negligence Disputes
Carriers aggressively reject cargo claims by invoking exceptions under the Carmack Amendment, specifically arguing that the damage resulted from **"act or default of the shipper,"** such as inadequate packaging, improper palletization, or poor load securement. Brokers lack the technical data to counter these boilerplate carrier pushbacks effectively.

---

## 4. Strategic Enhancements and High-Margin Additions for Marajet

To make Marajet significantly more powerful and unlock higher revenue streams per recovery, four strategic product modules and monetization extensions should be integrated into the roadmap:

### 1. Automated Salvage Valuation & Liquidation Module
* **The Problem:** Damaged goods often retain significant residual market value (e.g., electronics with scratched packaging, surplus goods). Brokers lack the time to broker salvage sales, resulting in total loss write-offs or excessive carrier salvage deductions.
* **The Solution:** Build a salvage management feature that estimates residual value using AI vision models on damage photos, connects with automated liquidation marketplaces or salvage buyers, and deducts salvage value accurately before claim submission.
* **Monetization Impact:** Instead of taking a contingency fee solely on recovered carrier payouts, Marajet can take an **additional platform fee or revenue share on liquidated salvage items**, turning a logistical headache into a dual-revenue stream.

### 2. Real-Time Carrier Insurance & Double-Brokering Verification Engine ("Marajet Risk Shield")
* **The Problem:** Successfully recovering a claim from a bankrupt, uninsured, or fraudulently impersonated carrier yields $0.
* **The Solution:** Integrate a pre-submission carrier compliance check that automatically queries motor carrier safety data (FMCSA/SAFER APIs) and active Certificate of Insurance (COI) databases at the moment a shipment is imported or a claim is initiated. If a carrier's insurance is lapsed or unverified, the system flags high collectibility risk.
* **Monetization Impact:** Position this as an elite risk-management tier ("Marajet Risk Shield"), charging a monthly SaaS subscription overlay or a higher contingency percentage (e.g., 22%) for high-risk carrier claims.

### 3. Tiered Contingency & Legal Escalation Partnerships
* **The Problem:** Carriers frequently reject initial valid claims (the "deny and wait" strategy), knowing that most brokers lack the legal resources to escalate to formal litigation or arbitration under the Carmack Amendment.
* **The Solution:** Introduce a **Tiered Contingency Structure**. For standard carrier responses, maintain the 15–20% contingency fee. For denied claims that require formal legal demand letters, litigation filing, or arbitration, partner with specialized freight law firms via a white-labeled API and charge a premium contingency rate of **30% to 35%** on recovered amounts.
* **Monetization Impact:** Substantially increases revenue on high-value disputed claims ($10,000+) without requiring internal legal headcount.

### 4. Proactive Statute & Tariff Guardian
* **The Problem:** Standard 9-month federal windows are well-known, but specific customer contracts, broker-carrier master service agreements (MSAs), and international multimodal waybills impose shorter contractual limitation periods (sometimes 60 to 180 days).
* **The Solution:** An advanced contract-parsing engine that ingests broker-carrier MSAs alongside the BOL to extract custom shorter limitation clauses, dynamically overriding standard statutory clocks.
* **Monetization Impact:** Eliminates the risk of catastrophic broker E&O (Errors & Omissions) liability, enabling Marajet to market itself not just as a recovery tool, but as an **insurance-grade risk mitigation platform**.

---

## 5. References (Strategic Analysis)

1. Algolyra / Marajet. *Master Implementation Plan (v4)*. Internal Product Specification, 2026.
2. CXTMS. *Freight Claims Management Goes Digital: How AI Is Transforming Logistics Recovery*, February 2026.
3. United States Code. *49 U.S.C. § 14706 - The Carmack Amendment*. Federal Motor Carrier Safety Regulations.
4. Logistics Plus. *6 Types of Freight Claims and 6 Reasons for Denial*, July 2020.
5. National Motor Freight Traffic Association (NMFTA). *National Motor Freight Classification (NMFC) Rules and Guidelines*.
6. GetTent. *Damaged Shipment & Freight Claims: Failure to Retain Damaged Freight*.
7. Reddit FreightBrokers Community. *What Are the Biggest Issues For Freight Brokers Today?*, May 2024.
8. Partnership Transportation. *5 Frustrating Reasons Your Freight Claim Was Denied*, July 2025.
