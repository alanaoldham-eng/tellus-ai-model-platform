from __future__ import annotations

from services.api.core.flow_builder.api_connector_engine import placeholder_connectors
from services.api.core.flow_builder.flow_schema import (
    ActionDefinition,
    Condition,
    FieldDefinition,
    FieldOption,
    FlowDefinition,
    NextStepLogic,
    NextStepRule,
    RetentionPolicy,
    StepDefinition,
    ValidationRule,
)


STANDARD_PII_RETENTION = RetentionPolicy(
    policy_id="banking_pii_standard",
    retention_period="7 years or tenant policy, whichever is stricter",
    deletion_rule="delete_or_anonymize_after_retention_and_legal_hold_release",
)
RESTRICTED_PII_RETENTION = RetentionPolicy(
    policy_id="banking_restricted_identity",
    retention_period="7 years or tenant policy, whichever is stricter",
    deletion_rule="delete_securely_after_retention_and_legal_hold_release",
)


def starter_templates() -> list[FlowDefinition]:
    return [
        consumer_checking_template(),
        small_business_deposit_template(),
        loan_prequalification_template(),
    ]


def template_by_key(template_key: str) -> FlowDefinition:
    normalized = template_key.strip().lower()
    for template in starter_templates():
        if template.flow_id == normalized or template.flow_type.lower() == normalized:
            return template
    if "business" in normalized or "kyb" in normalized:
        return small_business_deposit_template()
    if "loan" in normalized or "prequal" in normalized:
        return loan_prequalification_template()
    return consumer_checking_template()


