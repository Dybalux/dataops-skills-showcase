#!/usr/bin/env python3
"""
DMV Title Packet & Compliance Verification Engine.
Audits vehicle titling packets across US state DMVs, validating VIN check digits,
federal odometer compliance (Truth in Mileage Act), state-specific forms, and
cross-document entity integrity.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Tuple

# VIN Transliteration Values (ISO 3779 / NHTSA 49 CFR Part 565)
VIN_CHAR_VALUES: Dict[str, int] = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "P": 7, "R": 9,
    "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9,
    "0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
}

VIN_POSITION_WEIGHTS: List[int] = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]

# Model Year Code Map (Pos 10) for 1980-2039
MODEL_YEAR_CODES: Dict[str, int] = {
    "A": 2010, "B": 2011, "C": 2012, "D": 2013, "E": 2014, "F": 2015, "G": 2016,
    "H": 2017, "J": 2018, "K": 2019, "L": 2020, "M": 2021, "N": 2022, "P": 2023,
    "R": 2024, "S": 2025, "T": 2026, "V": 2027, "W": 2028, "X": 2029, "Y": 2030,
    "1": 2001, "2": 2002, "3": 2003, "4": 2004, "5": 2005, "6": 2006, "7": 2007,
    "8": 2008, "9": 2009,
}

# US 50 States + DC full name to 2-letter postal code mapping
US_STATE_ALIASES: Dict[str, str] = {
    "TEXAS": "TX", "CALIFORNIA": "CA", "FLORIDA": "FL", "NEW YORK": "NY",
    "ILLINOIS": "IL", "PENNSYLVANIA": "PA", "OHIO": "OH", "GEORGIA": "GA",
    "NORTH CAROLINA": "NC", "MICHIGAN": "MI", "NEW JERSEY": "NJ", "VIRGINIA": "VA",
    "WASHINGTON": "WA", "ARIZONA": "AZ", "MASSACHUSETTS": "MA", "TENNESSEE": "TN",
    "INDIANA": "IN", "MISSOURI": "MO", "MARYLAND": "MD", "WISCONSIN": "WI",
    "COLORADO": "CO", "MINNESOTA": "MN", "SOUTH CAROLINA": "SC", "ALABAMA": "AL",
    "LOUISIANA": "LA", "KENTUCKY": "KY", "OREGON": "OR", "OKLAHOMA": "OK",
    "CONNECTICUT": "CT", "UTAH": "UT", "IOWA": "IA", "NEVADA": "NV",
    "ARKANSAS": "AR", "MISSISSIPPI": "MS", "KANSAS": "KS", "NEW MEXICO": "NM",
    "NEBRASKA": "NE", "IDAHO": "ID", "WEST VIRGINIA": "WV", "HAWAII": "HI",
    "NEW HAMPSHIRE": "NH", "MAINE": "ME", "MONTANA": "MT", "RHODE ISLAND": "RI",
    "DELAWARE": "DE", "SOUTH DAKOTA": "SD", "NORTH DAKOTA": "ND", "ALASKA": "AK",
    "VERMONT": "VT", "WYOMING": "WY", "DISTRICT OF COLUMBIA": "DC",
}

STATE_CHECKLISTS: Dict[str, Dict[str, Any]] = {
    "TX": {
        "primary_form": "Form 130-U (Application for Texas Title and/or Registration)",
        "primary_code": "130-U",
        "secondary_forms": ["Texas Sales Tax Declaration"],
        "elt_mandatory": True,
        "out_of_state_inspection": "VI-30-A (Safety & VIN Inspection Certificate)",
        "out_of_state_code": "VI-30-A",
    },
    "CA": {
        "primary_form": "REG 343 (Application for Title or Registration)",
        "primary_code": "REG 343",
        "secondary_forms": ["REG 262 (Vehicle Transfer and Reassignment / Odometer)"],
        "elt_mandatory": True,
        "smog_required_years": 4,
        "out_of_state_inspection": "REG 31 (Verification of Vehicle)",
        "out_of_state_code": "REG 31",
    },
    "FL": {
        "primary_form": "HSMV 82040 (Application for Certificate of Motor Vehicle Title)",
        "primary_code": "HSMV 82040",
        "secondary_forms": ["Bill of Sale with Sales Tax Recapitulation"],
        "elt_mandatory": True,
        "out_of_state_inspection": "HSMV 82042 (VIN and Odometer Physical Verification)",
        "out_of_state_code": "HSMV 82042",
    },
    "NY": {
        "primary_form": "MV-82 (Vehicle Registration/Title Application)",
        "primary_code": "MV-82",
        "secondary_forms": ["DTF-802 (Statement of Transaction for Sales Tax)"],
        "lien_form": "MV-900 (Notice of Recorded Lien)",
        "lien_code": "MV-900",
        "elt_mandatory": False,
        "out_of_state_inspection": "MV-82 with Certified VIN Tracing",
        "out_of_state_code": "MV-82",
    },
}


def doc_matches_form(form_code: str, docs: Iterable[str]) -> bool:
    """Matches a specific state form code against attached document labels using word boundaries."""
    pattern = r"\b" + re.escape(form_code).replace(r"\ ", r"\s+") + r"\b"
    return any(bool(re.search(pattern, str(doc), re.IGNORECASE)) for doc in docs)


def validate_vin(vin: Optional[str], model_year: Optional[int] = None) -> Tuple[bool, str, Optional[str], Optional[int]]:
    """
    Validates a VIN using ISO 3779 / NHTSA mod-11 check-digit algorithm.
    Handles pre-1981 classic vehicle VINs (<17 chars) according to FM-1.
    Returns: (is_valid, message, expected_check_digit, decoded_year)
    """
    raw_vin = str(vin or "").strip().upper()
    if not raw_vin:
        return False, "VIN is missing or empty.", None, None

    if len(raw_vin) < 17:
        if model_year and model_year < 1981:
            return True, f"Pre-1981 classic vehicle ({model_year}) with {len(raw_vin)}-character VIN. ISO 3779 check digit waived; physical title verification mandatory (FM-1).", None, model_year
        return False, f"VIN has {len(raw_vin)} characters. 17 characters required for 1981+ vehicles; classic pre-1981 requires explicit model_year < 1981 (FM-1).", None, None

    if len(raw_vin) > 17:
        return False, f"VIN has {len(raw_vin)} characters (maximum 17 allowed).", None, None

    illegal_chars = [c for c in raw_vin if c in ("I", "O", "Q")]
    if illegal_chars:
        return False, f"Illegal characters detected: {', '.join(sorted(set(illegal_chars)))}. VINs cannot contain I, O, or Q.", None, None

    weighted_sum = 0
    for idx, char in enumerate(raw_vin):
        if char not in VIN_CHAR_VALUES:
            return False, f"Invalid character '{char}' in VIN.", None, None
        weighted_sum += VIN_CHAR_VALUES[char] * VIN_POSITION_WEIGHTS[idx]

    remainder = weighted_sum % 11
    expected_check_digit = "X" if remainder == 10 else str(remainder)
    actual_check_digit = raw_vin[8]

    # Decode Year from position 10
    pos_10 = raw_vin[9]
    decoded_year = MODEL_YEAR_CODES.get(pos_10)

    if actual_check_digit != expected_check_digit:
        return (
            False,
            f"Check digit mismatch at position 9. Actual: '{actual_check_digit}', Calculated: '{expected_check_digit}'.",
            expected_check_digit,
            decoded_year,
        )

    return True, "VIN check digit is valid.", expected_check_digit, decoded_year


def evaluate_odometer(model_year: int, reported_mileage: int, status: str, current_year: Optional[int] = None) -> Tuple[str, List[str]]:
    """
    Evaluates Federal Truth in Mileage Act odometer disclosure compliance.
    2011+ vehicles require disclosure for 20 years. <=2010 vehicles use legacy 10-year rule.
    """
    if current_year is None:
        current_year = date.today().year

    findings: List[str] = []
    status_clean = str(status or "").strip()
    status_lower = status_clean.lower()

    if model_year >= 2011:
        exemption_year = model_year + 20
        rule_desc = f"Federal 20-Year Rolling Rule (NHTSA 49 CFR § 580.17). Mandatory disclosure until {exemption_year}."
    else:
        exemption_year = model_year + 10
        rule_desc = f"Legacy 10-Year Rule. Mandatory disclosure until {exemption_year}."

    is_exempt_by_age = current_year >= exemption_year

    valid_statuses = {
        "actual": "Actual",
        "exempt": "Exempt",
        "exceeds mechanical limits": "Exceeds Mechanical Limits",
        "discrepancy": "Discrepancy",
        "warning: odometer discrepancy": "Warning: Odometer Discrepancy",
    }

    if status_lower not in valid_statuses:
        findings.append(f"Invalid Odometer Status '{status_clean}'. Must be Actual, Exempt, Exceeds Mechanical Limits, or Discrepancy.")
    elif status_lower == "exempt":
        if not is_exempt_by_age:
            findings.append(
                f"REJECTION HAZARD: Vehicle is Model Year {model_year} and cannot be marked 'Exempt' until {exemption_year} ({rule_desc})."
            )

    try:
        mileage_val = int(reported_mileage)
        if mileage_val < 0:
            findings.append("Reported mileage cannot be negative.")
    except (TypeError, ValueError):
        findings.append(f"Invalid reported mileage value: '{reported_mileage}'. Must be a valid integer.")

    return rule_desc, findings


def audit_title_packet(packet: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Audits a complete DMV Title Packet payload against Federal and State compliance rules.
    """
    violations: List[str] = []
    warnings: List[str] = []
    checklist_status: Dict[str, bool] = {}

    data = packet or {}

    vin = str(data.get("vin") or "").strip().upper()
    raw_state = str(data.get("state") or "").strip().upper()
    state = US_STATE_ALIASES.get(raw_state, raw_state)
    if not state or len(state) != 2 or not state.isalpha():
        violations.append(f"Invalid Jurisdiction Code '{raw_state}'. Must be a valid 2-letter US state code.")

    transaction_type = str(data.get("transaction_type") or "Dealer Sale").strip()

    raw_year = data.get("model_year")
    try:
        reported_year = int(raw_year) if raw_year is not None else None
    except (TypeError, ValueError):
        reported_year = None

    current_calendar_year = date.today().year
    if reported_year is not None:
        if reported_year < 1900 or reported_year > current_calendar_year + 1:
            violations.append(
                f"Model Year Anomaly: {reported_year} is outside realistic vehicle manufacturing boundaries (1900–{current_calendar_year + 1})."
            )

    try:
        odometer_miles = int(data.get("odometer_miles") or 0)
    except (TypeError, ValueError):
        odometer_miles = 0

    odometer_status = str(data.get("odometer_status") or "Actual")
    out_of_state = bool(data.get("out_of_state", False))
    has_lien = bool(data.get("has_lien", False))

    lienholder = data.get("lienholder") if isinstance(data.get("lienholder"), dict) else {}
    buyer = data.get("buyer") if isinstance(data.get("buyer"), dict) else {}
    bill_of_sale = data.get("bill_of_sale") if isinstance(data.get("bill_of_sale"), dict) else {}

    raw_docs = data.get("documents_present")
    documents_present = (
        [str(d).strip() for d in raw_docs if d is not None and str(d).strip()]
        if isinstance(raw_docs, (list, set, tuple))
        else []
    )

    # 1. VIN Validation
    vin_valid, vin_msg, expected_chk, decoded_year = validate_vin(vin, reported_year)
    if not vin_valid:
        violations.append(f"VIN Integrity: {vin_msg}")

    effective_year = reported_year or decoded_year or 2020

    # 2. Odometer Validation
    odo_rule, odo_findings = evaluate_odometer(effective_year, odometer_miles, odometer_status)
    violations.extend(odo_findings)

    # 3. State Checklist Verification
    state_rules = STATE_CHECKLISTS.get(state)
    if not state_rules:
        if len(state) == 2 and state.isalpha():
            warnings.append(f"State '{state}' not explicitly in rules matrix; standard AAMVA title application required.")
    else:
        primary_form = state_rules["primary_form"]
        primary_code = state_rules["primary_code"]
        has_primary = doc_matches_form(primary_code, documents_present)
        checklist_status[primary_form] = has_primary
        if not has_primary:
            violations.append(f"Missing State Primary Form: {primary_form}")

        # Out-of-state physical inspection check
        if out_of_state:
            inspection_form = state_rules.get("out_of_state_inspection", "Physical VIN Inspection Form")
            inspection_code = state_rules.get("out_of_state_code", "Inspection")
            has_insp = doc_matches_form(inspection_code, documents_present)
            checklist_status[inspection_form] = has_insp
            if not has_insp:
                violations.append(f"Out-of-State Transfer: Missing mandatory inspection form '{inspection_form}' (FM-5).")

        # ELT Check in ELT-mandated states
        if has_lien and state_rules.get("elt_mandatory"):
            elt_code = str(lienholder.get("elt_code") or "").strip()
            if not elt_code:
                violations.append(f"Lienholder ELT: State of {state} requires an Electronic Lien and Title (ELT) code for institutional lenders (FM-3).")
            else:
                checklist_status[f"ELT Code ({elt_code})"] = True

        # NY Lien Form check
        if has_lien and state == "NY":
            lien_form = state_rules.get("lien_form", "MV-900 (Notice of Recorded Lien)")
            lien_code = state_rules.get("lien_code", "MV-900")
            has_lien_doc = doc_matches_form(lien_code, documents_present)
            checklist_status[lien_form] = has_lien_doc
            if not has_lien_doc:
                violations.append(f"Missing Mandatory Lien Notice: {lien_form}")

    # 4. Cross-Document Reconciliation
    buyer_title_name = str(buyer.get("legal_name") or "").strip().lower()
    bos_buyer_name = str(bill_of_sale.get("buyer_name") or "").strip().lower()
    if buyer_title_name and bos_buyer_name and buyer_title_name != bos_buyer_name:
        violations.append(
            f"Entity Mismatch: Buyer name on Title Application ('{buyer.get('legal_name')}') does not match Bill of Sale ('{bill_of_sale.get('buyer_name')}') (FM-4)."
        )

    # Power of Attorney check
    representative_signatory = bool(data.get("representative_signatory", False))
    if representative_signatory:
        has_poa = any(bool(re.search(r"\b(POA|Power of Attorney)\b", str(doc), re.IGNORECASE)) for doc in documents_present)
        checklist_status["Secure Power of Attorney (POA)"] = has_poa
        if not has_poa:
            violations.append("Representative Execution: Missing mandatory Secure Power of Attorney form (POA).")

    # Financial & Tax calculation check
    if bill_of_sale:
        try:
            sale_price = float(bill_of_sale.get("sale_price") or 0.0)
            trade_in = float(bill_of_sale.get("trade_in_allowance") or 0.0)
            if sale_price < 0 or trade_in < 0:
                violations.append(
                    f"Financial Boundary Violation: Sale price (${sale_price:,.2f}) and trade-in allowance (${trade_in:,.2f}) cannot be negative."
                )
            taxable_basis_raw = bill_of_sale.get("taxable_basis")
            if taxable_basis_raw is not None:
                taxable_basis = float(taxable_basis_raw)
                expected_basis = max(0.0, sale_price - trade_in)
                if abs(taxable_basis - expected_basis) > 0.01:
                    violations.append(
                        f"Financial Discrepancy: Taxable basis (${taxable_basis:,.2f}) does not match Sale Price (${sale_price:,.2f}) minus Trade-in (${trade_in:,.2f})."
                    )
        except (TypeError, ValueError) as exc:
            violations.append(f"Financial Calculation Error: Malformed numerical values in bill of sale ({exc}).")

    # 5. Determine Overall Status
    if violations:
        status = "REJECTED"
        risk = "Critical"
    elif warnings:
        status = "WARNING"
        risk = "Low"
    else:
        status = "PASSED"
        risk = "None"

    return {
        "vin": vin,
        "state": state,
        "transaction_type": transaction_type,
        "status": status,
        "rejection_risk": risk,
        "model_year": effective_year,
        "odometer_miles": odometer_miles,
        "odometer_status": odometer_status,
        "vin_check_digit_valid": vin_valid,
        "vin_message": vin_msg,
        "odometer_rule": odo_rule,
        "violations": violations,
        "warnings": warnings,
        "checklist_status": checklist_status,
        "buyer_entity_match": "MATCH" if not any("Entity Mismatch" in v for v in violations) else "MISMATCH",
        "financial_match": "VALID" if not any("Financial" in v for v in violations) else "DISCREPANCY",
        "elt_validation": "VERIFIED" if not any("Lienholder ELT" in v for v in violations) else "MISSING_ELT",
    }


