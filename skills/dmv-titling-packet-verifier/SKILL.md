---
name: dmv-titling-packet-verifier
description: "Trigger: dmv title, title packet, vehicle registration rules, titling checklist, dmv compliance, odometer disclosure, vin check digit, title audit, title verification, dmv packet. Statically and dynamically audit vehicle titling and registration packets across state DMVs (TX, CA, FL, NY, etc.), validating VIN check digits, federal odometer compliance, state-specific forms, and cross-document integrity."
license: Apache-2.0
metadata:
  author: "dybalux"
  version: "1.0"
---

# Activation Contract

Activate when a Business Operations analyst, Data Operations agent, or engineer reviews, audits, or validates a vehicle titling and registration packet, checks DMV submission prerequisites, validates a 17-character VIN, evaluates odometer disclosure rules, or needs state-specific DMV compliance checklists.

```
Trigger keywords: dmv title, title packet, vehicle registration rules, titling checklist, dmv compliance, odometer disclosure, vin check digit, title audit, title verification, dmv packet
```

# Hard Rules

- **Deterministic VIN Verification**: Every 17-character VIN for model year 1981+ must pass the ISO 3779 / NHTSA (49 CFR Part 565) mod-11 check-digit calculation. Characters `I`, `O`, and `Q` are strictly illegal.
- **Truth in Mileage Act Rule Enforcement**: Apply the federal 20-year rolling odometer disclosure rule for model years 2011 and newer. Vehicles 2010 and older follow the legacy 10-year rule.
- **Zero Inconsistent State Filings**: Any packet missing state-mandatory primary forms (e.g., TX `130-U`, CA `REG 343`, FL `HSMV 82040`, NY `MV-82`) must fail audit before submission.
- **Strict Lienholder ELT Matching**: If a transaction includes a lien in an ELT-mandated state (e.g., Florida, Texas, California), the Electronic Lien and Title (ELT) code and full lienholder legal address must be verified.
- **Cross-Entity Consistency**: Buyer legal name, purchase price, trade-in allowance, and odometer reading must match exactly across the Bill of Sale, Title Application, and Odometer Disclosure. Discrepancies block submission.
- **Power of Attorney (POA) Enforcement**: If a dealership or third party executes title documentation on behalf of the buyer or seller, a dedicated secure POA form is mandatory.

# Decision Gates

| Jurisdiction & Rule | Hazardous / Rejection Pattern | Prescribed Safe Standard |
| :--- | :--- | :--- |
| **VIN Integrity (Federal)** | Typo in 17-char VIN or check digit mismatch at pos 9 | Execute mod-11 check-digit verification; reject illegal chars (`I`, `O`, `Q`) |
| **Odometer Disclosure (Federal)** | Marking a 2015 vehicle as "Exempt" in 2026 | Require explicit mileage reading under the 20-year federal rolling rule (2011+ model years) |
| **Texas (TX DMV)** | Missing Form `130-U` or missing Lienholder ELT code | Require completed Form `130-U`, Sales Tax declaration, and certified 10-digit ELT ID if financed |
| **California (CA DMV)** | Missing `REG 343` / `REG 262` or missing Smog Check (>4 yrs) | Enforce `REG 343` application, `REG 262` secure disclosure, and smog certification verification |
| **Florida (FL FLHSMV)** | Out-of-state vehicle submitted without physical VIN inspection | Mandate Form `HSMV 82040` + physical inspection verification via Form `HSMV 82042` |
| **New York (NY NYSDMV)** | Missing `MV-82` or lien filing without `MV-900` | Require `MV-82`, `MV-900` lien filing notice, and `DTF-802` tax statement |

# Execution Steps

1. **Ingest & Parse Titling Payload**
   - Ingest the transaction JSON payload or document field map representing the title packet.
   - Extract VIN, State, Model Year, Transaction Type (`Dealer Sale`, `Private Sale`, `Lease Buyout`, `Refinance`), Odometer, Buyer/Seller Info, and Lienholder details.

2. **Execute VIN Structural & Check Digit Validation**
   - Run the ISO 3779 / NHTSA check digit algorithm (using `assets/verify_title_packet.py` or inline verification).
   - Validate character length (17 chars), absence of forbidden letters (`I`, `O`, `Q`), and verify position 10 model year consistency.

3. **Verify Odometer Disclosure & Mileage Integrity**
   - Calculate exemption status based on model year vs current transaction year under the 2021 NHTSA rule (20-year rolling threshold).
   - Validate odometer brand status (`Actual`, `Exempt`, `Exceeds Mechanical Limits`, `Warning: Odometer Discrepancy`).
   - If historical mileage is supplied, verify current odometer >= historical odometer (flagging rollback anomalies).