def consumer_checking_template() -> FlowDefinition:
    return FlowDefinition(
        flow_id="template_consumer_checking_onboarding",
        name="Consumer Checking Account Onboarding",
        description="Draft onboarding and origination flow for a consumer checking account.",
        industry="banking",
        flow_type="consumer_deposit_account_opening",
        steps=[
            StepDefinition(
                step_id="eligibility",
                title="Eligibility",
                description="Collect high-level eligibility and routing information.",
                order=1,
                fields=[
                    _select(
                        "citizenship_status",
                        "Citizenship status",
                        ["US Citizen", "Permanent Resident", "Visa Holder", "Other"],
                        required=True,
                        pii="moderate",
                    ),
                    _number("applicant_age", "Applicant age", required=True, pii="moderate"),
                    _select(
                        "residency_status",
                        "Residency status",
                        ["Permanent Resident", "Temporary Resident", "Nonresident"],
                        required=True,
                        pii="moderate",
                        visible_if=Condition(
                            operator="not_equals",
                            field="citizenship_status",
                            value="US Citizen",
                        ),
                    ),
                    _text(
                        "country_of_citizenship",
                        "Country of citizenship",
                        required=True,
                        pii="moderate",
                        visible_if=Condition(
                            operator="not_equals",
                            field="citizenship_status",
                            value="US Citizen",
                        ),
                    ),
                ],
                actions=[
                    ActionDefinition(
                        action_id="route_minor_to_manual_review",
                        trigger="on_step_submit",
                        type="route_to_manual_review",
                        condition=Condition(
                            operator="less_than",
                            field="applicant_age",
                            value=18,
                        ),
                        audit_event_type="flow_reviewed",
                    )
                ],
                next_step_logic=NextStepLogic(
                    default_next_step_id="personal_information",
                    rules=[
                        NextStepRule(
                            condition=Condition(
                                operator="less_than",
                                field="applicant_age",
                                value=18,
                            ),
                            route_to_manual_review=True,
                        )
                    ],
                ),
            ),
            _personal_information_step(order=2, next_step_id="contact_information"),
            StepDefinition(
                step_id="contact_information",
                title="Contact information",
                order=3,
                fields=[
                    _email("email", "Email address", required=True),
                    _phone("phone", "Mobile phone", required=True),
                    _checkbox("sms_consent", "Consent to SMS account updates"),
                ],
                next_step_logic=NextStepLogic(default_next_step_id="address"),
            ),
            StepDefinition(
                step_id="address",
                title="Address",
                order=4,
                fields=[_address("physical_address", "Residential address", required=True)],
                next_step_logic=NextStepLogic(default_next_step_id="identity"),
            ),
            StepDefinition(
                step_id="identity",
                title="Identity",
                order=5,
                fields=[
                    _ssn_last4("ssn_last4", "SSN last 4", required=True),
                    _select(
                        "government_id_type",
                        "Government ID type",
                        ["Driver License", "State ID", "Passport", "Other"],
                        required=True,
                        pii="high",
                    ),
                    _text("government_id_number", "Government ID number", required=True, pii="restricted"),
                ],
                next_step_logic=NextStepLogic(default_next_step_id="employment_income"),
            ),
            StepDefinition(
                step_id="employment_income",
                title="Employment and income",
                order=6,
                fields=[
                    _select(
                        "employment_status",
                        "Employment status",
                        ["Employed", "Self-employed", "Student", "Retired", "Unemployed"],
                        required=True,
                    ),
                    _text("employer_name", "Employer name", pii="moderate"),
                    _currency("annual_income", "Annual income", required=True, pii="moderate"),
                ],
                next_step_logic=NextStepLogic(default_next_step_id="funding_source"),
            ),
            StepDefinition(
                step_id="funding_source",
                title="Funding source",
                order=7,
                fields=[
                    _select(
                        "funding_source",
                        "Funding source",
                        ["Payroll", "ACH transfer", "Wire transfer", "Check", "Cash", "Other"],
                        required=True,
                    ),
                    _currency("initial_deposit_amount", "Initial deposit amount"),
                ],
                next_step_logic=NextStepLogic(default_next_step_id="disclosures_consent"),
            ),
            _disclosures_step(order=8, next_step_id="document_upload"),
            StepDefinition(
                step_id="document_upload",
                title="Document upload",
                order=9,
                fields=[
                    _file("government_id_upload", "Upload government ID", required=True),
                ],
                actions=[
                    ActionDefinition(
                        action_id="verify_identity_document_placeholder",
                        trigger="on_step_submit",
                        type="call_api",
                        connector_id="document_verification_placeholder",
                        parameters={"document_field": "government_id_upload"},
                    )
                ],
                next_step_logic=NextStepLogic(default_next_step_id="review_submit"),
            ),
            StepDefinition(
                step_id="review_submit",
                title="Review and submit",
                order=10,
                fields=[
                    _checkbox("application_certification", "I certify this information is accurate"),
                ],
                actions=[
                    ActionDefinition(
                        action_id="run_kyc_before_submit",
                        trigger="before_final_submit",
                        type="call_api",
                        connector_id="kyc_placeholder",
                        parameters={"purpose": "identity_verification"},
                    ),
                    ActionDefinition(
                        action_id="submit_application",
                        trigger="after_final_submit",
                        type="submit_application",
                    ),
                ],
                next_step_logic=NextStepLogic(default_next_step_id="decision_result"),
            ),
            StepDefinition(
                step_id="decision_result",
                title="Decision/result",
                order=11,
                fields=[
                    _text("decision_status", "Decision status", pii="none"),
                ],
            ),
        ],
        connectors=[
            connector
            for connector in placeholder_connectors()
            if connector.connector_id
            in {"kyc_placeholder", "document_verification_placeholder", "fraud_scoring_placeholder"}
        ],
        assumptions=[
            "Draft template only; bank compliance review is required before publishing.",
            "KYC and document verification use placeholder connectors with secret references only.",
        ],
        risk_flags=[
            "regulated_banking_flow",
            "kyc_aml_review_required",
            "glba_privacy_review_required",
            "manual_review_for_minor_applicants",
        ],
        recommended_human_review_items=[
            "Review eligibility criteria for prohibited or discriminatory logic.",
            "Review disclosures, consent language, privacy notices, and retention policy.",
            "Review KYC, AML, OFAC, and CIP requirements before publishing.",
        ],
    )


