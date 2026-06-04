from services.api.core.flow_builder.condition_engine import evaluate_condition
from services.api.core.flow_builder.flow_schema import Condition


def test_non_us_citizen_condition_is_visible() -> None:
    condition = Condition(
        operator="not_equals",
        field="citizenship_status",
        value="US Citizen",
    )

    assert evaluate_condition(condition, {"citizenship_status": "Permanent Resident"}) is True
    assert evaluate_condition(condition, {"citizenship_status": "US Citizen"}) is False


def test_minor_manual_review_condition() -> None:
    condition = Condition(operator="less_than", field="applicant_age", value=18)

    assert evaluate_condition(condition, {"applicant_age": 17}) is True
    assert evaluate_condition(condition, {"applicant_age": 18}) is False


def test_nested_and_or_not_conditions() -> None:
    condition = Condition(
        operator="and",
        conditions=[
            Condition(operator="greater_than", field="income", value=50000),
            Condition(
                operator="not",
                conditions=[Condition(operator="equals", field="country", value="Blocked")],
            ),
        ],
    )

    assert evaluate_condition(condition, {"income": 75000, "country": "US"}) is True
    assert evaluate_condition(condition, {"income": 40000, "country": "US"}) is False


def test_business_entity_in_condition() -> None:
    condition = Condition(
        operator="in",
        field="business_entity_type",
        values=["LLC", "Corporation", "Partnership"],
    )

    assert evaluate_condition(condition, {"business_entity_type": "LLC"}) is True
    assert evaluate_condition(condition, {"business_entity_type": "Sole Proprietorship"}) is False

