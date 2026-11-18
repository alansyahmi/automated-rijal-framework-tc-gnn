"""Isolated, inactive preview support for proposed Shamela4 exception rules.

This module is intentionally not imported by the production proposal generator.
It validates a versioned registry and previews proposed actions for tests only.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = "1.0"
REGISTRY_VERSION = "1.0"
REGISTRY_ID = "SHAMELA4_EXCEPTION_RULES_V1"
ALLOWED_ACTIONS = {
    "suppress_base_match",
    "preserve_attributed_judgement",
    "preserve_qualification",
    "separate_status_from_reliability",
    "classify_specific_criticism",
    "abstain_for_review",
}
RULE_STATES = {"proposed", "reviewed", "approved", "retired"}
REGISTRY_STATES = {"inactive", "active"}
EXCEPTION_ID_PATTERN = re.compile(r"^EXC_[A-Z0-9_]+$")
PILOT_REF_PATTERN = re.compile(r"^PROV-[0-9]+-C[0-9]+-S[0-9]+$")
RULE_KEYS = {
    "exception_id",
    "rule_version",
    "status",
    "active",
    "trigger",
    "scope",
    "actions",
    "rationale",
    "expected_behavior",
    "supporting_pilot_refs",
    "evidence_status",
    "approval",
}


class ExceptionRegistryError(ValueError):
    """Raised when an exception registry violates its versioned contract."""


def load_exception_registry(path: str | Path) -> dict[str, Any]:
    """Load UTF-8 JSON and validate the inactive exception registry."""
    registry_path = Path(path)
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExceptionRegistryError(f"Could not read exception registry: {registry_path}") from exc
    validate_exception_registry(registry)
    return registry


def validate_exception_registry(registry: Mapping[str, Any]) -> None:
    """Validate registry structure, exact triggers, and approval requirements."""
    if not isinstance(registry, Mapping):
        raise ExceptionRegistryError("Registry must be an object")
    expected = {
        "schema_version",
        "registry_version",
        "registry_id",
        "status",
        "activation_policy",
        "conflict_policy",
        "actions_are_advisory",
        "rank_assignment_permitted",
        "rules",
    }
    if set(registry) != expected:
        raise ExceptionRegistryError("Registry fields do not match schema v1")
    if registry.get("schema_version") != SCHEMA_VERSION:
        raise ExceptionRegistryError("Unsupported exception registry schema version")
    if registry.get("registry_version") != REGISTRY_VERSION:
        raise ExceptionRegistryError("Unsupported exception registry version")
    if registry.get("registry_id") != REGISTRY_ID:
        raise ExceptionRegistryError("Unexpected exception registry ID")
    if registry.get("status") not in REGISTRY_STATES:
        raise ExceptionRegistryError("Invalid registry status")
    if registry.get("activation_policy") != "human_approval_required":
        raise ExceptionRegistryError("Invalid activation policy")
    if registry.get("conflict_policy") != "multiple_match_abstain":
        raise ExceptionRegistryError("Invalid conflict policy")
    if registry.get("actions_are_advisory") is not True:
        raise ExceptionRegistryError("Exception actions must remain advisory")
    if registry.get("rank_assignment_permitted") is not False:
        raise ExceptionRegistryError("Exception rules may not assign or force a rank")
    rules = registry.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ExceptionRegistryError("Registry rules must be a non-empty list")

    seen_ids: set[str] = set()
    active_rules = []
    for rule in rules:
        _validate_rule(rule)
        exception_id = rule["exception_id"]
        if exception_id in seen_ids:
            raise ExceptionRegistryError(f"Duplicate exception_id: {exception_id}")
        seen_ids.add(exception_id)
        if rule["active"]:
            active_rules.append(rule)

    if registry["status"] == "inactive" and active_rules:
        raise ExceptionRegistryError("Inactive registry cannot contain active rules")
    if registry["status"] == "active" and not active_rules:
        raise ExceptionRegistryError("Active registry must contain an approved active rule")


def _validate_rule(rule: Any) -> None:
    if not isinstance(rule, Mapping) or set(rule) != RULE_KEYS:
        raise ExceptionRegistryError("Exception rule fields do not match schema v1")
    if not isinstance(rule["exception_id"], str) or not EXCEPTION_ID_PATTERN.fullmatch(rule["exception_id"]):
        raise ExceptionRegistryError("Invalid stable exception_id")
    if rule["rule_version"] != "1.0":
        raise ExceptionRegistryError(f"Unsupported rule version: {rule['exception_id']}")
    if rule["status"] not in RULE_STATES:
        raise ExceptionRegistryError(f"Invalid rule status: {rule['exception_id']}")
    if not isinstance(rule["active"], bool):
        raise ExceptionRegistryError(f"Rule active flag must be boolean: {rule['exception_id']}")

    trigger = rule["trigger"]
    if not isinstance(trigger, Mapping) or set(trigger) != {"match_type", "field", "exact_value"}:
        raise ExceptionRegistryError(f"Invalid exact-span trigger: {rule['exception_id']}")
    if trigger["match_type"] != "exact_complete_span" or trigger["field"] != "statement_text_verbatim":
        raise ExceptionRegistryError(f"Exception trigger must use the exact complete statement span: {rule['exception_id']}")
    if not isinstance(trigger["exact_value"], str) or not trigger["exact_value"]:
        raise ExceptionRegistryError(f"Empty exact trigger: {rule['exception_id']}")

    scope = rule["scope"]
    required_scope = {
        "unit",
        "interpretation_dimension",
        "target_eligibility",
        "requires_confirmed_candidate_identity",
        "requires_human_confirmed_statement_span",
        "requires_verified_source_text",
    }
    dimensions = {
        "compound_grade_qualification",
        "attributed_evaluator_wording",
        "grade_qualification",
        "companion_status",
        "specific_transmission_criticism",
    }
    if not isinstance(scope, Mapping) or set(scope) != required_scope:
        raise ExceptionRegistryError(f"Exception scope fields are incomplete: {rule['exception_id']}")
    if (
        scope["unit"] != "confirmed_statement_span"
        or scope["interpretation_dimension"] not in dimensions
        or scope["target_eligibility"] != "not_assessed"
        or any(scope[key] is not True for key in (
            "requires_confirmed_candidate_identity",
            "requires_human_confirmed_statement_span",
            "requires_verified_source_text",
        ))
    ):
        raise ExceptionRegistryError(f"Exception scope must require all source gates: {rule['exception_id']}")

    actions = rule["actions"]
    if not isinstance(actions, list) or not actions or any(not isinstance(action, str) for action in actions):
        raise ExceptionRegistryError(f"Invalid advisory actions: {rule['exception_id']}")
    if len(actions) != len(set(actions)) or any(action not in ALLOWED_ACTIONS for action in actions):
        raise ExceptionRegistryError(f"Invalid advisory actions: {rule['exception_id']}")
    if not isinstance(rule["rationale"], str) or not rule["rationale"].strip():
        raise ExceptionRegistryError(f"Missing rationale: {rule['exception_id']}")
    if not isinstance(rule["expected_behavior"], str) or not rule["expected_behavior"].strip():
        raise ExceptionRegistryError(f"Missing expected behavior: {rule['exception_id']}")
    refs = rule["supporting_pilot_refs"]
    if not isinstance(refs, list) or not refs or any(not isinstance(ref, str) for ref in refs):
        raise ExceptionRegistryError(f"Missing or invalid pilot references: {rule['exception_id']}")
    if len(refs) != len(set(refs)):
        raise ExceptionRegistryError(f"Missing or duplicated pilot references: {rule['exception_id']}")
    if any(not PILOT_REF_PATTERN.fullmatch(ref) for ref in refs):
        raise ExceptionRegistryError(f"Invalid pilot reference: {rule['exception_id']}")
    if rule["evidence_status"] != "pilot_pattern_only":
        raise ExceptionRegistryError(f"Exception evidence must remain qualified as pilot-only: {rule['exception_id']}")

    approval = rule["approval"]
    if not isinstance(approval, Mapping) or set(approval) != {
        "status",
        "approved_by",
        "approved_on",
        "approval_reference",
    }:
        raise ExceptionRegistryError(f"Invalid approval record: {rule['exception_id']}")
    if approval["status"] not in {"not_approved", "approved"}:
        raise ExceptionRegistryError(f"Invalid approval state: {rule['exception_id']}")
    approval_metadata = ("approved_by", "approved_on", "approval_reference")
    if any(approval[field] is not None and not isinstance(approval[field], str) for field in approval_metadata):
        raise ExceptionRegistryError(f"Invalid approval metadata: {rule['exception_id']}")
    if rule["status"] == "retired" and rule["active"]:
        raise ExceptionRegistryError(f"Retired rules cannot be active: {rule['exception_id']}")
    if (rule["status"] == "approved") != (approval["status"] == "approved"):
        raise ExceptionRegistryError(f"Approval state and rule status disagree: {rule['exception_id']}")
    if approval["status"] == "approved":
        if not all(isinstance(approval[field], str) and approval[field].strip() for field in approval_metadata):
            raise ExceptionRegistryError(f"Approval evidence is required: {rule['exception_id']}")
        try:
            date.fromisoformat(approval["approved_on"])
        except (TypeError, ValueError) as exc:
            raise ExceptionRegistryError(f"Invalid approval date: {rule['exception_id']}") from exc
    elif any(approval[field] is not None for field in approval_metadata):
        raise ExceptionRegistryError(
            f"Approval metadata must be null while status is not_approved: {rule['exception_id']}"
        )
    if rule["active"]:
        if rule["status"] != "approved" or approval["status"] != "approved":
            raise ExceptionRegistryError(f"Human approval is required before activation: {rule['exception_id']}")


def inspect_exception_rules(
    statement_text: str,
    registry: Mapping[str, Any],
    *,
    context: Mapping[str, Any] | None = None,
    base_result: Mapping[str, Any] | None = None,
    simulate_proposed: bool = False,
) -> dict[str, Any]:
    """Preview exact exception matches without applying them to the base generator.

    ``simulate_proposed`` is intended for isolated tests and review only. The
    production proposal generator does not import or call this module.
    """
    validate_exception_registry(registry)
    preserved_base = deepcopy(dict(base_result)) if base_result is not None else None
    inactive_result = {
        "status": "inactive",
        "matched_exception_ids": [],
        "proposed_actions": [],
        "actions_applied_to_generator": False,
        "base_result_before": preserved_base,
        "simulated_effect": {"decision": "no_change", "base_result": deepcopy(preserved_base)},
    }
    if not simulate_proposed:
        return inactive_result

    matches = [
        rule
        for rule in registry["rules"]
        if rule["status"] != "retired" and rule["trigger"]["exact_value"] == statement_text
    ]
    match_ids = [rule["exception_id"] for rule in matches]
    if not matches:
        return {
            **inactive_result,
            "status": "no_match",
            "simulated_effect": {"decision": "no_exception_match", "base_result": deepcopy(preserved_base)},
        }
    if len(matches) > 1:
        return {
            **inactive_result,
            "status": "conflict_abstain",
            "matched_exception_ids": match_ids,
            "simulated_effect": {
                "decision": "abstain_for_review",
                "base_match_suppressed": True,
                "taqrib_rank_number": None,
            },
        }

    rule = matches[0]
    if not _scope_satisfied(rule, context or {}):
        return {
            **inactive_result,
            "status": "preconditions_not_met",
            "matched_exception_ids": match_ids,
            "proposed_actions": ["abstain_for_review"],
            "simulated_effect": {
                "decision": "abstain_for_review",
                "base_match_suppressed": True,
                "taqrib_rank_number": None,
            },
        }

    actions = list(rule["actions"])
    simulated_effect = _simulate_actions(actions, preserved_base)
    return {
        "status": "proposed_match",
        "matched_exception_ids": match_ids,
        "proposed_actions": actions,
        "actions_applied_to_generator": False,
        "base_result_before": preserved_base,
        "simulated_effect": simulated_effect,
    }


def _scope_satisfied(rule: Mapping[str, Any], context: Mapping[str, Any]) -> bool:
    scope = rule["scope"]
    required_context = {
        "requires_confirmed_candidate_identity": "candidate_identity_confirmed",
        "requires_human_confirmed_statement_span": "statement_span_human_confirmed",
        "requires_verified_source_text": "source_text_verified",
    }
    return all(context.get(context_key) is True for scope_key, context_key in required_context.items() if scope[scope_key])


def _simulate_actions(actions: list[str], base_result: dict[str, Any] | None) -> dict[str, Any]:
    """Describe proposed effects for tests; never mutates the base result."""
    if "abstain_for_review" in actions:
        return {
            "decision": "abstain_for_review",
            "base_match_suppressed": "suppress_base_match" in actions,
            "taqrib_rank_number": None,
        }
    if "preserve_qualification" in actions:
        return {
            "decision": "preserve_base_result",
            "base_result": deepcopy(base_result),
        }
    return {
        "decision": "advisory_only",
        "base_result": deepcopy(base_result),
        "taqrib_rank_number": None,
    }