def small_business_deposit_template() -> FlowDefinition:
    return FlowDefinition(
        flow_id="template_small_business_deposit_onboarding",
        name="Small Business Deposit Account Onboarding",
        description="Draft onboarding flow for small business deposit account origination.",
        industry="banking",
        flow_type="small_business_deposit_account_opening",
        steps=[
            StepDefinition(
                step_id="business_information",
                title="Business information",
                order=1,
                fields=[
                    _text("legal_business_name", "Legal business name", required=True, pii="moderate"),
                    _text("dba_name", "DBA name", pii="low"),
                    _phone("business_phone", "Business phone", required=True),
                    _email("business_email", "Business email", required=True),
                ],
                next_step_logic=NextStepLogic(default_next_step_id="entity_details"),
            ),
            StepDefinition(
                step_id="entity_details",
                title="Entity details",
                order=2,
                fields=[
                    _select(
                        "business_entity_type",
                        "Business entity type",
                        ["LLC", "Corporation", "Partnership", "Sole Proprietorship", "Nonprofit"],
                        required=True,
                    ),
                    _date("formation_date", "Formation date", pii="moderate"),
                    _text("state_of_formation", "State of formation", required=True),
                ],
                next_step_logic=NextStepLogic(default_next_step_id="tax_information"),
            ),
            StepDefinition(
                step_id="tax_information",
                title="Tax information",
                order=3,
                fields=[
                    _tax_id("ein", "EIN or tax ID", required=True),
                    _text("tax_classification", "Tax classification", required=True),
                ],
                next_step_logic=NextStepLogic(default_next_step_id="business_address"),
            ),
            StepDefinition(
                step_id="business_address",
                title="Business address",
                order=4,
                fields=[_address("business_address", "Business address", required=True)],
                next_step_logic=NextStepLogic(default_next_step_id="authorized_signer"),
            ),
            StepDefinition(
                step_id="authorized_signer",
                title="Authorized signer",
                order=5,
                fields=[
                    _text("signer_full_name", "Authorized signer full name", required=True, pii="high"),
                    _email("signer_email", "Authorized signer email", required=True),
                    _phone("signer_phone", "Authorized signer phone", required=True),
                    _ssn_last4("signer_ssn_last4", "Authorized signer SSN last 4", required=True),
                ],
                next_step_logic=NextStepLogic(default_next_step_id="beneficial_ownership"),
            ),
            StepDefinition(
                step_id="beneficial_ownership",
                title="Beneficial ownership",
                order=6,
                fields=[
                    _beneficial_owner(
                        "beneficial_owners",
                        "Beneficial owners",
                        visible_if=Condition(
                            operator="in",
                            field="business_entity_type",
                            values=["LLC", "Corporation", "Partnership"],
                        ),
                    )
                ],
                next_step_logic=NextStepLogic(default_next_step_id="expected_activity"),
            ),
            StepDefinition(
                step_id="expected_activity",
                title="Expected activity",
                order=7,
                fields=[
                    _currency("expected_monthly_deposits", "Expected monthly deposits", required=True),
                    _currency("expected_monthly_withdrawals", "Expected monthly withdrawals"),
                    _select(
                        "primary_business_activity",
                        "Primary business activity",
                        ["Retail", "Professional services", "Technology", "Hospitality", "Other"],
                        required=True,
                    ),
                ],
                next_step_logic=NextStepLogic(default_next_step_id="documents"),
            ),
            StepDefinition(
                step_id="documents",
                title="Documents",
                order=8,
                fields=[
                    _file("formation_document", "Formation document", required=True),
                    _file("operating_agreement", "Operating agreement"),
                ],
                next_step_logic=NextStepLogic(default_next_step_id="disclosures_consent"),
            ),
            _disclosures_step(order=9, next_step_id="review_submit"),
            StepDefinition(
                step_id="review_submit",
                title="Review and submit",
                order=10,
                fields=[_checkbox("business_certification", "I certify this business information is accurate")],
                actions=[
                    ActionDefinition(
                        action_id="run_kyb_before_submit",
                        trigger="before_final_submit",
                        type="call_api",
                        connector_id="kyb_placeholder",
                    ),
                    ActionDefinition(
                        action_id="run_ofac_before_submit",
                        trigger="before_final_submit",
                        type="call_api",
                        connector_id="ofac_sanctions_placeholder",
                    ),
                    ActionDefinition(
                        action_id="require_business_review",
                        trigger="before_final_submit",
                        type="require_human_review",
                    ),
                ],
                next_step_logic=NextStepLogic(default_next_step_id="manual_review_result"),
            ),
            StepDefinition(
                step_id="manual_review_result",
                title="Manual review/result",
                order=11,
                fields=[_text("review_status", "Review status")],
            ),
        ],
        connectors=[
            connector
            for connector in placeholder_connectors()
            if connector.connector_id in {"kyb_placeholder", "ofac_sanctions_placeholder"}
        ],
        assumptions=[
            "Beneficial ownership collection is shown for common entity types and must be reviewed.",
            "KYB and sanctions checks are placeholders only.",
        ],
        risk_flags=[
            "regulated_banking_flow",
            "kyb_review_required",
            "beneficial_ownership_review_required",
            "glba_privacy_review_required",
        ],
        recommended_human_review_items=[
            "Review beneficial ownership thresholds and certification language.",
            "Review KYB, AML, OFAC, and customer due diligence requirements.",
        ],
    )


