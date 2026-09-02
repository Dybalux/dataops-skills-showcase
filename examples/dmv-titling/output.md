# dmv-titling-packet-verifier — Execution Evidence

**Date**: 2026-09-01  
**Target Transaction**: Texas & California Out-of-State Dealer Titling Packets  
**Tooling Used**: `.claude/skills/dmv-titling-packet-verifier/assets/verify_title_packet.py`  
**Violations Detected**: `VIN-CHK-001`, `ODO-FED-002`, `DMV-TX-003`, `DMV-FL-005`

---

## 1. Raw Ingested Titling Packet Payload (Hazardous / Non-Compliant)

```json
{
  "vin": "1FA6P8CF5H5100001",
  "state": "TX",
  "transaction_type": "Dealer Sale",
  "model_year": 2017,
  "odometer_miles": 45200,
  "odometer_status": "Exempt",
  "out_of_state": true,
  "has_lien": true,
  "lienholder": {
    "name": "Ally Financial"
  },
  "buyer": {
    "legal_name": "Jane Smith"
  },
  "bill_of_sale": {
    "buyer_name": "Jane Smith",
    "sale_price": 28000.0,
    "trade_in_allowance": 5000.0,
    "taxable_basis": 23000.0
  },
  "documents_present": [
    "Form 130-U (Application for Texas Title and/or Registration)"
  ]
}
```

---

## 2. Automated DMV Compliance Audit Report

```markdown
# DMV Titling Packet Audit Report: `1FA6P8CF5H5100001`

- **Jurisdiction**: TX | **Transaction Type**: Dealer Sale
- **Audit Status**: `REJECTED`
- **DMV Rejection Risk**: **Critical**

### 1. VIN Integrity & Identification
- **VIN**: `1FA6P8CF5H5100001` (Check Digit: INVALID)
- **Decoded Model Year**: 2017
- **Findings**: Check digit mismatch at position 9. Actual: '5', Calculated: '6'.

### 2. Federal Odometer Compliance (Truth in Mileage Act)
- **Reported Mileage**: 45,200 miles | **Brand Status**: Exempt
- **Applicable Rule**: Federal 20-Year Rolling Rule (NHTSA 49 CFR § 580.17). Mandatory disclosure until 2037.

### 3. State-Specific DMV Checklist (TX)
- [x] Form 130-U (Application for Texas Title and/or Registration)
- [ ] VI-30-A (Safety & VIN Inspection Certificate)

### 4. Cross-Document Reconciliation
- **Buyer Entity Match**: MATCH
- **Financial / Tax Calculation**: VALID
- **Lienholder & ELT Validation**: MISSING_ELT

### Rejection Hazards Detected
- ❌ **VIN Integrity: Check digit mismatch at position 9. Actual: '5', Calculated: '6'.**
- ❌ **REJECTION HAZARD: Vehicle is Model Year 2017 and cannot be marked 'Exempt' until 2037 (Federal 20-Year Rolling Rule (NHTSA 49 CFR § 580.17). Mandatory disclosure until 2037.).**
- ❌ **Out-of-State Transfer: Missing mandatory inspection form 'VI-30-A (Safety & VIN Inspection Certificate)' (FM-5).**
- ❌ **Lienholder ELT: State of TX requires an Electronic Lien and Title (ELT) code for institutional lenders (FM-3).**

### 5. Actionable Remediations
1. Fix blocker: VIN Integrity: Check digit mismatch at position 9. Actual: '5', Calculated: '6'.
2. Fix blocker: REJECTION HAZARD: Vehicle is Model Year 2017 and cannot be marked 'Exempt' until 2037 (Federal 20-Year Rolling Rule (NHTSA 49 CFR § 580.17). Mandatory disclosure until 2037.).
3. Fix blocker: Out-of-State Transfer: Missing mandatory inspection form 'VI-30-A (Safety & VIN Inspection Certificate)' (FM-5).
4. Fix blocker: Lienholder ELT: State of TX requires an Electronic Lien and Title (ELT) code for institutional lenders (FM-3).
```

---

## 3. Remediated & Compliant Packet Audit

```json
{
  "vin": "1FA6P8CF6H5100001",
  "state": "TX",
  "transaction_type": "Dealer Sale",
  "model_year": 2017,
  "odometer_miles": 45200,
  "odometer_status": "Actual",
  "out_of_state": true,
  "has_lien": true,
  "lienholder": {
    "name": "Ally Financial",
    "elt_code": "0012345678"
  },
  "buyer": {
    "legal_name": "Jane Smith"
  },
  "bill_of_sale": {
    "buyer_name": "Jane Smith",
    "sale_price": 28000.0,
    "trade_in_allowance": 5000.0,
    "taxable_basis": 23000.0
  },
  "documents_present": [
    "Form 130-U (Application for Texas Title and/or Registration)",
    "VI-30-A (Safety & VIN Inspection Certificate)",
    "Texas Sales Tax Declaration"
  ]
}
```

### Verified Audit Output:

```markdown
# DMV Titling Packet Audit Report: `1FA6P8CF6H5100001`

- **Jurisdiction**: TX | **Transaction Type**: Dealer Sale
- **Audit Status**: `PASSED`
- **DMV Rejection Risk**: **None**

### 1. VIN Integrity & Identification
- **VIN**: `1FA6P8CF6H5100001` (Check Digit: Valid)
- **Decoded Model Year**: 2017
- **Findings**: VIN check digit is valid.

### 2. Federal Odometer Compliance (Truth in Mileage Act)
- **Reported Mileage**: 45,200 miles | **Brand Status**: Actual
- **Applicable Rule**: Federal 20-Year Rolling Rule (NHTSA 49 CFR § 580.17). Mandatory disclosure until 2037.

### 3. State-Specific DMV Checklist (TX)
- [x] Form 130-U (Application for Texas Title and/or Registration)
- [x] VI-30-A (Safety & VIN Inspection Certificate)
- [x] ELT Code (0012345678)

### 4. Cross-Document Reconciliation
- **Buyer Entity Match**: MATCH
- **Financial / Tax Calculation**: VALID
- **Lienholder & ELT Validation**: VERIFIED

### 5. Actionable Remediations
1. Title packet is verified and ready for DMV electronic/physical submission.
```
