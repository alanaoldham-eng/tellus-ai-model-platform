from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from typing import Any

from services.api.core.flow_builder.flow_schema import Condition


def evaluate_condition(condition: Condition | dict[str, Any] | None, payload: Mapping[str, Any]) -> bool:
    if condition is None:
        return True
    if isinstance(condition, dict):
        condition = Condition.model_validate(condition)

    operator = condition.operator
    if operator == "and":
        return all(evaluate_condition(child, payload) for child in condition.conditions)
    if operator == "or":
        return any(evaluate_condition(child, payload) for child in condition.conditions)
    if operator == "not":
        return not evaluate_condition(condition.conditions[0], payload)

    actual = get_value(payload, condition.field or "")
    expected = condition.value

    if operator == "equals":
        return actual == expected
    if operator == "not_equals":
        return actual != expected
    if operator == "contains":
        return _contains(actual, expected)
    if operator == "greater_than":
        return _compare(actual, expected) > 0
    if operator == "less_than":
        return _compare(actual, expected) < 0
    if operator == "between":
        lower, upper = _between_bounds(condition)
        return _compare(actual, lower) >= 0 and _compare(actual, upper) <= 0
    if operator == "exists":
        return actual is not None and actual != ""
    if operator == "not_exists":
        return actual is None or actual == ""
    if operator == "in":
        return actual in (condition.values or [])
    if operator == "not_in":
        return actual not in (condition.values or [])

    raise ValueError(f"Unsupported condition operator: {operator}")


def get_value(payload: Mapping[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.split("."):
        if isinstance(current, Mapping) and part in current:
            current = current[part]
        else:
            return None
    return current


def _contains(actual: Any, expected: Any) -> bool:
    if actual is None:
        return False
    if isinstance(actual, str):
        return str(expected) in actual
    if isinstance(actual, list | tuple | set):
        return expected in actual
    return False


def _compare(left: Any, right: Any) -> int:
    left_decimal = _to_decimal(left)
    right_decimal = _to_decimal(right)
    if left_decimal is not None and right_decimal is not None:
        if left_decimal > right_decimal:
            return 1
        if left_decimal < right_decimal:
            return -1
        return 0

    left_text = "" if left is None else str(left)
    right_text = "" if right is None else str(right)
    if left_text > right_text:
        return 1
    if left_text < right_text:
        return -1
    return 0


def _to_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _between_bounds(condition: Condition) -> tuple[Any, Any]:
    if condition.values and len(condition.values) == 2:
        return condition.values[0], condition.values[1]
    return condition.min_value, condition.max_value