def loan_prequalification_template() -> FlowDefinition:
    return FlowDefinition(
        flow_id="template_loan_prequalification",
        name="Loan Prequalification",
        description="Draft loan prequalification workflow with soft-pull placeholder.",
        industry="banking",
        flow_type="loan_prequalification",
        steps=[
            StepDefinition(
                step_id="product_selection",
                title="Product selection",
                order=1,
                fields=[
                    _select(
                        "loan_product",
                        "Loan product",
                        ["Personal loan", "Auto loan", "Small business loan"],
                        required=True,
                    )
                ],
                next_step_logic=NextStepLogic(default_next_step_id="applicant_information"),
            ),
            _personal_information_step(order=2, next_step_id="income"),
            StepDefinition(
                step_id="income",
                title="Income",
                order=3,
                fields=[
                    _currency("gross_annual_income", "Gross annual income", required=True),
                    _select(
                        "income_source",
                        "Income source",
                        ["Employment", "Self-employment", "Retirement", "Other"],
                        required=True,
                    ),
                ],
                next_step_logic=NextStepLogic(default_next_step_id="housing"),
            ),
            StepDefinition(
                step_id="housing",
                title="Housing",
                order=4,
                fields=[
                    _select("housing_status", "Housing status", ["Own", "Rent", "Other"], required=True),
                    _currency("monthly_housing_payment", "Monthly housing payment", required=True),
                ],
                next_step_logic=NextStepLogic(default_next_step_id="credit_consent"),
            ),
            StepDefinition(
                step_id="credit_consent",
                title="Credit consent",
                order=5,
                fields=[
                    _consent("credit_pull_consent", "I consent to a soft credit pull", required=True),
                ],
                next_step_logic=NextStepLogic(default_next_step_id="requested_amount"),
            ),
            StepDefinition(
                step_id="requested_amount",
                title="Requested amount",
                order=6,
                fields=[
                    _currency("requested_loan_amount", "Requested loan amount", required=True),
                    _number("requested_term_months", "Requested term in months", required=True),
                ],
                next_step_logic=NextStepLogic(default_next_step_id="soft_pull_placeholder"),
            ),
            StepDefinition(
                step_id="soft_pull_placeholder",
                title="Soft-pull placeholder",
                order=7,
                actions=[
                    ActionDefinition(
                        action_id="run_soft_pull_placeholder",
                        trigger="on_step_submit",
                        type="call_api",
                        connector_id="credit_bureau_placeholder",
                    )
                ],
                next_step_logic=NextStepLogic(default_next_step_id="decision_result"),
            ),
            StepDefinition(
                step_id="decision_result",
                title="Decision/result",
                order=8,
                fields=[_text("prequalification_status", "Prequalification status")],
            ),
        ],
        connectors=[
            connector
            for connector in placeholder_connectors()
            if connector.connector_id in {"credit_bureau_placeholder", "fraud_scoring_placeholder"}
        ],
        assumptions=[
            "This is a prequalification draft, not a final credit decision workflow.",
            "Credit bureau and fraud scoring calls are placeholders only.",
        ],
        risk_flags=[
            "regulated_lending_flow",
            "fcra_review_required",
            "ecoa_udaap_review_required",
            "adverse_action_notice_review_required",
        ],
        recommended_human_review_items=[
            "Review permissible purpose, credit consent, FCRA, ECOA, and adverse action handling.",
            "Review prohibited-basis and disparate-impact risks before publishing.",
        ],
    )


def _personal_information_step(order: int, next_step_id: str) -> StepDefinition:
    return StepDefinition(
        step_id="personal_information",
        title="Personal information",
        order=order,
        fields=[
            _text("first_name", "First name", required=True, pii="high"),
            _text("last_name", "Last name", required=True, pii="high"),
            _date("date_of_birth", "Date of birth", required=True, pii="high"),
        ],
        next_step_logic=NextStepLogic(default_next_step_id=next_step_id),
    )


