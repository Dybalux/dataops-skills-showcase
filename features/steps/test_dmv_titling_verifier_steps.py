import importlib.util
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("../dmv_titling_verifier.feature")

# Load verify_title_packet dynamically from assets
script_path = Path(".claude/skills/dmv-titling-packet-verifier/assets/verify_title_packet.py")
spec = importlib.util.spec_from_file_location("verify_title_packet", script_path)
verify_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_module)


@pytest.fixture
def titling_context():
    return {
        "packet": {},
        "result": None,
        "vin_x_result": None,
        "vin_illegal_result": None,
    }


@given(parsers.parse('a non-compliant titling packet with invalid VIN "{vin}" and status "{odo_status}" for a {year:d} vehicle'))
def setup_non_compliant_packet(titling_context: dict, vin: str, odo_status: str, year: int):
    titling_context["packet"] = {
        "vin": vin,
        "state": "TX",
        "transaction_type": "Dealer Sale",
        "model_year": year,
        "odometer_miles": 45200,
        "odometer_status": odo_status,
        "has_lien": True,
        "lienholder": {"name": "Ally Financial", "elt_code": "0012345678"},
        "buyer": {"legal_name": "Jane Smith"},
        "bill_of_sale": {"buyer_name": "Jane Smith", "sale_price": 28000.0, "taxable_basis": 28000.0},
        "documents_present": ["Form 130-U (Application for Texas Title and/or Registration)"],
    }


@given(parsers.parse('a compliant Texas dealership packet with valid VIN "{vin}", "{primary_form}", and valid ELT code'))
def setup_compliant_packet(titling_context: dict, vin: str, primary_form: str):
    titling_context["packet"] = {
        "vin": vin,
        "state": "TX",
        "transaction_type": "Dealer Sale",
        "model_year": 2017,
        "odometer_miles": 45200,
        "odometer_status": "Actual",
        "has_lien": True,
        "lienholder": {"name": "Ally Financial", "elt_code": "0012345678"},
        "buyer": {"legal_name": "Jane Smith"},
        "bill_of_sale": {"buyer_name": "Jane Smith", "sale_price": 28000.0, "taxable_basis": 28000.0},
        "documents_present": [primary_form, "Texas Sales Tax Declaration"],
    }


@given(parsers.parse('a compliant California packet for a 2020 Tesla with valid VIN "{vin}" and "{primary_form}"'))
def setup_compliant_ca_packet(titling_context: dict, vin: str, primary_form: str):
    titling_context["packet"] = {
        "vin": vin,
        "state": "CA",
        "transaction_type": "Dealer Sale",
        "model_year": 2020,
        "odometer_miles": 32000,
        "odometer_status": "Actual",
        "has_lien": True,
        "lienholder": {"name": "Tesla Finance LLC", "elt_code": "CA-TSLA-01"},
        "buyer": {"legal_name": "Marcus Vance"},
        "bill_of_sale": {"buyer_name": "Marcus Vance", "sale_price": 42000.0, "taxable_basis": 42000.0},
        "documents_present": [primary_form, "REG 262 (Vehicle Transfer and Reassignment / Odometer)"],
    }


@given(parsers.parse('an out-of-state transfer packet for Texas missing the "{missing_form}" inspection certificate'))
def setup_missing_tx_inspection_packet(titling_context: dict, missing_form: str):
    titling_context["packet"] = {
        "vin": "1FA6P8CF6H5100001",
        "state": "TX",
        "transaction_type": "Dealer Sale",
        "model_year": 2017,
        "odometer_miles": 45200,
        "odometer_status": "Actual",
        "out_of_state": True,
        "has_lien": True,
        "lienholder": {"name": "Ally Financial", "elt_code": "0012345678"},
        "buyer": {"legal_name": "Jane Smith"},
        "bill_of_sale": {"buyer_name": "Jane Smith", "sale_price": 28000.0, "taxable_basis": 28000.0},
        "documents_present": ["Form 130-U (Application for Texas Title and/or Registration)"],
    }


@given(parsers.parse('an out-of-state transfer packet for California having "{present_form}" but missing "{missing_form}"'))
def setup_missing_ca_inspection_packet(titling_context: dict, present_form: str, missing_form: str):
    titling_context["packet"] = {
        "vin": "5YJ3E1EB5LF000001",
        "state": "CA",
        "transaction_type": "Dealer Sale",
        "model_year": 2020,
        "odometer_miles": 32000,
        "odometer_status": "Actual",
        "out_of_state": True,
        "has_lien": False,
        "buyer": {"legal_name": "Marcus Vance"},
        "bill_of_sale": {"buyer_name": "Marcus Vance", "sale_price": 42000.0, "taxable_basis": 42000.0},
        "documents_present": [present_form],  # Has REG 343, missing REG 31
    }