def format_markdown_report(result: Dict[str, Any]) -> str:
    """Renders the audit result conforming strictly to the 5-section schema in SKILL.md."""
    md = []
    md.append(f"# DMV Titling Packet Audit Report: `{result['vin']}`\n")
    md.append(f"- **Jurisdiction**: {result['state']} | **Transaction Type**: {result['transaction_type']}")
    md.append(f"- **Audit Status**: `{result['status']}`")
    md.append(f"- **DMV Rejection Risk**: **{result['rejection_risk']}**\n")

    md.append("### 1. VIN Integrity & Identification")
    chk_status = "Valid" if result["vin_check_digit_valid"] else "INVALID"
    md.append(f"- **VIN**: `{result['vin']}` (Check Digit: {chk_status})")
    md.append(f"- **Decoded Model Year**: {result['model_year']}")
    md.append(f"- **Findings**: {result['vin_message']}\n")

    md.append("### 2. Federal Odometer Compliance (Truth in Mileage Act)")
    md.append(f"- **Reported Mileage**: {result.get('odometer_miles', 0):,} miles | **Brand Status**: {result.get('odometer_status', 'Actual')}")
    md.append(f"- **Applicable Rule**: {result['odometer_rule']}\n")

    md.append(f"### 3. State-Specific DMV Checklist ({result['state']})")
    if result["checklist_status"]:
        for form, present in result["checklist_status"].items():
            mark = "[x]" if present else "[ ]"
            md.append(f"- {mark} {form}")
    else:
        md.append("- *(Standard checklist items applied)*")
    md.append("")

    md.append("### 4. Cross-Document Reconciliation")
    md.append(f"- **Buyer Entity Match**: {result.get('buyer_entity_match', 'MATCH')}")
    md.append(f"- **Financial / Tax Calculation**: {result.get('financial_match', 'VALID')}")
    md.append(f"- **Lienholder & ELT Validation**: {result.get('elt_validation', 'VERIFIED')}\n")

    if result["violations"]:
        md.append("### Rejection Hazards Detected")
        for v in result["violations"]:
            md.append(f"- ❌ **{v}**")
        md.append("")

    if result["warnings"]:
        md.append("### Warnings & Secondary Checks")
        for w in result["warnings"]:
            md.append(f"- ⚠️ {w}")
        md.append("")

    md.append("### 5. Actionable Remediations")
    if not result["violations"] and not result["warnings"]:
        md.append("1. Title packet is verified and ready for DMV electronic/physical submission.")
    else:
        idx = 1
        for v in result["violations"]:
            md.append(f"{idx}. Fix blocker: {v}")
            idx += 1
        for w in result["warnings"]:
            md.append(f"{idx}. Review warning: {w}")
            idx += 1

    return "\n".join(md)