def _disclosures_step(order: int, next_step_id: str) -> StepDefinition:
    return StepDefinition(
        step_id="disclosures_consent",
        title="Disclosures and consent",
        order=order,
        fields=[
            _disclosure(
                "deposit_account_disclosure_ack",
                "I acknowledge receipt of required account disclosures",
                required=True,
            ),
            _consent("esign_consent", "I consent to electronic records and signatures", required=True),
            _consent("privacy_notice_ack", "I acknowledge the privacy notice", required=True),
        ],
        actions=[
            ActionDefinition(
                action_id="generate_disclosure_packet",
                trigger="on_step_submit",
                type="generate_disclosure_packet",
            )
        ],
        next_step_logic=NextStepLogic(default_next_step_id=next_step_id),
    )


def _text(
    field_id: str,
    label: str,
    required: bool = False,
    pii: str = "none",
    visible_if: Condition | None = None,
) -> FieldDefinition:
    return _field(field_id, label, "text", required, pii, visible_if=visible_if)


def _number(field_id: str, label: str, required: bool = False, pii: str = "none") -> FieldDefinition:
    return _field(field_id, label, "number", required, pii)


def _currency(field_id: str, label: str, required: bool = False, pii: str = "moderate") -> FieldDefinition:
    return _field(field_id, label, "currency", required, pii)


def _date(field_id: str, label: str, required: bool = False, pii: str = "moderate") -> FieldDefinition:
    return _field(field_id, label, "date", required, pii)


def _email(field_id: str, label: str, required: bool = False) -> FieldDefinition:
    return _field(field_id, label, "email", required, "moderate")


def _phone(field_id: str, label: str, required: bool = False) -> FieldDefinition:
    return _field(field_id, label, "phone", required, "moderate")


def _address(field_id: str, label: str, required: bool = False) -> FieldDefinition:
    return _field(field_id, label, "address", required, "high")


def _ssn_last4(field_id: str, label: str, required: bool = False) -> FieldDefinition:
    return _field(
        field_id,
        label,
        "ssn_last4",
        required,
        "restricted",
        validation_rules=[ValidationRule(rule="length", value=4)],
    )


def _tax_id(field_id: str, label: str, required: bool = False) -> FieldDefinition:
    return _field(field_id, label, "tax_id", required, "restricted")


def _file(field_id: str, label: str, required: bool = False) -> FieldDefinition:
    return _field(field_id, label, "file_upload", required, "restricted", audit_required=True)


def _checkbox(field_id: str, label: str, required: bool = False) -> FieldDefinition:
    return _field(field_id, label, "checkbox", required, "none", audit_required=required)


def _consent(field_id: str, label: str, required: bool = False) -> FieldDefinition:
    return _field(field_id, label, "consent_checkbox", required, "moderate", audit_required=True)


def _disclosure(field_id: str, label: str, required: bool = False) -> FieldDefinition:
    return _field(
        field_id,
        label,
        "disclosure_acknowledgment",
        required,
        "moderate",
        audit_required=True,
    )


def _beneficial_owner(
    field_id: str,
    label: str,
    visible_if: Condition | None = None,
) -> FieldDefinition:
    return _field(
        field_id,
        label,
        "beneficial_owner",
        required=True,
        pii="restricted",
        visible_if=visible_if,
        audit_required=True,
    )


def _select(
    field_id: str,
    label: str,
    options: list[str],
    required: bool = False,
    pii: str = "none",
    visible_if: Condition | None = None,
) -> FieldDefinition:
    return _field(
        field_id,
        label,
        "select",
        required,
        pii,
        visible_if=visible_if,
        options=[FieldOption(label=option, value=option) for option in options],
    )


def _field(
    field_id: str,
    label: str,
    field_type: str,
    required: bool,
    pii: str,
    visible_if: Condition | None = None,
    options: list[FieldOption] | None = None,
    validation_rules: list[ValidationRule] | None = None,
    audit_required: bool = False,
) -> FieldDefinition:
    retention = None
    if pii in {"high", "restricted"}:
        retention = RESTRICTED_PII_RETENTION if pii == "restricted" else STANDARD_PII_RETENTION
    return FieldDefinition(
        field_id=field_id,
        label=label,
        type=field_type,  # type: ignore[arg-type]
        required=required,
        validation_rules=validation_rules or [],
        visible_if=visible_if,
        options=options or [],
        pii_classification=pii,  # type: ignore[arg-type]
        retention_policy=retention,
        audit_required=audit_required or pii in {"high", "restricted"},
    )