@given(parsers.parse('an out-of-state transfer packet for Florida having "{present_form}" but missing "{missing_form}"'))
def setup_missing_fl_inspection_packet(titling_context: dict, present_form: str, missing_form: str):
    titling_context["packet"] = {
        "vin": "1FA6P8CF6H5100001",
        "state": "FL",
        "transaction_type": "Dealer Sale",
        "model_year": 2017,
        "odometer_miles": 45200,
        "odometer_status": "Actual",
        "out_of_state": True,
        "has_lien": False,
        "buyer": {"legal_name": "Jane Smith"},
        "bill_of_sale": {"buyer_name": "Jane Smith", "sale_price": 28000.0, "taxable_basis": 28000.0},
        "documents_present": [present_form],  # Has HSMV 82040, missing HSMV 82042
    }


@given(parsers.parse('a classic {year:d} Ford Mustang with short VIN "{vin}"'))
def setup_classic_vehicle_packet(titling_context: dict, year: int, vin: str):
    titling_context["packet"] = {
        "vin": vin,
        "state": "TX",
        "transaction_type": "Private Sale",
        "model_year": year,
        "odometer_miles": 112000,
        "odometer_status": "Exempt",
        "out_of_state": False,
        "has_lien": False,
        "buyer": {"legal_name": "Jane Smith"},
        "bill_of_sale": {"buyer_name": "Jane Smith", "sale_price": 35000.0, "taxable_basis": 35000.0},
        "documents_present": ["Form 130-U (Application for Texas Title and/or Registration)", "Texas Sales Tax Declaration"],
    }


@given("a financed vehicle in Florida missing the mandatory ELT code")
def setup_missing_elt_packet(titling_context: dict):
    titling_context["packet"] = {
        "vin": "1FA6P8CF6H5100001",
        "state": "FL",
        "transaction_type": "Dealer Sale",
        "model_year": 2017,
        "odometer_miles": 45200,
        "odometer_status": "Actual",
        "has_lien": True,
        "lienholder": {"name": "Bank of America", "elt_code": ""},  # Missing ELT code
        "buyer": {"legal_name": "Jane Smith"},
        "bill_of_sale": {"buyer_name": "Jane Smith", "sale_price": 28000.0, "taxable_basis": 28000.0},
        "documents_present": ["HSMV 82040 (Application for Certificate of Motor Vehicle Title)"],
    }


@given(parsers.parse('a transaction where the buyer on Title Application is "{title_buyer}" but Bill of Sale is "{bos_buyer}"'))
def setup_entity_mismatch_packet(titling_context: dict, title_buyer: str, bos_buyer: str):
    titling_context["packet"] = {
        "vin": "1FA6P8CF6H5100001",
        "state": "TX",
        "transaction_type": "Dealer Sale",
        "model_year": 2017,
        "odometer_miles": 45200,
        "odometer_status": "Actual",
        "has_lien": False,
        "buyer": {"legal_name": title_buyer},
        "bill_of_sale": {"buyer_name": bos_buyer, "sale_price": 28000.0, "taxable_basis": 28000.0},
        "documents_present": ["Form 130-U (Application for Texas Title and/or Registration)", "Texas Sales Tax Declaration"],
    }


@given(parsers.parse('a vehicle with valid check digit X in VIN "{vin_x}" and another with illegal character "{vin_illegal}"'))
def setup_vin_check_cases(titling_context: dict, vin_x: str, vin_illegal: str):
    titling_context["vin_x"] = vin_x
    titling_context["vin_illegal"] = vin_illegal


@when("both VINs are validated by the engine")
def validate_both_vins(titling_context: dict):
    titling_context["vin_x_result"] = verify_module.validate_vin(titling_context["vin_x"])
    titling_context["vin_illegal_result"] = verify_module.validate_vin(titling_context["vin_illegal"])


@then(parsers.parse("the check digit X is valid and the illegal character {illegal_char} is rejected"))
def assert_check_digit_x_and_illegal_char(titling_context: dict, illegal_char: str):
    valid_x, msg_x, exp_x, _ = titling_context["vin_x_result"]
    assert valid_x is True, f"Expected check digit X to be valid: {msg_x}"
    assert exp_x == "X"

    valid_ill, msg_ill, _, _ = titling_context["vin_illegal_result"]
    assert valid_ill is False, "Expected illegal char VIN to fail validation"
    assert "Illegal characters detected" in msg_ill or illegal_char in msg_ill


@when("the DMV titling packet verifier audits the transaction")
def audit_packet_step(titling_context: dict):
    titling_context["result"] = verify_module.audit_title_packet(titling_context["packet"])


