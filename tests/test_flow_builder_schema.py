from services.api.core.flow_builder.flow_schema import flow_json_schema, flatten_fields
from services.api.core.flow_builder.templates import consumer_checking_template
from services.api.core.flow_builder.validation_engine import validate_flow_definition


def test_consumer_checking_template_validates() -> None:
    flow = consumer_checking_template()

    result = validate_flow_definition(flow)

    assert result.valid is True
    assert result.errors == []
    assert "regulated_banking_flow" in result.risk_flags


def test_sensitive_fields_are_classified_and_retained() -> None:
    flow = consumer_checking_template()

    fields = {field.field_id: field for field in flatten_fields(flow)}

    assert fields["ssn_last4"].pii_classification == "restricted"
    assert fields["ssn_last4"].retention_policy is not None
    assert fields["government_id_upload"].audit_required is True


def test_flow_json_schema_exposes_core_properties() -> None:
    schema = flow_json_schema()

    assert "properties" in schema
    assert "steps" in schema["properties"]
    assert "connectors" in schema["properties"]