def main() -> None:
    parser = argparse.ArgumentParser(description="DMV Titling Packet Verification Engine")
    parser.add_argument("--payload", type=str, help="Path to JSON titling packet file")
    parser.add_argument("--raw-json", type=str, help="Raw JSON string of titling packet")
    parser.add_argument("--vin", type=str, help="Quick standalone VIN check")
    parser.add_argument("--json-out", action="store_true", help="Output raw JSON instead of Markdown")

    args = parser.parse_args()

    if args.vin:
        valid, msg, exp, year = validate_vin(args.vin)
        res = {
            "vin": args.vin,
            "valid": valid,
            "message": msg,
            "expected_check_digit": exp,
            "decoded_year": year,
        }
        if args.json_out:
            print(json.dumps(res, indent=2))
        else:
            status = "VALID" if valid else "INVALID"
            print(f"VIN: {args.vin} | Status: {status} | Year: {year} | Details: {msg}")
        return

    packet: Dict[str, Any] = {}
    if args.payload:
        with open(args.payload, "r", encoding="utf-8") as f:
            packet = json.load(f)
    elif args.raw_json:
        packet = json.loads(args.raw_json)
    else:
        # Default sample if nothing passed
        packet = {
            "vin": "1FA6P8CF6H5100001",
            "state": "TX",
            "transaction_type": "Dealer Sale",
            "model_year": 2017,
            "odometer_miles": 45200,
            "odometer_status": "Actual",
            "has_lien": True,
            "lienholder": {"name": "Ally Financial", "elt_code": "0012345678"},
            "buyer": {"legal_name": "Jane Smith"},
            "bill_of_sale": {"buyer_name": "Jane Smith", "sale_price": 28000.0, "trade_in_allowance": 5000.0, "taxable_basis": 23000.0},
            "documents_present": ["Form 130-U (Application for Texas Title and/or Registration)", "Texas Sales Tax Declaration"],
        }

    audit_result = audit_title_packet(packet)

    if args.json_out:
        print(json.dumps(audit_result, indent=2))
    else:
        print(format_markdown_report(audit_result))


if __name__ == "__main__":
    main()