@then(parsers.parse('the audit status is "{expected_status}" with "{expected_risk}" rejection risk'))
def assert_audit_status(titling_context: dict, expected_status: str, expected_risk: str):
    res = titling_context["result"]
    assert res["status"] == expected_status, f"Expected status {expected_status}, got {res['status']}"
    assert res["rejection_risk"] == expected_risk, f"Expected risk {expected_risk}, got {res['rejection_risk']}"


@then("the verifier flags a VIN check digit mismatch at position 9")
def assert_vin_mismatch(titling_context: dict):
    res = titling_context["result"]
    assert res["vin_check_digit_valid"] is False, "VIN check digit should be invalid"
    assert any("check digit mismatch" in v.lower() for v in res["violations"])


@then("the verifier flags an odometer violation under the 20-year federal rolling rule")
def assert_odometer_violation(titling_context: dict):
    res = titling_context["result"]
    assert any("20-year" in v.lower() or "cannot be marked 'exempt'" in v.lower() for v in res["violations"])


@then("the packet is approved for DMV submission")
def assert_packet_approved(titling_context: dict):
    res = titling_context["result"]
    assert len(res["violations"]) == 0, f"Expected 0 violations, got {res['violations']}"
    assert res["status"] == "PASSED"


@then(parsers.parse('the verifier flags a missing out-of-state physical inspection form under "{failure_mode}"'))
def assert_missing_out_of_state_form(titling_context: dict, failure_mode: str):
    res = titling_context["result"]
    assert any(failure_mode in v for v in res["violations"]), f"Expected {failure_mode} in violations, got {res['violations']}"


@then(parsers.parse('the VIN is accepted as a pre-1981 classic vehicle under "{failure_mode}"'))
def assert_classic_vehicle_accepted(titling_context: dict, failure_mode: str):
    res = titling_context["result"]
    assert res["vin_check_digit_valid"] is True, f"Expected classic VIN to pass with FM-1 waiver: {res['vin_message']}"
    assert failure_mode in res["vin_message"]


@then(parsers.parse('the verifier flags a missing ELT code under "{failure_mode}"'))
def assert_missing_elt_code(titling_context: dict, failure_mode: str):
    res = titling_context["result"]
    assert any(failure_mode in v for v in res["violations"]), f"Expected {failure_mode} in violations, got {res['violations']}"


@then(parsers.parse('the verifier flags an entity mismatch under "{failure_mode}"'))
def assert_entity_mismatch(titling_context: dict, failure_mode: str):
    res = titling_context["result"]
    assert any(failure_mode in v for v in res["violations"]), f"Expected {failure_mode} in violations, got {res['violations']}"


@given(parsers.parse('a Texas transaction with state "{state_name}" and dirty documents list containing nulls and numbers'))
def setup_dirty_docs_tx_packet(titling_context: dict, state_name: str):
    titling_context["packet"] = {
        "vin": "1FA6P8CF6H5100001",
        "state": state_name,
        "transaction_type": "Dealer Sale",
        "model_year": 2017,
        "odometer_miles": 45200,
        "odometer_status": "Actual",
        "has_lien": True,
        "lienholder": {"name": "Ally Financial", "elt_code": "0012345678"},
        "buyer": {"legal_name": "Jane Smith"},
        "bill_of_sale": {"buyer_name": "Jane Smith", "sale_price": 28000.0, "taxable_basis": 28000.0},
        "documents_present": [
            None,
            12345,
            {},
            "Form 130-U (Application for Texas Title and/or Registration)",
            "Texas Sales Tax Declaration",
        ],
    }


@then(parsers.parse('the jurisdiction is normalized to "{expected_state}"'))
def assert_jurisdiction_normalized(titling_context: dict, expected_state: str):
    res = titling_context["result"]
    assert res["state"] == expected_state, f"Expected state {expected_state}, got {res['state']}"


@given(parsers.parse('a transaction with negative sale price {price:d} and future model year {year:d}'))
def setup_anomalous_packet(titling_context: dict, price: int, year: int):
    titling_context["packet"] = {
        "vin": "1FA6P8CF6H5100001",
        "state": "TX",
        "transaction_type": "Dealer Sale",
        "model_year": year,
        "odometer_miles": 45200,
        "odometer_status": "Actual",
        "has_lien": False,
        "buyer": {"legal_name": "Jane Smith"},
        "bill_of_sale": {"buyer_name": "Jane Smith", "sale_price": float(price), "taxable_basis": float(price)},
        "documents_present": ["Form 130-U (Application for Texas Title and/or Registration)", "Texas Sales Tax Declaration"],
    }


@then("the verifier flags financial boundary and model year violations")
def assert_financial_and_model_year_violations(titling_context: dict):
    res = titling_context["result"]
    assert any("Financial Boundary Violation" in v for v in res["violations"]), f"Expected financial violation in {res['violations']}"
    assert any("Model Year Anomaly" in v for v in res["violations"]), f"Expected model year anomaly in {res['violations']}"