4. **Audit State-Specific Form Requirements**
   - Match transaction state (`TX`, `CA`, `FL`, `NY`, etc.) against required document checklist.
   - Verify presence of mandatory state title applications and supplementary forms.
   - If financed, verify required ELT codes and lienholder address format.
   - If out-of-state transfer, verify presence of state physical VIN verification forms.

5. **Execute Cross-Document Entity Reconciliation**
   - Check Buyer Legal Name across Bill of Sale vs Title Application.
   - Check Net Purchase Price calculation: `Net Price = Total Price - Trade-in Allowance`.
   - Verify Power of Attorney (POA) presence if representative signatures are detected.

6. **Generate DMV Audit Compliance Report**
   - Emit a structured audit report with status `PASSED`, `WARNING`, or `REJECTED`, detailing specific rejection risks and actionable remediation instructions.

# Output Contract

Audits must produce a structured Markdown report conforming to this schema:

```markdown
# DMV Titling Packet Audit Report: [VIN]

- **Jurisdiction**: [State Code] | **Transaction Type**: [Type]
- **Audit Status**: [PASSED | WARNING | REJECTED]
- **DMV Rejection Risk**: [None | Low | High | Critical]

### 1. VIN Integrity & Identification
- **VIN**: `[17-char VIN]` (Check Digit Pos 9: [Valid | Invalid])
- **Decoded Model Year**: [Year] | **Make/Model**: [Make / Model]
- **Findings**: [Details]

### 2. Federal Odometer Compliance (Truth in Mileage Act)
- **Reported Mileage**: [Miles] | **Brand Status**: [Actual | Exempt | Discrepancy]
- **Exemption Rule Applied**: [20-Year Rolling (2011+) | 10-Year Legacy (<=2010)]
- **Findings**: [Details]

### 3. State-Specific DMV Checklist ([State])
- [x] [Mandatory Primary Form (e.g. TX 130-U, CA REG 343)]
- [ ] [Mandatory Secondary Form / Lien Notice (e.g. FL HSMV 82042)]
- [x] [Sales Tax / Fee Declaration]

### 4. Cross-Document Reconciliation
- **Buyer Entity Match**: [MATCH | MISMATCH]
- **Financial / Tax Calculation**: [VALID | DISCREPANCY]
- **Lienholder & ELT Validation**: [VERIFIED | MISSING_ELT]

### 5. Actionable Remediations
1. [Step-by-step fix for any failed check before DMV submission]
```

# Failure Modes

- **FM-1: Pre-1981 Classic Vehicle Check Digit False Rejection**:
  * *Root Cause*: Attempting standard 17-character ISO 3779 check-digit validation on pre-1981 vehicles (which had non-standard 11-15 character VINs).
  * *Mitigation*: Check model year or length before check-digit validation. If length < 17 and year < 1981, classify as legacy classic VIN and verify physical title inspection requirement instead.
- **FM-2: Misapplying Legacy 10-Year Odometer Exemption to Post-2010 Vehicles**:
  * *Root Cause*: Treating a 2012 vehicle as exempt after 10 years (2022).
  * *Mitigation*: Enforce NHTSA 49 CFR § 580.17 amendment: 2011+ model year vehicles must capture actual odometer disclosures for 20 years.
- **FM-3: Missing Mandatory Electronic Lien and Title (ELT) Code**:
  * *Root Cause*: Submitting paper lienholder details in states where electronic titling is strictly mandated for institutional lenders (e.g. Florida, California).
  * *Mitigation*: Validate state-specific lender ELT ID database; flag submission as `REJECTED` if ELT ID is omitted when a financial institution is named as lienholder.
- **FM-4: Entity / Name Mismatch between Bill of Sale and Title**:
  * *Root Cause*: Buyer listed as individual on Bill of Sale (e.g. "John Doe") but titling under LLC (e.g. "Doe Logistics LLC") without reassignment or dealer documentation.
  * *Mitigation*: Cross-check buyer string similarity; require business authorization / reassignment document if purchaser and titleholder names diverge.
- **FM-5: Out-of-State Title Missing Physical VIN Verification**:
  * *Root Cause*: Transferring out-of-state vehicle without physical inspection form (e.g. FL `HSMV 82042`, CA `REG 31`).
  * *Mitigation*: Flag any `out_of_state: true` packet missing certified law enforcement / DMV physical VIN verification form.
