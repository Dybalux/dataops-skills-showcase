Feature: DMV Title Packet & Compliance Verification
  As a Business Operations Analyst at Fairway
  I want to automatically audit vehicle titling packets across state DMVs
  So that invalid VINs, non-compliant odometer disclosures, and missing state forms are caught before DMV submission

  Scenario: Detect invalid VIN check digit and illegal odometer exemption
    Given a non-compliant titling packet with invalid VIN "1FA6P8CF5H5100001" and status "Exempt" for a 2017 vehicle
    When the DMV titling packet verifier audits the transaction
    Then the audit status is "REJECTED" with "Critical" rejection risk
    And the verifier flags a VIN check digit mismatch at position 9
    And the verifier flags an odometer violation under the 20-year federal rolling rule

  Scenario: Verify compliant Texas dealership title packet
    Given a compliant Texas dealership packet with valid VIN "1FA6P8CF6H5100001", "Form 130-U", and valid ELT code
    When the DMV titling packet verifier audits the transaction
    Then the audit status is "PASSED" with "None" rejection risk
    And the packet is approved for DMV submission

  Scenario: Verify compliant California electric vehicle title packet
    Given a compliant California packet for a 2020 Tesla with valid VIN "5YJ3E1EB5LF000001" and "REG 343"
    When the DMV titling packet verifier audits the transaction
    Then the audit status is "PASSED" with "None" rejection risk
    And the packet is approved for DMV submission

  Scenario: Detect missing out-of-state physical inspection form in Texas
    Given an out-of-state transfer packet for Texas missing the "VI-30-A" inspection certificate
    When the DMV titling packet verifier audits the transaction
    Then the audit status is "REJECTED" with "Critical" rejection risk
    And the verifier flags a missing out-of-state physical inspection form under "FM-5"

  Scenario: Detect missing out-of-state physical inspection form in California
    Given an out-of-state transfer packet for California having "REG 343" but missing "REG 31"
    When the DMV titling packet verifier audits the transaction
    Then the audit status is "REJECTED" with "Critical" rejection risk
    And the verifier flags a missing out-of-state physical inspection form under "FM-5"

  Scenario: Detect missing out-of-state physical inspection form in Florida
    Given an out-of-state transfer packet for Florida having "HSMV 82040" but missing "HSMV 82042"
    When the DMV titling packet verifier audits the transaction
    Then the audit status is "REJECTED" with "Critical" rejection risk
    And the verifier flags a missing out-of-state physical inspection form under "FM-5"

  Scenario: Allow pre-1981 classic vehicle with short VIN under FM-1
    Given a classic 1967 Ford Mustang with short VIN "7R01C100001"
    When the DMV titling packet verifier audits the transaction
    Then the VIN is accepted as a pre-1981 classic vehicle under "FM-1"

  Scenario: Detect missing ELT code for financed vehicle under FM-3
    Given a financed vehicle in Florida missing the mandatory ELT code
    When the DMV titling packet verifier audits the transaction
    Then the audit status is "REJECTED" with "Critical" rejection risk
    And the verifier flags a missing ELT code under "FM-3"

  Scenario: Detect buyer name mismatch between Bill of Sale and Title under FM-4
    Given a transaction where the buyer on Title Application is "Jane Smith" but Bill of Sale is "Acme Corp LLC"
    When the DMV titling packet verifier audits the transaction
    Then the audit status is "REJECTED" with "Critical" rejection risk
    And the verifier flags an entity mismatch under "FM-4"

  Scenario: Verify check digit calculation with Roman numeral X and reject illegal characters
    Given a vehicle with valid check digit X in VIN "1FA6P8C2XH5100001" and another with illegal character "1FA6P8CF6HI100001"
    When both VINs are validated by the engine
    Then the check digit X is valid and the illegal character I is rejected

  Scenario: Normalize full state name and sanitize dirty document arrays
    Given a Texas transaction with state "Texas" and dirty documents list containing nulls and numbers
    When the DMV titling packet verifier audits the transaction
    Then the audit status is "PASSED" with "None" rejection risk
    And the jurisdiction is normalized to "TX"

  Scenario: Detect negative financial values and future model year anomalies
    Given a transaction with negative sale price -25000 and future model year 2055
    When the DMV titling packet verifier audits the transaction
    Then the audit status is "REJECTED" with "Critical" rejection risk
    And the verifier flags financial boundary and model year violations
