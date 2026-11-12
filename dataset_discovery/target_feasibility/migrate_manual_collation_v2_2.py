#!/usr/bin/env python3
"""Create a non-destructive Schema v2.2 review scaffold from the frozen pilot."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import shutil
import sys
import uuid
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = ROOT / "dataset_discovery" / "target_feasibility" / "manual_collation_pilot_10"
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "data"
    / "2_interim"
    / "shamela4_narrator_audit"
    / "manual_annotation_working"
    / "manual_collation_pilot_10_v2_2_impl_r1"
)
IMPLEMENTATION_VERSION = "2.2.1"

FROZEN_NAME = "MANUAL_COLLATION_PILOT_10.csv"
WORKING_NAME = "MANUAL_COLLATION_PILOT_10_WORKING.csv"
KEY_NAME = "MANUAL_COLLATION_PILOT_10_KEY.csv"
MANIFEST_NAME = "MANUAL_COLLATION_PILOT_10_MANIFEST.json"

EXPECTED_INPUT_HASHES = {
    FROZEN_NAME: "78cb15eb72b04c1b2c0d2e350e375615236df22a2918c38256977ccccffae958",
    WORKING_NAME: "4b3f731b5a799c1df499c57391f4b502fcee84f129c2bae2e77325e738a04548",
    KEY_NAME: "9eccd4533cb4482390a41861955e3636453d1f0bc39e8aac544f748f4dcc0684",
    MANIFEST_NAME: "9339ad77f1fa18e204b443e9a3ec888d6ec56924b801b85d94f3bb8ea49bf72d",
}

EXPECTED_HEADERS = [
    "audit_record_id",
    "dataset_name",
    "dataset_narrator_id",
    "dataset_narrator_name",
    "original_grade_field",
    "original_grade_verbatim",
    "original_source_location",
    "taqrib_book_id",
    "taqrib_printed_page_from_corpus",
    "taqrib_entry_number",
    "taqrib_entry_text_verbatim",
    "retrieval_note",
    "taqrib_printed_page",
    "taqrib_entry_name_verbatim",
    "taqrib_grade_verbatim",
    "taqrib_qualification_verbatim",
    "taqrib_rank_number",
    "taqrib_identity_match_status",
    "taqrib_text_match_status",
    "assessment_author",
    "assessment_attribution_status",
    "compiler_or_transmitter",
    "editorial_material_status",
    "attribution_evidence_verbatim",
    "source_locator",
    "source_verification_status",
    "textual_fidelity",
    "attribution_fidelity",
    "identity_fidelity",
    "record_disposition",
    "input_eligibility",
    "exclusion_or_quarantine_reason",
    "reviewer_notes",
    "corroboration_status",
]

CONTEXT_COLUMNS = [
    "audit_record_id",
    "dataset_name",
    "dataset_narrator_id",
    "dataset_narrator_name",
    "original_grade_field",
    "original_grade_verbatim",
    "original_source_location",
    "taqrib_book_id",
    "taqrib_printed_page_from_corpus",
    "taqrib_entry_text_verbatim",
    "retrieval_note",
]

OUTPUT_TABLES: dict[str, list[str]] = {
    "cases.csv": [
        "audit_record_id",
        "dataset_name",
        "dataset_narrator_id",
        "dataset_narrator_name",
        "original_grade_field",
        "original_grade_verbatim",
        "original_grade_source_location",
        "original_value_status",
    ],
    "candidate_entries.csv": [
        "audit_record_id",
        "candidate_entry_id",
        "within_case_candidate_index",
        "dataset_name",
        "dataset_narrator_id",
        "dataset_narrator_name",
        "original_grade_field",
        "original_grade_verbatim",
        "original_grade_source_location",
        "taqrib_book_id",
        "taqrib_printed_page_from_corpus",
        "taqrib_entry_text_verbatim",
        "candidate_entry_text_status",
        "source_entry_number_from_text",
        "source_locator_verbatim",
        "canonical_source_locator_key",
        "candidate_field_source_correspondence",
        "candidate_comparison_source_span",
        "candidate_comparison_source_span_status",
        "candidate_comparison_rationale",
        "candidate_comparison_locator",
        "identity_match_status",
        "identity_evidence_verbatim",
        "identity_evidence_text_status",
        "identity_evidence_record_id",
        "identity_evidence_locator",
        "identity_evidence_independence_rationale",
        "taqrib_source_record_id",
        "legacy_rank_candidate",
        "legacy_reviewer_notes_verbatim",
    ],
    "statements.csv": [
        "audit_record_id",
        "candidate_entry_id",
        "statement_id",
        "statement_record_status",
        "statement_type",
        "statement_text_verbatim",
        "statement_text_status",
        "grade_base_verbatim",
        "grade_base_text_status",
        "grade_qualification_verbatim",
        "grade_qualification_text_status",
        "taqrib_rank_number",
        "rank_status",
        "taqrib_statement_validity",
        "target_task_scope",
        "statement_source_correspondence",
        "statement_source_span_verbatim",
        "statement_source_span_status",
        "statement_source_correspondence_rationale",
        "statement_source_locator",
        "statement_source_evidence_record_id",
        "historical_input_eligibility",
        "historical_input_eligibility_rationale",
        "target_task_scope_rationale",
        "corroboration_status",
        "temporal_policy_id",
        "temporal_policy_version",
        "temporal_policy_result",
    ],
    "attribution_links.csv": [
        "attribution_link_id",
        "statement_id",
        "named_historical_evaluator",
        "evaluator_value_status",
        "intermediary_transmitter",
        "transmitter_value_status",
        "surviving_wording_author",
        "wording_author_value_status",
        "attribution_form",
        "passage_evaluator_naming_status",
        "historical_evaluator_attribution_status",
        "transmission_route_status",
        "compiler_authorship_status",
        "attribution_evidence_verbatim",
        "attribution_evidence_text_status",
        "attribution_evidence_record_id",
        "attribution_evidence_locator",
        "transmission_route_evidence_record_id",
    ],
    "sources.csv": [
        "source_record_id",
        "candidate_entry_id",
        "source_work_id",
        "source_work_title",
        "consulted_edition",
        "consulted_editor",
        "consulted_witness_id",
        "consulted_witness_type",
        "consulted_corpus_artifact_id",
        "consulted_corpus_artifact_type",
        "source_page_numbering_note",
        "source_work_author_compiler",
        "source_author_metadata_status",
        "source_locator_verbatim",
        "canonical_source_locator_key",
        "source_verification_status",
        "edition_variant_status",
        "edition_metadata_evidence_record_id",
    ],
    "source_evidence.csv": [
        "evidence_record_id",
        "source_record_id",
        "candidate_entry_id",
        "statement_id",
        "attribution_link_id",
        "evidence_role",
        "evidence_text_verbatim",
        "evidence_text_status",
        "source_locator",
    ],
    "date_claims.csv": [
        "date_claim_id",
        "date_subject_role",
        "date_kind",
        "date_value",
        "date_calendar",
        "date_precision",
        "date_claim_status",
        "evidence_record_id",
    ],
    "feature_sources.csv": [
        "feature_source_id",
        "statement_id",
        "source_record_id",
        "feature_input_name",
        "temporal_date_claim_id",
        "feature_inclusion_status",
        "feature_exclusion_policy_id",
        "feature_exclusion_policy_version",
        "decision_rationale",
    ],
    "migration_mapping.csv": [
        "source_file",
        "input_row_index",
        "audit_record_id",
        "within_case_candidate_index",
        "taqrib_entry_text_sha256",
        "source_locator_verbatim",
        "canonical_source_locator_key",
        "candidate_entry_id",
        "statement_id",
        "migration_join_status",
    ],
    "legacy_v1_values.csv": [
        "source_file",
        "input_row_index",
        "audit_record_id",
        "candidate_entry_id",
        "field_name",
        "legacy_value",
        "is_empty_cell",
    ],
    "column_mapping.csv": [
        "source_file",
        "source_column",
        "target_table",
        "target_column",
        "mapping_type",
        "transformation_rule",
        "review_required",
    ],
}

FIELD_ENUMS: dict[str, tuple[str, ...]] = {
    "candidate_entry_text_status": ("transcribed", "not_found_after_review", "unavailable", "unresolved", "not_assessed"),
    "original_value_status": ("present", "absent_in_source", "unavailable", "not_assessed"),
    "evidence_role": ("identity", "passage_text", "historical_attribution", "transmission_route", "temporal_date", "edition_metadata", "other"),
    "date_kind": ("evaluator_lifespan_or_death", "approximate_judgment_date", "source_work_composition_date", "surviving_witness_date", "modern_edition_publication_date"),
    "statement_record_status": ("provisional_work_item", "reviewed_statement", "superseded_placeholder"),
    "statement_type": ("standardized_narrator_grade", "qualified_narrator_grade", "attributed_earlier_critic_judgment", "descriptive_or_generational_status", "specific_transmission_criticism", "biographical_or_factual_statement", "mixed_or_unclear", "not_assessed"),
    "statement_text_status": ("transcribed", "not_transcribed", "unavailable", "unresolved", "not_assessed"),
    "evidence_text_status": ("transcribed", "not_found_after_review", "unavailable", "unresolved", "not_assessed", "not_applicable"),
    "identity_match_status": ("confirmed", "probable", "unresolved", "mismatch", "not_found", "not_assessed"),
    "candidate_field_source_correspondence": ("exact", "minor_variation", "partial_or_truncated", "substantial_difference", "not_found", "unresolved", "not_assessed"),
    "candidate_comparison_source_span_status": ("transcribed", "not_found_after_review", "unavailable", "unresolved", "not_assessed"),
    "statement_source_correspondence": ("exact", "minor_variation", "substantial_difference", "not_found", "unresolved", "not_assessed"),
    "rank_status": ("assigned", "unranked", "not_applicable", "not_assessed", "unresolved", "not_found"),
    "evaluator_value_status": ("identified", "collective_unidentified", "none_named", "unknown", "not_assessed", "not_applicable"),
    "transmitter_value_status": ("identified", "none_identified", "unknown", "not_assessed", "not_applicable"),
    "wording_author_value_status": ("identified", "unknown", "not_assessed", "not_applicable"),
    "source_author_metadata_status": ("recorded", "unknown", "not_assessed", "not_applicable"),
    "attribution_form": ("direct_quotation", "explicit_attribution", "collective_attribution", "compiler_synthesis", "unclear", "not_applicable", "not_assessed"),
    "passage_evaluator_naming_status": ("explicit_individual_named", "collective_only", "no_evaluator_named", "unclear", "not_assessed", "not_applicable"),
    "historical_evaluator_attribution_status": ("supported_by_verified_source_or_route", "explicitly_reported_but_historically_unverified", "contradicted", "unresolved", "not_assessed", "not_applicable"),
    "transmission_route_status": ("documented_traceable", "named_authority_route_unverified", "route_examined_not_found", "unresolved", "not_assessed", "not_applicable"),
    "compiler_authorship_status": ("supported", "contradicted", "unresolved", "not_assessed", "not_applicable"),
    "taqrib_statement_validity": ("supported_taqrib_statement", "not_supported_in_taqrib", "unresolved", "not_assessed"),
    "target_task_scope": ("ordinary_grade_candidate", "status_only_candidate", "not_in_defined_task", "unresolved", "not_assessed"),
    "source_verification_status": ("verified_in_corpus", "verified_external_edition", "unverified", "contradicted", "not_assessed"),
    "edition_variant_status": ("no_variant_marked", "variant_marked_in_edition_metadata", "editorial_insertion_verified", "editorial_note_or_footnote", "unclear", "not_assessed", "not_applicable"),
    "date_claim_status": ("recorded_in_source", "unknown", "unresolved", "not_assessed", "not_applicable"),
    "temporal_policy_result": ("passes_policy", "fails_policy", "cannot_assess", "not_applicable"),
    "historical_input_eligibility": ("eligible", "quarantined_pending_verification", "ineligible", "not_applicable", "not_assessed"),
    "corroboration_status": ("independent_corroboration", "dependent_corroboration", "unresolved_corroboration", "not_examined", "not_applicable"),
    "feature_inclusion_status": ("included", "excluded", "quarantined", "not_assessed"),
    "migration_join_status": ("matched", "missing_component", "duplicate_key", "ambiguous_match", "context_mismatch", "not_assessed"),
}

PRIMARY_KEYS = {
    "cases.csv": ("audit_record_id",),
    "candidate_entries.csv": ("candidate_entry_id",),
    "statements.csv": ("statement_id",),
    "attribution_links.csv": ("attribution_link_id",),
    "sources.csv": ("source_record_id",),
    "source_evidence.csv": ("evidence_record_id",),
    "date_claims.csv": ("date_claim_id",),
    "feature_sources.csv": ("feature_source_id",),
    "migration_mapping.csv": ("source_file", "input_row_index", "candidate_entry_id"),
    "legacy_v1_values.csv": ("source_file", "input_row_index", "field_name"),
    "column_mapping.csv": ("source_file", "source_column", "target_table", "target_column"),
}

TEXT_STATUS_PAIRS = {
    "candidate_entries.csv": (
        ("taqrib_entry_text_verbatim", "candidate_entry_text_status"),
        ("candidate_comparison_source_span", "candidate_comparison_source_span_status"),
        ("identity_evidence_verbatim", "identity_evidence_text_status"),
    ),
    "statements.csv": (
        ("statement_text_verbatim", "statement_text_status"),
        ("grade_base_verbatim", "grade_base_text_status"),
        ("grade_qualification_verbatim", "grade_qualification_text_status"),
        ("statement_source_span_verbatim", "statement_source_span_status"),
    ),
    "attribution_links.csv": (("attribution_evidence_verbatim", "attribution_evidence_text_status"),),
    "source_evidence.csv": (("evidence_text_verbatim", "evidence_text_status"),),
}

FIELD_ENUM_ALIASES = {
    "statement_source_span_status": "evidence_text_status",
    "identity_evidence_text_status": "evidence_text_status",
    "attribution_evidence_text_status": "evidence_text_status",
    "grade_base_text_status": "evidence_text_status",
    "grade_qualification_text_status": "evidence_text_status",
}

REQUIRED_NONEMPTY = {
    "cases.csv": ("audit_record_id", "dataset_name", "dataset_narrator_id", "dataset_narrator_name", "original_grade_field", "original_value_status"),
    "candidate_entries.csv": (
        "audit_record_id", "candidate_entry_id", "within_case_candidate_index", "dataset_name",
        "dataset_narrator_id", "dataset_narrator_name", "original_grade_field", "taqrib_book_id",
        "taqrib_printed_page_from_corpus", "candidate_entry_text_status", "source_entry_number_from_text",
        "canonical_source_locator_key", "candidate_field_source_correspondence", "candidate_comparison_source_span_status",
        "identity_match_status", "identity_evidence_text_status", "taqrib_source_record_id",
    ),
    "statements.csv": (
        "audit_record_id", "candidate_entry_id", "statement_id", "statement_record_status", "statement_type",
        "statement_text_status", "grade_base_text_status", "grade_qualification_text_status", "rank_status",
        "taqrib_statement_validity", "target_task_scope", "statement_source_correspondence",
        "statement_source_span_status", "historical_input_eligibility", "corroboration_status", "temporal_policy_result",
    ),
    "attribution_links.csv": (
        "attribution_link_id", "statement_id", "evaluator_value_status", "transmitter_value_status",
        "wording_author_value_status", "attribution_form", "passage_evaluator_naming_status",
        "historical_evaluator_attribution_status", "transmission_route_status", "compiler_authorship_status",
        "attribution_evidence_text_status",
    ),
    "sources.csv": ("source_record_id", "candidate_entry_id", "source_work_id", "source_work_title", "consulted_edition", "consulted_corpus_artifact_id", "source_author_metadata_status", "source_verification_status", "edition_variant_status"),
    "source_evidence.csv": ("evidence_record_id", "source_record_id", "evidence_role", "evidence_text_status"),
    "date_claims.csv": ("date_claim_id", "date_subject_role", "date_kind", "date_claim_status"),
    "feature_sources.csv": (
        "feature_source_id", "statement_id", "source_record_id", "feature_input_name", "temporal_date_claim_id",
        "feature_inclusion_status", "feature_exclusion_policy_id", "feature_exclusion_policy_version", "decision_rationale",
    ),
    "migration_mapping.csv": ("source_file", "input_row_index", "audit_record_id", "within_case_candidate_index", "candidate_entry_id", "statement_id", "migration_join_status"),
    "legacy_v1_values.csv": ("source_file", "input_row_index", "audit_record_id", "candidate_entry_id", "field_name", "is_empty_cell"),
    "column_mapping.csv": ("source_file", "source_column", "target_table", "target_column", "mapping_type", "transformation_rule", "review_required"),
}

FIELD_RULES = {
    "taqrib_rank_number": "Nullable integer 1..12; present iff rank_status=assigned.",
    "identity_evidence_record_id": "Must link to transcribed identity evidence for this candidate from a verified source work distinct from the Taqrib target work.",
    "candidate_comparison_source_span": "Non-empty iff candidate_comparison_source_span_status=transcribed.",
    "candidate_comparison_rationale": "Required for an assessed candidate-field comparison.",
    "candidate_comparison_locator": "Required for an assessed candidate-field comparison.",
    "statement_source_span_verbatim": "Non-empty iff statement_source_span_status=transcribed.",
    "statement_source_correspondence_rationale": "Required for an assessed statement-to-passage comparison.",
    "statement_source_locator": "Required for an assessed statement-to-passage comparison.",
    "statement_source_evidence_record_id": "Must link to passage evidence attached to this statement.",
    "attribution_evidence_record_id": "Must link to evidence attached to this attribution record.",
    "transmission_route_evidence_record_id": "Required when transmission_route_status=documented_traceable.",
    "source_work_author_compiler": "Source-work metadata only; never substitute for surviving_wording_author.",
    "edition_metadata_evidence_record_id": "Must link to source metadata evidence when edition or editorial status is assessed.",
    "temporal_date_claim_id": "Must link to a recorded date claim with its own evidence record.",
}

SPEC_INVENTORY_FIELDS = {
    # This inventory expands every logical-table item in frozen-spec section 3
    # into the concrete normalized output columns that carry it.
    "Cases": (
        "audit_record_id", "dataset_name", "dataset_narrator_id", "dataset_narrator_name",
        "original_grade_field", "original_grade_verbatim", "original_grade_source_location", "original_value_status",
    ),
    "Candidate entries": (
        "candidate_entry_id", "audit_record_id", "within_case_candidate_index", "dataset_name",
        "dataset_narrator_id", "dataset_narrator_name", "original_grade_field", "original_grade_verbatim",
        "original_grade_source_location", "taqrib_book_id", "taqrib_printed_page_from_corpus",
        "taqrib_entry_text_verbatim", "candidate_entry_text_status", "source_locator_verbatim",
        "canonical_source_locator_key", "identity_match_status", "identity_evidence_verbatim",
        "identity_evidence_text_status", "identity_evidence_record_id", "identity_evidence_locator",
        "candidate_field_source_correspondence", "candidate_comparison_source_span",
        "candidate_comparison_source_span_status", "candidate_comparison_rationale", "candidate_comparison_locator",
        "taqrib_source_record_id",
    ),
    "Statements and research use": (
        "statement_id", "candidate_entry_id", "statement_record_status", "statement_type",
        "statement_text_verbatim", "statement_text_status", "grade_base_verbatim", "grade_base_text_status",
        "grade_qualification_verbatim", "grade_qualification_text_status", "taqrib_rank_number", "rank_status",
        "taqrib_statement_validity", "target_task_scope", "target_task_scope_rationale",
        "statement_source_correspondence", "statement_source_span_verbatim", "statement_source_span_status",
        "statement_source_correspondence_rationale", "statement_source_locator", "statement_source_evidence_record_id",
        "historical_input_eligibility", "historical_input_eligibility_rationale", "corroboration_status",
        "temporal_policy_id", "temporal_policy_version", "temporal_policy_result",
    ),
    "Attribution links": (
        "attribution_link_id", "statement_id", "passage_evaluator_naming_status", "attribution_form",
        "historical_evaluator_attribution_status", "transmission_route_status", "named_historical_evaluator",
        "evaluator_value_status", "intermediary_transmitter", "transmitter_value_status", "surviving_wording_author",
        "wording_author_value_status", "attribution_evidence_verbatim", "attribution_evidence_text_status",
        "attribution_evidence_record_id", "attribution_evidence_locator", "transmission_route_evidence_record_id",
        "compiler_authorship_status",
    ),
    "Sources": (
        "source_record_id", "source_work_id", "source_work_title", "consulted_edition", "consulted_editor",
        "consulted_witness_id", "consulted_witness_type", "consulted_corpus_artifact_id",
        "consulted_corpus_artifact_type", "source_page_numbering_note", "source_work_author_compiler",
        "source_author_metadata_status", "source_locator_verbatim", "source_verification_status",
        "edition_variant_status", "edition_metadata_evidence_record_id",
    ),
    "Evidence and dates": (
        "evidence_record_id", "source_record_id", "candidate_entry_id", "statement_id", "attribution_link_id",
        "evidence_role", "evidence_text_verbatim", "evidence_text_status", "source_locator", "date_claim_id",
        "date_subject_role", "date_kind", "date_value", "date_calendar", "date_precision", "date_claim_status",
    ),
    "Feature-source firewall": (
        "feature_source_id", "statement_id", "source_record_id", "feature_input_name", "temporal_date_claim_id",
        "feature_inclusion_status", "feature_exclusion_policy_id", "feature_exclusion_policy_version", "decision_rationale",
    ),
}


def build_schema_field_registry() -> dict[str, object]:
    """Return a machine-readable v2.2 field/type/nullability/rule registry."""
    fields: list[dict[str, object]] = []
    tables: dict[str, dict[str, dict[str, object]]] = {}
    frozen_field_names = set(FIELD_ENUMS)
    for inventory_fields in SPEC_INVENTORY_FIELDS.values():
        frozen_field_names.update(inventory_fields)
    for table_name, columns in OUTPUT_TABLES.items():
        tables[table_name] = {}
        for column in columns:
            enum_name = column if column in FIELD_ENUMS else FIELD_ENUM_ALIASES.get(column)
            enum_values = list(FIELD_ENUMS[enum_name]) if enum_name else []
            if column == "is_empty_cell":
                field_type = "boolean"
            elif column in {"within_case_candidate_index", "source_entry_number_from_text", "input_row_index", "taqrib_rank_number"}:
                field_type = "nullable_integer" if column == "taqrib_rank_number" else "integer"
            elif column.endswith("sha256"):
                field_type = "sha256_hex"
            elif column == "date_value":
                field_type = "date_or_range_text"
            elif enum_name:
                field_type = "enum"
            else:
                field_type = "string"
            nullable = column not in REQUIRED_NONEMPTY[table_name]
            if column in FIELD_RULES:
                rule = FIELD_RULES[column]
            elif enum_name:
                rule = f"Required controlled value; allowed values are the v2.2 {enum_name} registry."
            elif column in PRIMARY_KEYS.get(table_name, ()):
                rule = "Required non-empty unique identifier/key component."
            elif "verbatim" in column or column.endswith("_span"):
                rule = "Exact source text or null; paired status controls whether text is present."
            else:
                rule = "Nullable string unless marked required; preserve source meaning without normalization."
            item = {
                "frozen_schema_field": column if column in frozen_field_names else None,
                "field_origin": "frozen_schema" if column in frozen_field_names else "implementation_support",
                "output_table": table_name,
                "output_column": column,
                "field_type": field_type,
                "allowed_enum_values": enum_values,
                "nullable": nullable,
                "nullability": "nullable" if nullable else "required_nonempty",
                "validation_rule": rule,
            }
            fields.append(item)
            tables[table_name][column] = item
    return {
        "schema_name": "manual_collation_schema",
        "schema_version": "2.2",
        "implementation_version": IMPLEMENTATION_VERSION,
        "frozen_inventory_fields": {name: list(fields) for name, fields in SPEC_INVENTORY_FIELDS.items()},
        "enums": {name: list(values) for name, values in sorted(FIELD_ENUMS.items())},
        "tables": tables,
        "fields": fields,
    }

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


class MigrationError(RuntimeError):
    """Raised when migration validation fails closed."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = list(reader.fieldnames or [])
        rows = list(reader)
    if not headers:
        raise MigrationError(f"CSV has no header: {path.name}")
    if any(None in row for row in rows):
        raise MigrationError(f"CSV row has more values than headers: {path.name}")
    return headers, rows


def _digits(value: str) -> str:
    return value.translate(ARABIC_DIGITS)


def entry_number_from_text(text: str) -> int:
    match = re.match(r"^\s*([0-9٠-٩۰-۹]+)\s*-", text)
    if not match:
        raise MigrationError("cannot parse leading entry number from candidate entry text")
    return int(_digits(match.group(1)))


def canonical_locator_key(book_id: str, page: str, entry: int) -> tuple[int, int, int]:
    try:
        canonical = (int(_digits(str(book_id))), int(_digits(str(page))), int(entry))
    except (TypeError, ValueError) as exc:
        raise MigrationError("invalid book/page/entry locator component") from exc
    if any(part <= 0 for part in canonical):
        raise MigrationError("book/page/entry locator components must be positive")
    return canonical


def parse_working_locator(locator: str) -> tuple[int, int]:
    match = re.fullmatch(r"\s*Taqrib\s*,\s*p\.\s*([0-9٠-٩۰-۹]+)\s*,\s*entry\s*([0-9٠-٩۰-۹]+)\s*", locator, re.IGNORECASE)
    if not match:
        raise MigrationError(f"unrecognized working source_locator: {locator!r}")
    return int(_digits(match.group(1))), int(_digits(match.group(2)))


def assert_unique_composite_keys(keys: Sequence[tuple[object, ...]]) -> None:
    seen: set[tuple[object, ...]] = set()
    for key in keys:
        if key in seen:
            raise MigrationError(f"duplicate composite key: {key!r}")
        seen.add(key)


def ordinary_grade_candidate_conditions_pass(
    candidate: Mapping[str, str],
    statement: Mapping[str, str],
    attribution: Mapping[str, str],
    source: Mapping[str, str],
    *,
    evidence_by_id: Mapping[str, Mapping[str, str]] | None = None,
    sources_by_id: Mapping[str, Mapping[str, str]] | None = None,
) -> bool:
    """Fail closed unless every ordinary-grade condition has linked evidence."""
    evidence_by_id = evidence_by_id or {}
    sources_by_id = sources_by_id or {}

    def text_is_transcribed(row: Mapping[str, str], text_field: str, status_field: str) -> bool:
        return row.get(status_field) == "transcribed" and bool(str(row.get(text_field, "")).strip())

    def evidence_is_valid(
        evidence_id: str,
        *,
        role: str,
        owner_field: str,
        owner_id: str,
        source_id: str | None = None,
        text: str | None = None,
        locator: str | None = None,
    ) -> bool:
        record = evidence_by_id.get(evidence_id)
        if not record or not evidence_id:
            return False
        if record.get("evidence_role") != role or record.get("evidence_text_status") != "transcribed":
            return False
        if not str(record.get("evidence_text_verbatim", "")).strip() or not str(record.get("source_locator", "")).strip():
            return False
        if record.get(owner_field) != owner_id:
            return False
        if source_id and record.get("source_record_id") != source_id:
            return False
        if text is not None and record.get("evidence_text_verbatim") != text:
            return False
        if locator is not None and record.get("source_locator") != locator:
            return False
        evidence_source = sources_by_id.get(record.get("source_record_id", ""))
        return bool(evidence_source) and evidence_source.get("source_verification_status") in {
            "verified_in_corpus",
            "verified_external_edition",
        }

    try:
        raw_rank = str(statement.get("taqrib_rank_number", ""))
        if not re.fullmatch(r"(?:[1-9]|1[0-2])", raw_rank):
            return False
        rank = int(raw_rank)
    except (TypeError, ValueError):
        return False

    candidate_id = candidate.get("candidate_entry_id", "")
    statement_id = statement.get("statement_id", "")
    attribution_id = attribution.get("attribution_link_id", "")
    target_source_id = source.get("source_record_id", "")
    identity_evidence_id = candidate.get("identity_evidence_record_id", "")
    identity_evidence = evidence_by_id.get(identity_evidence_id, {})
    identity_source = sources_by_id.get(identity_evidence.get("source_record_id", ""), {})
    target_work_id = source.get("source_work_id", "")

    def role_value_consistent(row: Mapping[str, str], value_field: str, status_field: str) -> bool:
        value = str(row.get(value_field, "") or "").strip()
        status = row.get(status_field, "")
        if status == "identified":
            return bool(value)
        return not value

    identity_supported_independently = all(
        (
            candidate.get("identity_match_status") == "confirmed",
            text_is_transcribed(candidate, "identity_evidence_verbatim", "identity_evidence_text_status"),
            bool(candidate.get("identity_evidence_independence_rationale", "").strip()),
            bool(candidate.get("identity_evidence_locator", "").strip()),
            evidence_is_valid(
                identity_evidence_id,
                role="identity",
                owner_field="candidate_entry_id",
                owner_id=candidate_id,
                text=candidate.get("identity_evidence_verbatim", ""),
                locator=candidate.get("identity_evidence_locator", ""),
            ),
            identity_source.get("source_record_id") != target_source_id,
            bool(identity_source.get("source_work_id")),
            identity_source.get("source_work_id") != target_work_id,
            identity_source.get("source_work_title", "").strip(),
            identity_source.get("consulted_edition", "").strip(),
            identity_source.get("source_locator_verbatim", "").strip(),
        )
    )

    statement_source_evidence_id = statement.get("statement_source_evidence_record_id", "")
    attribution_evidence_id = attribution.get("attribution_evidence_record_id", "")
    return all(
        (
            identity_supported_independently,
            candidate.get("taqrib_source_record_id") == target_source_id,
            candidate.get("candidate_entry_text_status") == "transcribed",
            bool(candidate.get("taqrib_entry_text_verbatim", "").strip()),
            candidate.get("candidate_field_source_correspondence") in {"exact", "minor_variation"},
            text_is_transcribed(candidate, "candidate_comparison_source_span", "candidate_comparison_source_span_status"),
            bool(candidate.get("candidate_comparison_rationale", "").strip()),
            bool(candidate.get("candidate_comparison_locator", "").strip()),
            statement.get("audit_record_id") == candidate.get("audit_record_id"),
            statement.get("candidate_entry_id") == candidate_id,
            statement.get("statement_record_status") == "reviewed_statement",
            statement.get("statement_type") in {"standardized_narrator_grade", "qualified_narrator_grade"},
            text_is_transcribed(statement, "statement_text_verbatim", "statement_text_status"),
            statement.get("taqrib_statement_validity") == "supported_taqrib_statement",
            statement.get("statement_source_correspondence") in {"exact", "minor_variation"},
            text_is_transcribed(statement, "statement_source_span_verbatim", "statement_source_span_status"),
            bool(statement.get("statement_source_correspondence_rationale", "").strip()),
            bool(statement.get("statement_source_locator", "").strip()),
            evidence_is_valid(
                statement_source_evidence_id,
                role="passage_text",
                owner_field="statement_id",
                owner_id=statement_id,
                source_id=target_source_id,
                text=statement.get("statement_source_span_verbatim", ""),
                locator=statement.get("statement_source_locator", ""),
            ),
            statement.get("rank_status") == "assigned",
            2 <= rank <= 12,
            statement.get("target_task_scope") == "ordinary_grade_candidate",
            statement.get("statement_record_status") != "superseded_placeholder",
            statement.get("historical_input_eligibility") == "not_applicable",
            attribution.get("statement_id") == statement_id,
            attribution.get("surviving_wording_author") == "Ibn Hajar",
            attribution.get("wording_author_value_status") == "identified",
            role_value_consistent(attribution, "named_historical_evaluator", "evaluator_value_status"),
            role_value_consistent(attribution, "intermediary_transmitter", "transmitter_value_status"),
            role_value_consistent(attribution, "surviving_wording_author", "wording_author_value_status"),
            attribution.get("evaluator_value_status") == "none_named",
            attribution.get("transmitter_value_status") in {"none_identified", "not_applicable"},
            attribution.get("compiler_authorship_status") == "supported",
            attribution.get("attribution_form") == "compiler_synthesis",
            attribution.get("passage_evaluator_naming_status") == "no_evaluator_named",
            attribution.get("historical_evaluator_attribution_status") == "not_applicable",
            attribution.get("transmission_route_status") == "not_applicable",
            text_is_transcribed(attribution, "attribution_evidence_verbatim", "attribution_evidence_text_status"),
            evidence_is_valid(
                attribution_evidence_id,
                role="passage_text",
                owner_field="attribution_link_id",
                owner_id=attribution_id,
                source_id=target_source_id,
                text=attribution.get("attribution_evidence_verbatim", ""),
                locator=attribution.get("attribution_evidence_locator", ""),
            ),
            source.get("source_verification_status") in {"verified_in_corpus", "verified_external_edition"},
            source.get("edition_variant_status") in {"no_variant_marked", "variant_marked_in_edition_metadata"},
            bool(source.get("source_locator_verbatim", "").strip()),
            bool(source.get("source_work_id", "").strip()),
            bool(source.get("source_work_title", "").strip()),
            bool(source.get("consulted_edition", "").strip()),
            source.get("source_author_metadata_status") != "recorded" or bool(source.get("source_work_author_compiler", "").strip()),
            source.get("source_author_metadata_status") == "recorded" or not source.get("source_work_author_compiler", "").strip(),
        )
    )


def _verify_inputs(input_dir: Path, expected_hashes: Mapping[str, str]) -> tuple[dict[str, bytes], dict[str, str]]:
    payloads: dict[str, bytes] = {}
    actual_hashes: dict[str, str] = {}
    for name in EXPECTED_INPUT_HASHES:
        path = input_dir / name
        if not path.is_file():
            raise MigrationError(f"required input is missing: {path}")
        payload = path.read_bytes()
        digest = sha256_bytes(payload)
        expected = expected_hashes.get(name)
        if expected is None or digest != expected:
            raise MigrationError(f"hash mismatch for {name}: expected {expected}, got {digest}")
        payloads[name] = payload
        actual_hashes[name] = digest
    return payloads, actual_hashes


def _validate_manifest_metadata(manifest_bytes: bytes, frozen_hash: str, key_hash: str) -> dict[str, str]:
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MigrationError("input manifest is not valid UTF-8 JSON") from exc
    recorded = manifest.get("output_sha256", {})
    if recorded.get(FROZEN_NAME) != frozen_hash:
        raise MigrationError("manifest does not record the frozen packet hash")
    if recorded.get(KEY_NAME) != key_hash:
        raise MigrationError("manifest does not record the key hash")
    source_corpus = manifest.get("source_corpus")
    if not isinstance(source_corpus, dict):
        raise MigrationError("input manifest does not contain source-corpus metadata")
    if str(source_corpus.get("book_id", "")) != "3076":
        raise MigrationError("source-corpus book identifier does not match the frozen pilot")
    for required in ("title", "editor", "edition", "pages_jsonl_sha256"):
        if not str(source_corpus.get(required, "")).strip():
            raise MigrationError(f"source-corpus manifest metadata is missing {required}")
    return {str(key): str(value) for key, value in source_corpus.items() if value is not None}


def _entry_key(row: Mapping[str, str], within_index: int, locator: tuple[int, int, int]) -> tuple[object, ...]:
    return (
        row.get("audit_record_id", ""),
        within_index,
        row.get("taqrib_entry_text_verbatim", ""),
        locator,
    )


def _validate_and_join(
    frozen_rows: list[dict[str, str]], working_rows: list[dict[str, str]]
) -> list[dict[str, object]]:
    if len(frozen_rows) != 11 or len(working_rows) != 11:
        raise MigrationError("expected 11 source-entry rows in both CSV inputs")
    if len({row["audit_record_id"] for row in frozen_rows}) != 10:
        raise MigrationError("expected 10 distinct audit_record_id values")
    if len({row["audit_record_id"] for row in working_rows}) != 10:
        raise MigrationError("working file does not contain 10 distinct audit_record_id values")

    joined: list[dict[str, object]] = []
    frozen_counts: Counter[str] = Counter()
    working_counts: Counter[str] = Counter()
    frozen_keys: list[tuple[object, ...]] = []
    working_keys: list[tuple[object, ...]] = []

    for row_index, (frozen, working) in enumerate(zip(frozen_rows, working_rows), start=1):
        if any(frozen.get(column, "") != working.get(column, "") for column in CONTEXT_COLUMNS):
            raise MigrationError(f"pre-populated context mismatch at input row {row_index}")
        audit_id = frozen["audit_record_id"]
        frozen_counts[audit_id] += 1
        working_counts[audit_id] += 1
        if frozen_counts[audit_id] != working_counts[audit_id]:
            raise MigrationError(f"within-case row order mismatch at input row {row_index}")
        within_index = frozen_counts[audit_id]
        entry_number = entry_number_from_text(frozen["taqrib_entry_text_verbatim"])
        frozen_locator = canonical_locator_key(
            frozen["taqrib_book_id"], frozen["taqrib_printed_page_from_corpus"], entry_number
        )
        working_page, working_entry = parse_working_locator(working.get("source_locator", ""))
        working_locator = canonical_locator_key(frozen["taqrib_book_id"], working_page, working_entry)
        if frozen_locator != working_locator:
            raise MigrationError(f"source locator does not match frozen entry at input row {row_index}")
        if _digits(str(working.get("taqrib_entry_number", ""))) != str(entry_number):
            raise MigrationError(f"working entry number does not match full entry text at input row {row_index}")
        if working.get("taqrib_printed_page", "") and _digits(working["taqrib_printed_page"]) != str(working_page):
            raise MigrationError(f"working printed page does not match source locator at input row {row_index}")

        fkey = _entry_key(frozen, within_index, frozen_locator)
        wkey = _entry_key(working, within_index, working_locator)
        frozen_keys.append(fkey)
        working_keys.append(wkey)
        joined.append(
            {
                "frozen": frozen,
                "working": working,
                "input_row_index": row_index,
                "within_case_candidate_index": within_index,
                "entry_number": entry_number,
                "locator": frozen_locator,
                "composite_key": fkey,
            }
        )

    if frozen_counts != working_counts:
        raise MigrationError("case row counts differ between frozen and working CSVs")
    assert_unique_composite_keys(frozen_keys)
    assert_unique_composite_keys(working_keys)
    if frozen_keys != working_keys:
        raise MigrationError("frozen and working rows do not have a one-to-one composite join")
    if sum(1 for row in frozen_rows if row["audit_record_id"] == "PROV-04") != 2:
        raise MigrationError("expected two PROV-04 candidate entries")
    return joined


def _build_tables(
    joined: Sequence[Mapping[str, object]], source_metadata: Mapping[str, str] | None = None
) -> dict[str, list[dict[str, str]]]:
    source_metadata = source_metadata or {}
    cases: dict[str, dict[str, str]] = {}
    candidates: list[dict[str, str]] = []
    statements: list[dict[str, str]] = []
    attribution: list[dict[str, str]] = []
    sources: list[dict[str, str]] = []
    mapping: list[dict[str, str]] = []
    legacy: list[dict[str, str]] = []

    for item in joined:
        frozen = item["frozen"]
        working = item["working"]
        row_index = int(item["input_row_index"])
        within_index = int(item["within_case_candidate_index"])
        audit_id = str(frozen["audit_record_id"])
        candidate_id = f"{audit_id}-C{within_index:02d}"
        statement_id = f"{candidate_id}-S00"
        locator = item["locator"]
        locator_key = f"{locator[0]}:{locator[1]}:{locator[2]}"
        entry_text = str(frozen["taqrib_entry_text_verbatim"])
        entry_hash = sha256_bytes(entry_text.encode("utf-8"))

        if audit_id not in cases:
            cases[audit_id] = {
                "audit_record_id": audit_id,
                "dataset_name": frozen["dataset_name"],
                "dataset_narrator_id": frozen["dataset_narrator_id"],
                "dataset_narrator_name": frozen["dataset_narrator_name"],
                "original_grade_field": frozen["original_grade_field"],
                "original_grade_verbatim": frozen["original_grade_verbatim"],
                "original_grade_source_location": frozen["original_source_location"],
                "original_value_status": "present" if frozen["original_grade_verbatim"] else "absent_in_source",
            }

        legacy_rank = str(working.get("taqrib_rank_number", ""))
        legacy_rank_candidate = ""
        if re.fullmatch(r"(?:[1-9]|1[0-2])", _digits(legacy_rank)):
            legacy_rank_candidate = _digits(legacy_rank)

        candidates.append(
            {
                "audit_record_id": audit_id,
                "candidate_entry_id": candidate_id,
                "within_case_candidate_index": str(within_index),
                "dataset_name": frozen["dataset_name"],
                "dataset_narrator_id": frozen["dataset_narrator_id"],
                "dataset_narrator_name": frozen["dataset_narrator_name"],
                "original_grade_field": frozen["original_grade_field"],
                "original_grade_verbatim": frozen["original_grade_verbatim"],
                "original_grade_source_location": frozen["original_source_location"],
                "taqrib_book_id": frozen["taqrib_book_id"],
                "taqrib_printed_page_from_corpus": frozen["taqrib_printed_page_from_corpus"],
                "taqrib_entry_text_verbatim": entry_text,
                "candidate_entry_text_status": "transcribed",
                "source_entry_number_from_text": str(item["entry_number"]),
                "source_locator_verbatim": working.get("source_locator", ""),
                "canonical_source_locator_key": locator_key,
                "candidate_field_source_correspondence": "not_assessed",
                "candidate_comparison_source_span": "",
                "candidate_comparison_source_span_status": "not_assessed",
                "candidate_comparison_rationale": "",
                "candidate_comparison_locator": "",
                "identity_match_status": "not_assessed",
                "identity_evidence_verbatim": "",
                "identity_evidence_text_status": "not_assessed",
                "identity_evidence_record_id": "",
                "identity_evidence_locator": "",
                "identity_evidence_independence_rationale": "",
                "taqrib_source_record_id": f"SRC-{candidate_id}",
                "legacy_rank_candidate": legacy_rank_candidate,
                "legacy_reviewer_notes_verbatim": str(working.get("reviewer_notes", "")),
            }
        )

        statements.append(
            {
                "audit_record_id": audit_id,
                "candidate_entry_id": candidate_id,
                "statement_id": statement_id,
                "statement_record_status": "provisional_work_item",
                "statement_type": "not_assessed",
                "statement_text_verbatim": "",
                "statement_text_status": "not_transcribed",
                "grade_base_verbatim": "",
                "grade_base_text_status": "not_assessed",
                "grade_qualification_verbatim": "",
                "grade_qualification_text_status": "not_assessed",
                "taqrib_rank_number": "",
                "rank_status": "not_assessed",
                "taqrib_statement_validity": "not_assessed",
                "target_task_scope": "not_assessed",
                "statement_source_correspondence": "not_assessed",
                "statement_source_span_verbatim": "",
                "statement_source_span_status": "not_assessed",
                "statement_source_correspondence_rationale": "",
                "statement_source_locator": "",
                "statement_source_evidence_record_id": "",
                "historical_input_eligibility": "not_assessed",
                "historical_input_eligibility_rationale": "",
                "target_task_scope_rationale": "",
                "corroboration_status": "not_examined",
                "temporal_policy_id": "",
                "temporal_policy_version": "",
                "temporal_policy_result": "cannot_assess",
            }
        )

        attribution.append(
            {
                "attribution_link_id": f"{statement_id}-A01",
                "statement_id": statement_id,
                "named_historical_evaluator": "",
                "evaluator_value_status": "not_assessed",
                "intermediary_transmitter": "",
                "transmitter_value_status": "not_assessed",
                "surviving_wording_author": "",
                "wording_author_value_status": "not_assessed",
                "attribution_form": "not_assessed",
                "passage_evaluator_naming_status": "not_assessed",
                "historical_evaluator_attribution_status": "not_assessed",
                "transmission_route_status": "not_assessed",
                "compiler_authorship_status": "not_assessed",
                "attribution_evidence_verbatim": "",
                "attribution_evidence_text_status": "not_assessed",
                "attribution_evidence_record_id": "",
                "attribution_evidence_locator": "",
                "transmission_route_evidence_record_id": "",
            }
        )

        source_id = f"SRC-{candidate_id}"
        sources.append(
            {
                "source_record_id": source_id,
                "candidate_entry_id": candidate_id,
                "source_work_id": frozen["taqrib_book_id"],
                "source_work_title": source_metadata.get("title", ""),
                "consulted_edition": source_metadata.get("edition", ""),
                "consulted_editor": source_metadata.get("editor", ""),
                "consulted_witness_id": "",
                "consulted_witness_type": "",
                "consulted_corpus_artifact_id": source_metadata.get("pages_jsonl_sha256", ""),
                "consulted_corpus_artifact_type": "pages_jsonl digital corpus artifact",
                "source_page_numbering_note": source_metadata.get("page_numbering_note", ""),
                "source_work_author_compiler": "",
                "source_author_metadata_status": "not_assessed",
                "source_locator_verbatim": working.get("source_locator", ""),
                "canonical_source_locator_key": locator_key,
                "source_verification_status": "not_assessed",
                "edition_variant_status": "not_assessed",
                "edition_metadata_evidence_record_id": "",
            }
        )

        for source_file in (FROZEN_NAME, WORKING_NAME):
            mapping.append(
                {
                    "source_file": source_file,
                    "input_row_index": str(row_index),
                    "audit_record_id": audit_id,
                    "within_case_candidate_index": str(within_index),
                    "taqrib_entry_text_sha256": entry_hash,
                    "source_locator_verbatim": working.get("source_locator", ""),
                    "canonical_source_locator_key": locator_key,
                    "candidate_entry_id": candidate_id,
                    "statement_id": statement_id,
                    "migration_join_status": "matched",
                }
            )

        for source_name, source_row in ((FROZEN_NAME, frozen), (WORKING_NAME, working)):
            for field_name in EXPECTED_HEADERS:
                legacy.append(
                    {
                        "source_file": source_name,
                        "input_row_index": str(row_index),
                        "audit_record_id": audit_id,
                        "candidate_entry_id": candidate_id,
                        "field_name": field_name,
                        "legacy_value": source_row.get(field_name, ""),
                        "is_empty_cell": "true" if source_row.get(field_name, "") == "" else "false",
                    }
                )

    empty_tables = {
        "source_evidence.csv": [],
        "date_claims.csv": [],
        "feature_sources.csv": [],
    }
    return {
        "cases.csv": list(cases.values()),
        "candidate_entries.csv": candidates,
        "statements.csv": statements,
        "attribution_links.csv": attribution,
        "sources.csv": sources,
        "source_evidence.csv": empty_tables["source_evidence.csv"],
        "date_claims.csv": empty_tables["date_claims.csv"],
        "feature_sources.csv": empty_tables["feature_sources.csv"],
        "migration_mapping.csv": mapping,
        "legacy_v1_values.csv": legacy,
        "column_mapping.csv": [],
    }


COLUMN_MAPPING_HEADERS = OUTPUT_TABLES["column_mapping.csv"]

LEGACY_DECISION_COLUMNS = {
    "taqrib_entry_name_verbatim",
    "taqrib_grade_verbatim",
    "taqrib_qualification_verbatim",
    "taqrib_rank_number",
    "taqrib_identity_match_status",
    "taqrib_text_match_status",
    "assessment_author",
    "assessment_attribution_status",
    "compiler_or_transmitter",
    "editorial_material_status",
    "attribution_evidence_verbatim",
    "source_verification_status",
    "textual_fidelity",
    "attribution_fidelity",
    "identity_fidelity",
    "record_disposition",
    "input_eligibility",
    "exclusion_or_quarantine_reason",
    "corroboration_status",
}


def _build_column_mapping(
    frozen_headers: Sequence[str],
    working_headers: Sequence[str],
    source_metadata: Mapping[str, str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(source_file: str, source_column: str, target_table: str, target_column: str, mapping_type: str, rule: str) -> None:
        rows.append(
            {
                "source_file": source_file,
                "source_column": source_column,
                "target_table": target_table,
                "target_column": target_column,
                "mapping_type": mapping_type,
                "transformation_rule": rule,
                "review_required": "true" if mapping_type in {"legacy_only", "deferred_for_review"} else "false",
            }
        )

    frozen_targets: dict[str, tuple[tuple[str, str], ...]] = {
        "audit_record_id": (("cases.csv", "audit_record_id"), ("candidate_entries.csv", "audit_record_id")),
        "dataset_name": (("cases.csv", "dataset_name"), ("candidate_entries.csv", "dataset_name")),
        "dataset_narrator_id": (("cases.csv", "dataset_narrator_id"), ("candidate_entries.csv", "dataset_narrator_id")),
        "dataset_narrator_name": (("cases.csv", "dataset_narrator_name"), ("candidate_entries.csv", "dataset_narrator_name")),
        "original_grade_field": (("cases.csv", "original_grade_field"), ("candidate_entries.csv", "original_grade_field")),
        "original_grade_verbatim": (("cases.csv", "original_grade_verbatim"), ("candidate_entries.csv", "original_grade_verbatim")),
        "original_source_location": (("cases.csv", "original_grade_source_location"), ("candidate_entries.csv", "original_grade_source_location")),
        "taqrib_book_id": (("candidate_entries.csv", "taqrib_book_id"), ("sources.csv", "source_work_id")),
        "taqrib_printed_page_from_corpus": (("candidate_entries.csv", "taqrib_printed_page_from_corpus"),),
        "taqrib_entry_text_verbatim": (("candidate_entries.csv", "taqrib_entry_text_verbatim"),),
    }
    working_targets: dict[str, tuple[tuple[str, str, str], ...]] = {
        "source_locator": (
            ("candidate_entries.csv", "source_locator_verbatim", "Exact locator retained; canonical tuple is separately parsed and validated."),
            ("sources.csv", "source_locator_verbatim", "Exact locator retained; canonical tuple is separately parsed and validated."),
            ("candidate_entries.csv", "canonical_source_locator_key", "Parse book/page/entry tuple after matching it against the frozen entry text."),
            ("sources.csv", "canonical_source_locator_key", "Parse book/page/entry tuple after matching it against the frozen entry text."),
        ),
        "taqrib_rank_number": (
            ("candidate_entries.csv", "legacy_rank_candidate", "Strict decimal 1..12 convenience value only; never assigned to the v2.2 rank."),
        ),
        "reviewer_notes": (
            ("candidate_entries.csv", "legacy_reviewer_notes_verbatim", "Copied verbatim as a legacy note; not promoted to a new reviewer decision."),
        ),
    }

    for filename, headers in ((FROZEN_NAME, frozen_headers), (WORKING_NAME, working_headers)):
        targets = frozen_targets if filename == FROZEN_NAME else {}
        for column in headers:
            mapped = False
            if column in targets:
                for table, target_column in targets[column]:
                    add(filename, column, table, target_column, "copied", "Exact logical cell copied without normalization.")
                    mapped = True
                if column == "taqrib_entry_text_verbatim":
                    add(filename, column, "candidate_entries.csv", "source_entry_number_from_text", "mechanically_transformed", "Parse leading entry number for locator validation only; retain full source text verbatim.")
                    mapped = True
            elif column in working_targets:
                for table, target_column, rule in working_targets[column]:
                    add(filename, column, table, target_column, "mechanically_transformed", rule)
                    mapped = True
            mapping_type = "deferred_for_review" if column in LEGACY_DECISION_COLUMNS else "legacy_only"
            add(
                filename,
                column,
                "legacy_v1_values.csv",
                "legacy_value",
                mapping_type,
                "Exact value retained in the immutable legacy snapshot; no v2.2 decision is inferred."
                if not mapped
                else "Exact legacy value retained alongside the explicitly documented v2.2 mapping.",
            )

    provenance_targets = {
        "book_id": ("sources.csv", "source_work_id"),
        "title": ("sources.csv", "source_work_title"),
        "editor": ("sources.csv", "consulted_editor"),
        "edition": ("sources.csv", "consulted_edition"),
        "page_numbering_note": ("sources.csv", "source_page_numbering_note"),
        "pages_jsonl_sha256": ("sources.csv", "consulted_corpus_artifact_id"),
    }
    for key, (table, column) in provenance_targets.items():
        if key in source_metadata:
            add(MANIFEST_NAME, f"source_corpus.{key}", table, column, "copied", "Exact source-corpus metadata copied from the pinned provenance manifest; no scholarly decision inferred.")
    add(MANIFEST_NAME, "source_corpus.pages_jsonl_sha256", "sources.csv", "consulted_corpus_artifact_type", "mechanically_transformed", "Fixed label describes the hashed JSONL corpus artifact; it is not treated as a manuscript witness.")
    return rows


def write_csv_file(path: Path, rows: Iterable[Mapping[str, str]], columns: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _assert_link(rows: Mapping[str, Mapping[str, str]], identifier: str, table: str, field: str) -> Mapping[str, str]:
    if not identifier or identifier not in rows:
        raise MigrationError(f"{table}.{field} references missing record {identifier!r}")
    return rows[identifier]


def _status_text_valid(row: Mapping[str, str], text_field: str, status_field: str, table: str) -> None:
    status = row.get(status_field, "")
    value = row.get(text_field, "")
    if status == "transcribed" and not str(value or "").strip():
        raise MigrationError(f"{table}.{text_field} is empty although {status_field}=transcribed")
    if status != "transcribed" and value not in {"", None}:
        raise MigrationError(f"{table}.{text_field} must be null unless {status_field}=transcribed")


def _check_ref_value_status(
    row: Mapping[str, str], value_field: str, status_field: str, positive_status: str, table: str
) -> None:
    value = str(row.get(value_field, "") or "").strip()
    status = row.get(status_field, "")
    if status == positive_status and not value:
        raise MigrationError(f"{table}.{value_field} is required when {status_field}={positive_status}")
    if status in {"none_named", "none_identified", "unknown", "not_assessed", "not_applicable"} and value:
        raise MigrationError(f"{table}.{value_field} must be empty when {status_field}={status}")


def validate_feature_source_record(
    row: Mapping[str, str],
    *,
    statements: Mapping[str, Mapping[str, str]],
    candidates: Mapping[str, Mapping[str, str]],
    sources: Mapping[str, Mapping[str, str]],
    date_claims: Mapping[str, Mapping[str, str]],
    evidence: Mapping[str, Mapping[str, str]],
) -> None:
    """Enforce the Task A feature firewall for one proposed feature source."""
    statement = _assert_link(statements, row["statement_id"], "feature_sources.csv", "statement_id")
    feature_source = _assert_link(sources, row["source_record_id"], "feature_sources.csv", "source_record_id")
    candidate = candidates[statement["candidate_entry_id"]]
    status = row["feature_inclusion_status"]
    if not row["feature_exclusion_policy_id"].strip() or not row["feature_exclusion_policy_version"].strip() or not row["decision_rationale"].strip():
        raise MigrationError("every proposed feature source requires policy ID/version and a decision rationale")
    date_claim = _assert_link(date_claims, row["temporal_date_claim_id"], "feature_sources.csv", "temporal_date_claim_id")
    if statement["statement_record_status"] != "reviewed_statement" and status == "included":
        raise MigrationError("provisional or superseded placeholders cannot be included as feature sources")
    if status != "included":
        return
    if not row["feature_input_name"].strip():
        raise MigrationError("included feature source requires a feature input name")
    normalized_name = re.sub(r"[^a-z0-9]+", "_", row["feature_input_name"].lower()).strip("_")
    leak_terms = ("grade", "taqrib", "rank", "target", "label", "assessment", "evaluation", "score", "classif")
    if any(term in normalized_name for term in leak_terms) or row["feature_input_name"] == candidate["original_grade_field"]:
        raise MigrationError("direct or named target-derived feature is prohibited by Task A")
    target_source = _assert_link(sources, candidate["taqrib_source_record_id"], "feature_sources.csv", "candidate Taqrib source")
    if feature_source["source_record_id"] == candidate["taqrib_source_record_id"] or feature_source["source_work_id"] == target_source["source_work_id"]:
        raise MigrationError("Taqrib target source cannot be included as an independent Task A feature")
    if feature_source["candidate_entry_id"] != candidate["candidate_entry_id"]:
        raise MigrationError("feature source must be linked to the same candidate as its statement")
    if statement["target_task_scope"] != "ordinary_grade_candidate":
        raise MigrationError("Task A feature cannot be included for a statement outside the ordinary-grade task")
    if date_claim["date_claim_status"] != "recorded_in_source":
        raise MigrationError("included feature source requires a recorded temporal date claim")
    date_evidence = _assert_link(evidence, date_claim["evidence_record_id"], "feature_sources.csv", "date evidence_record_id")
    if date_evidence["source_record_id"] != feature_source["source_record_id"]:
        raise MigrationError("feature date claim must be evidenced by the included source")


def validate_historical_input_decision(
    statement: Mapping[str, str],
    *,
    date_claims: Mapping[str, Mapping[str, str]],
    evidence: Mapping[str, Mapping[str, str]],
    sources: Mapping[str, Mapping[str, str]],
) -> None:
    """Fail closed when a historical-input decision lacks linked temporal evidence."""
    eligibility = statement["historical_input_eligibility"]
    policy_id, policy_version = statement["temporal_policy_id"], statement["temporal_policy_version"]
    result = statement["temporal_policy_result"]
    if eligibility == "not_assessed":
        if result != "cannot_assess" or policy_id or policy_version:
            raise MigrationError("not-assessed historical input must not carry an applied temporal policy")
        return
    if eligibility == "not_applicable":
        if result != "not_applicable" or policy_id or policy_version:
            raise MigrationError("not-applicable historical input must not carry an applied temporal policy")
        return
    if not policy_id.strip() or not policy_version.strip() or not statement["historical_input_eligibility_rationale"].strip():
        raise MigrationError("assessed historical-input decision requires policy ID/version and a rationale")
    expected_result = {
        "eligible": "passes_policy",
        "ineligible": "fails_policy",
        "quarantined_pending_verification": "cannot_assess",
    }[eligibility]
    if result != expected_result:
        raise MigrationError(f"historical-input status {eligibility} conflicts with its temporal-policy result")

    linked_claims: list[Mapping[str, str]] = []
    for claim in date_claims.values():
        evidence_id = claim["evidence_record_id"]
        if not evidence_id:
            continue
        evidence_row = _assert_link(evidence, evidence_id, "date_claims.csv", "evidence_record_id")
        if evidence_row["statement_id"] == statement["statement_id"]:
            linked_claims.append(claim)
    if not linked_claims:
        raise MigrationError("assessed historical-input decision requires date claims linked to its statement")
    if eligibility in {"eligible", "ineligible"}:
        kinds = {claim["date_kind"] for claim in linked_claims if claim["date_claim_status"] == "recorded_in_source"}
        if not {"evaluator_lifespan_or_death", "approximate_judgment_date"}.issubset(kinds):
            raise MigrationError(
                "temporal eligibility cannot rest on evaluator death alone; link recorded evaluator and judgment-date claims"
            )
        for claim in linked_claims:
            if claim["date_claim_status"] != "recorded_in_source":
                continue
            evidence_row = evidence[claim["evidence_record_id"]]
            source = _assert_link(sources, evidence_row["source_record_id"], "date_claims.csv", "source_record_id")
            if evidence_row["evidence_role"] != "temporal_date" or evidence_row["evidence_text_status"] != "transcribed":
                raise MigrationError("temporal eligibility requires transcribed temporal-date evidence")
            if source["source_verification_status"] not in {"verified_in_corpus", "verified_external_edition"}:
                raise MigrationError("temporal eligibility requires verified date sources")


def _manifest_status_counts(tables: Mapping[str, list[dict[str, str]]]) -> dict[str, dict[str, dict[str, int]]]:
    counts: dict[str, dict[str, dict[str, int]]] = {}
    for table_name, rows in tables.items():
        fields = [name for name in OUTPUT_TABLES[table_name] if name in FIELD_ENUMS or name in FIELD_ENUM_ALIASES]
        if fields:
            counts[table_name] = {
                field: dict(sorted(Counter(row.get(field, "") for row in rows).items())) for field in fields
            }
    return counts


def _manifest_missingness_counts(tables: Mapping[str, list[dict[str, str]]]) -> dict[str, dict[str, dict[str, int]]]:
    return {
        table_name: {
            field: {
                "empty_or_null": sum(row.get(field) in {"", None} for row in rows),
                "nonempty": sum(row.get(field) not in {"", None} for row in rows),
            }
            for field in OUTPUT_TABLES[table_name]
        }
        for table_name, rows in tables.items()
    }


def validate_package_tables(tables: Mapping[str, list[dict[str, str]]]) -> None:
    """Validate schemas, relationships, statuses, and analytical-safety invariants."""
    if set(tables) != set(OUTPUT_TABLES):
        raise MigrationError("table set does not match the frozen v2.2 package schema")

    indexed: dict[str, dict[str, Mapping[str, str]]] = {}
    for table_name, columns in OUTPUT_TABLES.items():
        rows = tables[table_name]
        primary = PRIMARY_KEYS.get(table_name)
        seen_primary: set[tuple[str, ...]] = set()
        for row_index, row in enumerate(rows, start=1):
            if set(row) != set(columns):
                raise MigrationError(f"{table_name} row {row_index} fields do not match its declared schema")
            for field in REQUIRED_NONEMPTY[table_name]:
                if row.get(field) is None or not str(row.get(field, "")).strip():
                    raise MigrationError(f"{table_name}.{field} is required at row {row_index}")
            for field in columns:
                enum_name = field if field in FIELD_ENUMS else FIELD_ENUM_ALIASES.get(field)
                if enum_name:
                    value = row.get(field, "")
                    if value not in FIELD_ENUMS[enum_name]:
                        raise MigrationError(f"{table_name}.{field} has invalid enum value {value!r} at row {row_index}")
            if "is_empty_cell" in row and row["is_empty_cell"] not in {"true", "false"}:
                raise MigrationError(f"{table_name}.is_empty_cell must be true or false")
            if "review_required" in row and row["review_required"] not in {"true", "false"}:
                raise MigrationError(f"{table_name}.review_required must be true or false")
            if primary:
                key = tuple(str(row.get(field, "")) for field in primary)
                if any(not value for value in key) or key in seen_primary:
                    raise MigrationError(f"{table_name} has a missing or duplicate primary key at row {row_index}: {key!r}")
                seen_primary.add(key)
        indexed[table_name] = {
            str(row[primary[0]]): row for row in rows
        } if primary and len(primary) == 1 else {}

    # Field placement is deliberate: identity is candidate-level; statement semantics are statement-level.
    if "identity_match_status" in OUTPUT_TABLES["statements.csv"] or "taqrib_statement_validity" in OUTPUT_TABLES["candidate_entries.csv"]:
        raise MigrationError("candidate-level and statement-level fields are mixed")
    if "source_work_author_compiler" in OUTPUT_TABLES["attribution_links.csv"] or "surviving_wording_author" in OUTPUT_TABLES["sources.csv"]:
        raise MigrationError("source-work and surviving-wording author roles are conflated")

    cases = indexed["cases.csv"]
    candidates = indexed["candidate_entries.csv"]
    statements = indexed["statements.csv"]
    attributions = indexed["attribution_links.csv"]
    sources = indexed["sources.csv"]
    evidence = indexed["source_evidence.csv"]
    date_claims = indexed["date_claims.csv"]
    feature_sources = indexed["feature_sources.csv"]
    if len(cases) != 10 or len(candidates) != 11:
        raise MigrationError("frozen pilot must remain 10 cases and 11 candidate entries")
    if len(tables["migration_mapping.csv"]) != 22 or len(tables["legacy_v1_values.csv"]) != 748:
        raise MigrationError("frozen pilot row mapping or legacy snapshot count is incomplete")

    candidate_counts: Counter[str] = Counter()
    for row in tables["candidate_entries.csv"]:
        case_id = row["audit_record_id"]
        _assert_link(cases, case_id, "candidate_entries.csv", "audit_record_id")
        try:
            within_index = int(row["within_case_candidate_index"])
        except ValueError as exc:
            raise MigrationError("candidate within-case index must be an integer") from exc
        if within_index <= 0 or row["candidate_entry_id"] != f"{case_id}-C{within_index:02d}":
            raise MigrationError("candidate identifier does not match its validated within-case index")
        candidate_counts[case_id] += 1
    if set(candidate_counts) != set(cases):
        raise MigrationError("cases.csv contains a case with no candidate entry")
    if candidate_counts != Counter({case_id: (2 if case_id == "PROV-04" else 1) for case_id in cases}):
        raise MigrationError("candidate-per-case pattern differs from the frozen pilot, including PROV-04")
    for case_id, count in candidate_counts.items():
        observed_indices = sorted(
            int(row["within_case_candidate_index"])
            for row in tables["candidate_entries.csv"]
            if row["audit_record_id"] == case_id
        )
        if observed_indices != list(range(1, count + 1)):
            raise MigrationError("candidate within-case indices must be contiguous and start at 1")

    candidates_by_id = candidates
    statements_by_candidate: Counter[str] = Counter()
    for row in tables["statements.csv"]:
        candidate = _assert_link(candidates_by_id, row["candidate_entry_id"], "statements.csv", "candidate_entry_id")
        if row["audit_record_id"] != candidate["audit_record_id"]:
            raise MigrationError("statements.csv audit_record_id does not match its candidate entry")
        if row["statement_record_status"] in {"provisional_work_item", "superseded_placeholder"} and row["statement_id"] != f"{row['candidate_entry_id']}-S00":
            raise MigrationError("provisional placeholder identifier must be stable and candidate-linked")
        statements_by_candidate[row["candidate_entry_id"]] += 1
    if set(statements_by_candidate) != set(candidates):
        raise MigrationError("candidate_entries.csv contains a candidate with no statement work item")
    attribution_statement_ids = {row["statement_id"] for row in tables["attribution_links.csv"]}
    if set(statements) - attribution_statement_ids:
        raise MigrationError(
            "statements.csv contains a statement without a matching attribution_links.csv statement_id relationship"
        )

    for table_name, pairs in TEXT_STATUS_PAIRS.items():
        for row in tables[table_name]:
            for text_field, status_field in pairs:
                _status_text_valid(row, text_field, status_field, table_name)

    for row in tables["cases.csv"]:
        status, original = row["original_value_status"], row["original_grade_verbatim"]
        if (status == "present") != bool(original):
            raise MigrationError("cases.csv original_value_status conflicts with original_grade_verbatim")

    for row in tables["statements.csv"]:
        rank_status, rank_value = row["rank_status"], row["taqrib_rank_number"]
        if rank_status == "assigned":
            if not re.fullmatch(r"(?:[1-9]|1[0-2])", str(rank_value or "")):
                raise MigrationError("statements.csv assigned rank must be an integer from 1 through 12")
        elif rank_value:
            raise MigrationError("statements.csv rank must be null unless rank_status=assigned")
        if row["statement_source_correspondence"] in {"exact", "minor_variation"}:
            if row["statement_source_span_status"] != "transcribed":
                raise MigrationError("assessed statement correspondence requires a transcribed source span")
            if not row["statement_source_correspondence_rationale"].strip() or not row["statement_source_locator"].strip():
                raise MigrationError("assessed statement correspondence requires rationale and locator")
            if not row["statement_source_evidence_record_id"]:
                raise MigrationError("assessed statement correspondence requires linked source evidence")
        if row["statement_source_span_status"] == "transcribed" and not row["statement_source_evidence_record_id"]:
            raise MigrationError("transcribed statement source span requires a linked evidence record")
        if row["statement_source_correspondence"] != "not_assessed":
            if not row["statement_source_correspondence_rationale"].strip() or not row["statement_source_locator"].strip():
                raise MigrationError("reviewed statement correspondence requires rationale and source locator")
        if row["taqrib_statement_validity"] == "supported_taqrib_statement":
            if row["statement_text_status"] != "transcribed" or row["statement_source_correspondence"] not in {"exact", "minor_variation"}:
                raise MigrationError("supported Taqrib statement requires transcribed text and assessed source correspondence")
            if not row["statement_source_evidence_record_id"]:
                raise MigrationError("supported Taqrib statement requires linked passage evidence")
        record_status = row["statement_record_status"]
        if record_status in {"provisional_work_item", "superseded_placeholder"}:
            if not row["statement_id"].endswith("-S00"):
                raise MigrationError("placeholder record must retain an S00 statement identifier")
            if row["statement_type"] != "not_assessed" or row["statement_text_status"] != "not_transcribed" or row["statement_text_verbatim"]:
                raise MigrationError("S00 placeholder must remain textless and unclassified")
            if row["taqrib_rank_number"] or row["rank_status"] != "not_assessed":
                raise MigrationError("S00 placeholder cannot carry rank")
            if row["target_task_scope"] != "not_assessed" or row["historical_input_eligibility"] != "not_assessed":
                raise MigrationError("S00 placeholder cannot carry an analytical eligibility decision")
        elif row["statement_id"].endswith("-S00"):
            raise MigrationError("S00 placeholder cannot be promoted; create a separate reviewed statement record")

    # Candidate, source, and evidence relationships.
    for row in tables["sources.csv"]:
        _assert_link(candidates, row["candidate_entry_id"], "sources.csv", "candidate_entry_id")
        if row["source_author_metadata_status"] == "recorded" and not row["source_work_author_compiler"].strip():
            raise MigrationError("sources.csv recorded source author/compiler requires a value")
        if row["source_author_metadata_status"] != "recorded" and row["source_work_author_compiler"]:
            raise MigrationError("sources.csv source-work author/compiler value conflicts with its status")
        if row["source_verification_status"] in {"verified_in_corpus", "verified_external_edition"}:
            if not row["source_locator_verbatim"].strip() or not row["source_work_title"].strip() or not row["consulted_edition"].strip():
                raise MigrationError("verified source requires title, consulted edition, and locator")
        needs_edition_evidence = row["edition_variant_status"] in {
            "variant_marked_in_edition_metadata", "editorial_insertion_verified", "editorial_note_or_footnote"
        }
        evidence_id = row["edition_metadata_evidence_record_id"]
        if needs_edition_evidence and not evidence_id:
            raise MigrationError("assessed edition or editorial status requires linked edition metadata evidence")
        if evidence_id:
            ev = _assert_link(evidence, evidence_id, "sources.csv", "edition_metadata_evidence_record_id")
            if ev["evidence_role"] != "edition_metadata" or ev["source_record_id"] != row["source_record_id"]:
                raise MigrationError("edition metadata evidence must be linked to its source record")
    for candidate_id, candidate in candidates.items():
        target_source = _assert_link(sources, candidate["taqrib_source_record_id"], "candidate_entries.csv", "taqrib_source_record_id")
        if target_source["candidate_entry_id"] != candidate_id or target_source["source_work_id"] != candidate["taqrib_book_id"]:
            raise MigrationError("candidate Taqrib source link does not match its source record")
        entry_number = entry_number_from_text(candidate["taqrib_entry_text_verbatim"])
        if candidate["source_entry_number_from_text"] != str(entry_number):
            raise MigrationError("candidate source entry number does not match the preserved full entry text")
        page, locator_entry = parse_working_locator(candidate["source_locator_verbatim"])
        expected_locator = canonical_locator_key(candidate["taqrib_book_id"], candidate["taqrib_printed_page_from_corpus"], entry_number)
        try:
            source_locator = tuple(int(part) for part in candidate["canonical_source_locator_key"].split(":"))
        except (TypeError, ValueError) as exc:
            raise MigrationError("candidate canonical locator key is malformed") from exc
        if (page, locator_entry) != expected_locator[1:] or source_locator != expected_locator:
            raise MigrationError("candidate canonical locator does not match its source text and page")
        if (
            target_source["source_locator_verbatim"] != candidate["source_locator_verbatim"]
            or target_source["canonical_source_locator_key"] != candidate["canonical_source_locator_key"]
        ):
            raise MigrationError("candidate and source locator values disagree")

    for row in tables["source_evidence.csv"]:
        _assert_link(sources, row["source_record_id"], "source_evidence.csv", "source_record_id")
        if row["candidate_entry_id"]:
            _assert_link(candidates, row["candidate_entry_id"], "source_evidence.csv", "candidate_entry_id")
        if row["statement_id"]:
            _assert_link(statements, row["statement_id"], "source_evidence.csv", "statement_id")
        if row["attribution_link_id"]:
            _assert_link(attributions, row["attribution_link_id"], "source_evidence.csv", "attribution_link_id")
        scopes = sum(bool(row[field]) for field in ("candidate_entry_id", "statement_id", "attribution_link_id"))
        if scopes > 1:
            raise MigrationError("source_evidence.csv evidence row may have only one direct annotation owner")
        role_owner = {
            "identity": "candidate_entry_id",
            "passage_text": "statement_id" if row["statement_id"] else "attribution_link_id",
            "historical_attribution": "attribution_link_id",
            "transmission_route": "attribution_link_id",
            "edition_metadata": "candidate_entry_id",
        }.get(row["evidence_role"])
        if role_owner and not row[role_owner]:
            raise MigrationError(f"source_evidence.csv role {row['evidence_role']} requires {role_owner}")
        if row["evidence_role"] == "passage_text" and not (row["statement_id"] or row["attribution_link_id"]):
            raise MigrationError("passage-text evidence must link to a statement or attribution record")

    for candidate_id, candidate in candidates.items():
        identity_id = candidate["identity_evidence_record_id"]
        if candidate["identity_evidence_text_status"] == "transcribed" and not identity_id:
            raise MigrationError("transcribed identity evidence requires an evidence-record link")
        if identity_id:
            ev = _assert_link(evidence, identity_id, "candidate_entries.csv", "identity_evidence_record_id")
            if ev["evidence_role"] != "identity" or ev["candidate_entry_id"] != candidate_id:
                raise MigrationError("candidate identity evidence must link to identity evidence owned by that candidate")
            if ev["evidence_text_verbatim"] != candidate["identity_evidence_verbatim"] or ev["source_locator"] != candidate["identity_evidence_locator"]:
                raise MigrationError("candidate identity evidence fields differ from their linked evidence record")
        if candidate["identity_match_status"] == "confirmed":
            if not identity_id or not candidate["identity_evidence_independence_rationale"].strip():
                raise MigrationError("confirmed identity requires linked evidence and an independence rationale")
            ev = evidence[identity_id]
            ev_source = sources[ev["source_record_id"]]
            target = sources[candidate["taqrib_source_record_id"]]
            if ev_source["source_verification_status"] not in {"verified_in_corpus", "verified_external_edition"}:
                raise MigrationError("confirmed identity evidence must come from a verified source")
            if ev_source["source_work_id"] == target["source_work_id"]:
                raise MigrationError("confirmed identity evidence must be from a distinct source work")

    for row in tables["statements.csv"]:
        evidence_id = row["statement_source_evidence_record_id"]
        if evidence_id:
            ev = _assert_link(evidence, evidence_id, "statements.csv", "statement_source_evidence_record_id")
            if ev["evidence_role"] != "passage_text" or ev["statement_id"] != row["statement_id"]:
                raise MigrationError("statement source evidence must be passage text owned by that statement")
            if ev["evidence_text_verbatim"] != row["statement_source_span_verbatim"] or ev["source_locator"] != row["statement_source_locator"]:
                raise MigrationError("statement source span differs from its linked evidence")
            candidate = candidates[row["candidate_entry_id"]]
            if ev["source_record_id"] != candidate["taqrib_source_record_id"]:
                raise MigrationError("statement source evidence must refer to its candidate's Taqrib source")
            if row["taqrib_statement_validity"] == "supported_taqrib_statement":
                source = sources[candidate["taqrib_source_record_id"]]
                if source["source_verification_status"] not in {"verified_in_corpus", "verified_external_edition"}:
                    raise MigrationError("supported Taqrib statement requires a verified consulted source")

    for row in tables["attribution_links.csv"]:
        _assert_link(statements, row["statement_id"], "attribution_links.csv", "statement_id")
        _check_ref_value_status(row, "named_historical_evaluator", "evaluator_value_status", "identified", "attribution_links.csv")
        _check_ref_value_status(row, "intermediary_transmitter", "transmitter_value_status", "identified", "attribution_links.csv")
        _check_ref_value_status(row, "surviving_wording_author", "wording_author_value_status", "identified", "attribution_links.csv")
        naming_to_value = {
            "explicit_individual_named": ("identified", "named_historical_evaluator"),
            "collective_only": ("collective_unidentified", None),
            "no_evaluator_named": ("none_named", None),
        }
        expected = naming_to_value.get(row["passage_evaluator_naming_status"])
        if expected and row["evaluator_value_status"] != expected[0]:
            raise MigrationError("attribution passage naming conflicts with evaluator value status")
        if row["attribution_form"] == "compiler_synthesis" and row["passage_evaluator_naming_status"] in {"explicit_individual_named", "collective_only"}:
            raise MigrationError("compiler synthesis conflicts with a passage naming an earlier evaluator")
        if row["attribution_form"] == "collective_attribution" and row["passage_evaluator_naming_status"] not in {"collective_only", "not_assessed"}:
            raise MigrationError("collective attribution conflicts with the passage naming status")
        if row["passage_evaluator_naming_status"] in {"explicit_individual_named", "collective_only", "no_evaluator_named"} and not row["attribution_evidence_record_id"]:
            raise MigrationError("reviewed passage evaluator naming requires linked passage evidence")
        if row["historical_evaluator_attribution_status"] in {
            "supported_by_verified_source_or_route",
            "explicitly_reported_but_historically_unverified",
            "contradicted",
        }:
            ev_id = row["attribution_evidence_record_id"]
            route_id = row["transmission_route_evidence_record_id"]
            if not ev_id and not route_id:
                raise MigrationError("assessed historical attribution requires linked evidence")
            if ev_id:
                attribution_ev = _assert_link(evidence, ev_id, "attribution_links.csv", "attribution_evidence_record_id")
            else:
                attribution_ev = None
            if row["historical_evaluator_attribution_status"] == "supported_by_verified_source_or_route" and attribution_ev and attribution_ev["evidence_role"] != "historical_attribution" and not route_id:
                raise MigrationError("historical attribution support must cite historical-attribution or route evidence")
        evidence_id = row["attribution_evidence_record_id"]
        if evidence_id:
            ev = _assert_link(evidence, evidence_id, "attribution_links.csv", "attribution_evidence_record_id")
            if ev["attribution_link_id"] != row["attribution_link_id"] or ev["evidence_role"] not in {"passage_text", "historical_attribution"}:
                raise MigrationError("attribution evidence must be linked to this attribution record")
            if ev["evidence_text_verbatim"] != row["attribution_evidence_verbatim"] or ev["source_locator"] != row["attribution_evidence_locator"]:
                raise MigrationError("attribution evidence fields differ from the linked evidence record")
            statement = statements[row["statement_id"]]
            candidate = candidates[statement["candidate_entry_id"]]
            if ev["evidence_role"] == "passage_text" and ev["source_record_id"] != candidate["taqrib_source_record_id"]:
                raise MigrationError("attribution passage evidence must refer to its candidate's Taqrib source")
        if row["attribution_evidence_text_status"] == "transcribed" and not evidence_id:
            raise MigrationError("transcribed attribution evidence requires an evidence-record link")
        route_id = row["transmission_route_evidence_record_id"]
        if row["transmission_route_status"] in {"documented_traceable", "route_examined_not_found"}:
            ev = _assert_link(evidence, route_id, "attribution_links.csv", "transmission_route_evidence_record_id")
            if ev["evidence_role"] != "transmission_route" or ev["attribution_link_id"] != row["attribution_link_id"]:
                raise MigrationError("assessed transmission route requires linked route evidence")
        elif route_id:
            raise MigrationError("route evidence cannot be linked unless the route was examined or documented")

    # Date claims and historical-input policy decisions must remain evidence-linked and explicit.
    for row in tables["date_claims.csv"]:
        status = row["date_claim_status"]
        evidence_id = row["evidence_record_id"]
        if status == "recorded_in_source":
            if not row["date_value"].strip() or not row["date_calendar"].strip() or not row["date_precision"].strip():
                raise MigrationError("recorded date claim requires value, calendar, and precision")
            ev = _assert_link(evidence, evidence_id, "date_claims.csv", "evidence_record_id")
            if ev["evidence_role"] != "temporal_date" or ev["evidence_text_status"] != "transcribed":
                raise MigrationError("recorded date claim requires its own transcribed temporal evidence")
            if ev["source_locator"] == "":
                raise MigrationError("recorded date claim evidence requires a source locator")
            source = _assert_link(sources, ev["source_record_id"], "date_claims.csv", "source_record_id")
            if source["source_verification_status"] not in {"verified_in_corpus", "verified_external_edition"}:
                raise MigrationError("recorded date claim requires a verified source")
        elif status == "not_applicable":
            if row["date_value"] or row["date_calendar"] or row["date_precision"] or evidence_id:
                raise MigrationError("not-applicable date claims cannot carry date values or evidence")
        else:
            if row["date_value"] or row["date_calendar"] or row["date_precision"]:
                raise MigrationError("non-asserted date claim cannot carry a date value, calendar, or precision")
            ev = _assert_link(evidence, evidence_id, "date_claims.csv", "evidence_record_id")
            expected_evidence_status = {
                "unknown": {"not_found_after_review"},
                "unresolved": {"unresolved", "transcribed"},
                "not_assessed": {"not_assessed"},
            }[status]
            if ev["evidence_role"] != "temporal_date" or ev["evidence_text_status"] not in expected_evidence_status:
                raise MigrationError("non-asserted date claim requires matching linked temporal evidence status")
            if status == "unknown" and not ev["source_locator"].strip():
                raise MigrationError("unknown date claim must record the inspected source scope/locator")

    for row in tables["statements.csv"]:
        validate_historical_input_decision(row, date_claims=date_claims, evidence=evidence, sources=sources)

    for row in tables["statements.csv"]:
        if row["target_task_scope"] != "not_assessed" and not row["target_task_scope_rationale"].strip():
            raise MigrationError("an assessed target-task scope requires a rationale")

    # Feature review is fail-closed for direct target leakage and all provisional statements.
    for row in tables["feature_sources.csv"]:
        validate_feature_source_record(
            row,
            statements=statements,
            candidates=candidates,
            sources=sources,
            date_claims=date_claims,
            evidence=evidence,
        )

    # Every ordinary target must satisfy the evidence-bearing guard, not just status labels.
    evidence_by_id = evidence
    for statement in tables["statements.csv"]:
        if statement["target_task_scope"] == "ordinary_grade_candidate":
            candidate = candidates[statement["candidate_entry_id"]]
            attribution_rows = [row for row in tables["attribution_links.csv"] if row["statement_id"] == statement["statement_id"]]
            if len(attribution_rows) != 1:
                raise MigrationError("ordinary-grade target requires exactly one reviewed attribution link")
            source = sources[candidate["taqrib_source_record_id"]]
            sources_by_id = sources
            if not ordinary_grade_candidate_conditions_pass(
                candidate,
                statement,
                attribution_rows[0],
                source,
                evidence_by_id=evidence_by_id,
                sources_by_id=sources_by_id,
            ):
                raise MigrationError("ordinary-grade target does not satisfy the complete evidence-based invariant")

    # The row map and column map are provenance records, not annotation sources.
    for row in tables["migration_mapping.csv"]:
        candidate = _assert_link(candidates, row["candidate_entry_id"], "migration_mapping.csv", "candidate_entry_id")
        statement = _assert_link(statements, row["statement_id"], "migration_mapping.csv", "statement_id")
        if candidate["audit_record_id"] != row["audit_record_id"] or statement["candidate_entry_id"] != row["candidate_entry_id"]:
            raise MigrationError("migration_mapping.csv row-to-record links are inconsistent")
        if row["migration_join_status"] != "matched":
            raise MigrationError("published row mappings must all be matched")
        try:
            candidate_index = int(row["within_case_candidate_index"])
            source_row_index = int(row["input_row_index"])
        except ValueError as exc:
            raise MigrationError("migration mapping indices must be integers") from exc
        candidate = candidates[row["candidate_entry_id"]]
        if candidate["within_case_candidate_index"] != str(candidate_index):
            raise MigrationError("migration mapping candidate index disagrees with candidate table")
        if candidate["canonical_source_locator_key"] != row["canonical_source_locator_key"]:
            raise MigrationError("migration mapping locator disagrees with candidate table")
        expected_text_hash = sha256_bytes(candidate["taqrib_entry_text_verbatim"].encode("utf-8"))
        if row["taqrib_entry_text_sha256"] != expected_text_hash or not 1 <= source_row_index <= 11:
            raise MigrationError("migration mapping text hash or source row index is invalid")
    mapping_counts = Counter(row["source_file"] for row in tables["migration_mapping.csv"])
    if mapping_counts != Counter({FROZEN_NAME: 11, WORKING_NAME: 11}):
        raise MigrationError("migration row map must cover every row from both content inputs")
    for source_file in (FROZEN_NAME, WORKING_NAME):
        indices = {int(row["input_row_index"]) for row in tables["migration_mapping.csv"] if row["source_file"] == source_file}
        if indices != set(range(1, 12)):
            raise MigrationError(f"migration row map does not cover all rows in {source_file}")
        try:
            candidate_index = int(row["within_case_candidate_index"])
            source_row_index = int(row["input_row_index"])
        except ValueError as exc:
            raise MigrationError("migration mapping indices must be integers") from exc
        candidate = candidates[row["candidate_entry_id"]]
        if candidate["within_case_candidate_index"] != str(candidate_index):
            raise MigrationError("migration mapping candidate index disagrees with candidate table")
        if candidate["canonical_source_locator_key"] != row["canonical_source_locator_key"]:
            raise MigrationError("migration mapping locator disagrees with candidate table")
        expected_text_hash = sha256_bytes(candidate["taqrib_entry_text_verbatim"].encode("utf-8"))
        if row["taqrib_entry_text_sha256"] != expected_text_hash or not 1 <= source_row_index <= 11:
            raise MigrationError("migration mapping text hash or source row index is invalid")
    mapping_counts = Counter(row["source_file"] for row in tables["migration_mapping.csv"])
    if mapping_counts != Counter({FROZEN_NAME: 11, WORKING_NAME: 11}):
        raise MigrationError("migration row map must cover every row from both content inputs")
    for source_file in (FROZEN_NAME, WORKING_NAME):
        indices = {int(row["input_row_index"]) for row in tables["migration_mapping.csv"] if row["source_file"] == source_file}
        if indices != set(range(1, 12)):
            raise MigrationError(f"migration row map does not cover all rows in {source_file}")
        rows_by_index = {
            int(row["input_row_index"]): row
            for row in tables["migration_mapping.csv"]
            if row["source_file"] == source_file
        }
        for source_index, candidate in enumerate(tables["candidate_entries.csv"], start=1):
            row_map = rows_by_index[source_index]
            expected_statement_id = f"{candidate['candidate_entry_id']}-S00"
            expected_text_hash = sha256_bytes(candidate["taqrib_entry_text_verbatim"].encode("utf-8"))
            if (
                row_map["audit_record_id"] != candidate["audit_record_id"]
                or row_map["within_case_candidate_index"] != candidate["within_case_candidate_index"]
                or row_map["candidate_entry_id"] != candidate["candidate_entry_id"]
                or row_map["statement_id"] != expected_statement_id
                or row_map["taqrib_entry_text_sha256"] != expected_text_hash
                or row_map["source_locator_verbatim"] != candidate["source_locator_verbatim"]
                or row_map["canonical_source_locator_key"] != candidate["canonical_source_locator_key"]
            ):
                raise MigrationError(f"migration row map does not preserve validated input order for {source_file}")

    expected_legacy_keys = {
        (source_file, str(input_index), field)
        for source_file in (FROZEN_NAME, WORKING_NAME)
        for input_index in range(1, 12)
        for field in EXPECTED_HEADERS
    }
    observed_legacy_keys = {
        (row["source_file"], row["input_row_index"], row["field_name"])
        for row in tables["legacy_v1_values.csv"]
    }
    if observed_legacy_keys != expected_legacy_keys:
        raise MigrationError("legacy_v1_values.csv does not contain exactly one value per original input cell")
    for row in tables["legacy_v1_values.csv"]:
        candidate = _assert_link(candidates, row["candidate_entry_id"], "legacy_v1_values.csv", "candidate_entry_id")
        if row["audit_record_id"] != candidate["audit_record_id"]:
            raise MigrationError("legacy_v1_values.csv case/candidate references disagree")
        if row["source_file"] not in {FROZEN_NAME, WORKING_NAME} or row["field_name"] not in EXPECTED_HEADERS:
            raise MigrationError("legacy_v1_values.csv points to an unknown content input field")
        if not row["input_row_index"].isdigit() or not 1 <= int(row["input_row_index"]) <= 11:
            raise MigrationError("legacy_v1_values.csv has an invalid source row index")
    mapped_headers = {
        (row["source_file"], row["source_column"]) for row in tables["column_mapping.csv"]
    }
    for source_file, source_headers in ((FROZEN_NAME, EXPECTED_HEADERS), (WORKING_NAME, EXPECTED_HEADERS)):
        missing = {(source_file, header) for header in source_headers} - mapped_headers
        if missing:
            raise MigrationError(f"column_mapping.csv omits source columns: {sorted(missing)!r}")
    for row in tables["column_mapping.csv"]:
        if row["mapping_type"] not in {"copied", "mechanically_transformed", "legacy_only", "deferred_for_review"}:
            raise MigrationError("column_mapping.csv contains an invalid mapping type")
        if row["target_table"] not in set(OUTPUT_TABLES):
            raise MigrationError("column_mapping.csv points to an unknown output table")
        if row["mapping_type"] in {"legacy_only", "deferred_for_review"} and row["target_table"] != "legacy_v1_values.csv":
            raise MigrationError("legacy-only/deferred source values must point to the legacy snapshot")
        if row["target_column"] not in OUTPUT_TABLES[row["target_table"]]:
            raise MigrationError("column_mapping.csv target column is absent from its declared output table")

    referenced_evidence = set()
    referenced_evidence.update(row["identity_evidence_record_id"] for row in tables["candidate_entries.csv"] if row["identity_evidence_record_id"])
    referenced_evidence.update(row["statement_source_evidence_record_id"] for row in tables["statements.csv"] if row["statement_source_evidence_record_id"])
    referenced_evidence.update(row[field] for row in tables["attribution_links.csv"] for field in ("attribution_evidence_record_id", "transmission_route_evidence_record_id") if row[field])
    referenced_evidence.update(row["edition_metadata_evidence_record_id"] for row in tables["sources.csv"] if row["edition_metadata_evidence_record_id"])
    referenced_evidence.update(row["evidence_record_id"] for row in tables["date_claims.csv"] if row["evidence_record_id"])
    orphan_evidence = set(evidence) - referenced_evidence
    if orphan_evidence:
        raise MigrationError(f"source_evidence.csv contains unreferenced evidence records: {sorted(orphan_evidence)!r}")
    referenced_sources = {row["taqrib_source_record_id"] for row in tables["candidate_entries.csv"]}
    referenced_sources.update(row["source_record_id"] for row in tables["source_evidence.csv"])
    referenced_sources.update(row["source_record_id"] for row in tables["feature_sources.csv"])
    orphan_sources = set(sources) - referenced_sources
    if orphan_sources:
        raise MigrationError(f"sources.csv contains unreferenced source records: {sorted(orphan_sources)!r}")


ANALYTICAL_PURPOSES = {
    "statement_count",
    "grade_distribution",
    "annotation_completion",
    "training",
    "evaluation",
    "ordinary_grade_target",
}


def _reviewed_statement_has_source_provenance(
    tables: Mapping[str, list[dict[str, str]]], statement: Mapping[str, str]
) -> bool:
    if statement.get("statement_record_status") != "reviewed_statement" or statement.get("statement_id", "").endswith("-S00"):
        return False
    if statement.get("statement_text_status") != "transcribed" or not statement.get("statement_text_verbatim", "").strip():
        return False
    if statement.get("taqrib_statement_validity") != "supported_taqrib_statement":
        return False
    if statement.get("statement_source_correspondence") not in {"exact", "minor_variation"}:
        return False
    if statement.get("statement_source_span_status") != "transcribed" or not statement.get("statement_source_span_verbatim", "").strip():
        return False
    if not statement.get("statement_source_correspondence_rationale", "").strip() or not statement.get("statement_source_locator", "").strip():
        return False
    evidence_by_id = {row["evidence_record_id"]: row for row in tables.get("source_evidence.csv", [])}
    evidence = evidence_by_id.get(statement.get("statement_source_evidence_record_id", ""))
    if not evidence or evidence.get("evidence_role") != "passage_text" or evidence.get("statement_id") != statement.get("statement_id"):
        return False
    if evidence.get("evidence_text_status") != "transcribed" or not evidence.get("evidence_text_verbatim", "").strip():
        return False
    sources = {row["source_record_id"]: row for row in tables.get("sources.csv", [])}
    source = sources.get(evidence.get("source_record_id", ""))
    return bool(source) and source.get("source_verification_status") in {"verified_in_corpus", "verified_external_edition"}


def filter_analytical_rows(
    tables: Mapping[str, list[dict[str, str]]], purpose: str
) -> list[dict[str, str]]:
    """Return only review-complete rows allowed for the named analysis purpose.

    All downstream statistics and extracts should call this function instead of
    reading statements.csv directly. Provisional and superseded S00 records are
    never eligible, even if someone edits their text cells.
    """
    if purpose not in ANALYTICAL_PURPOSES:
        raise MigrationError(f"unknown analytical purpose: {purpose}")
    candidates = {row["candidate_entry_id"]: row for row in tables.get("candidate_entries.csv", [])}
    attributions_by_statement: dict[str, list[dict[str, str]]] = {}
    for row in tables.get("attribution_links.csv", []):
        attributions_by_statement.setdefault(row["statement_id"], []).append(row)
    sources = {row["source_record_id"]: row for row in tables.get("sources.csv", [])}
    evidence = {row["evidence_record_id"]: row for row in tables.get("source_evidence.csv", [])}
    eligible: list[dict[str, str]] = []
    for statement in tables.get("statements.csv", []):
        if statement.get("statement_record_status") != "reviewed_statement" or statement.get("statement_id", "").endswith("-S00"):
            continue
        candidate = candidates.get(statement.get("candidate_entry_id", ""))
        if not candidate:
            continue
        if purpose == "annotation_completion":
            # The denominator is real reviewed statements only; S00 work items are excluded.
            if candidate["taqrib_source_record_id"] not in sources:
                continue
            eligible.append(statement)
            continue
        if not _reviewed_statement_has_source_provenance(tables, statement):
            continue
        if purpose == "statement_count":
            eligible.append(statement)
            continue
        statement_attributions = attributions_by_statement.get(statement["statement_id"], [])
        if len(statement_attributions) != 1:
            continue
        target_source = sources.get(candidate.get("taqrib_source_record_id", ""))
        if not target_source:
            continue
        if ordinary_grade_candidate_conditions_pass(
            candidate,
            statement,
            statement_attributions[0],
            target_source,
            evidence_by_id=evidence,
            sources_by_id=sources,
        ):
            eligible.append(statement)
    return eligible


def annotation_completion_counts(tables: Mapping[str, list[dict[str, str]]]) -> dict[str, int]:
    """Return reviewed-statement completion counts without putting placeholders in the denominator."""
    denominator_rows = filter_analytical_rows(tables, "annotation_completion")
    complete = sum(
        _reviewed_statement_has_source_provenance(tables, row)
        and row.get("statement_type") != "not_assessed"
        and row.get("target_task_scope") not in {"not_assessed", "unresolved"}
        and row.get("historical_input_eligibility") not in {"not_assessed", "unresolved"}
        for row in denominator_rows
    )
    return {"denominator": len(denominator_rows), "complete": complete}


def export_analytical_rows(
    tables: Mapping[str, list[dict[str, str]]], purpose: str, output_path: Path
) -> int:
    """Write an analysis CSV only after applying the provisional-item filter."""
    rows = filter_analytical_rows(tables, purpose)
    write_csv_file(Path(output_path), rows, OUTPUT_TABLES["statements.csv"])
    return len(rows)


def _validate_staged_package(stage: Path, tables: Mapping[str, list[dict[str, str]]]) -> None:
    if not (stage / "manifest.json").is_file() or not (stage / "MANIFEST.sha256").is_file():
        raise MigrationError("staged manifest or checksum is missing")
    manifest_path = stage / "manifest.json"
    checksum_path = stage / "MANIFEST.sha256"
    manifest_bytes = manifest_path.read_bytes()
    checksum_line = checksum_path.read_text(encoding="ascii")
    expected_manifest_hash = sha256_bytes(manifest_bytes)
    if checksum_line != f"{expected_manifest_hash}  manifest.json\n":
        raise MigrationError("staged manifest checksum validation failed")
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    output_hashes = manifest.get("outputs_sha256", {})
    output_meta = manifest.get("outputs", {})
    expected_output_names = set(tables) | {"schema_field_registry.json"}
    if set(output_hashes) != expected_output_names or set(output_meta) != expected_output_names:
        raise MigrationError("manifest output inventory does not match generated data files")
    if "manifest.json" in output_hashes or "MANIFEST.sha256" in output_hashes:
        raise MigrationError("manifest/checksum must not hash themselves")

    parsed_tables: dict[str, list[dict[str, str]]] = {}
    for filename, rows in tables.items():
        path = stage / filename
        if not path.is_file() or sha256_file(path) != output_hashes.get(filename):
            raise MigrationError(f"staged output hash mismatch: {filename}")
        metadata = output_meta.get(filename, {})
        if metadata.get("sha256") != output_hashes.get(filename) or metadata.get("bytes") != path.stat().st_size:
            raise MigrationError(f"staged output metadata mismatch: {filename}")
        headers, actual_rows = read_csv(path)
        if headers != OUTPUT_TABLES[filename] or headers != metadata.get("headers"):
            raise MigrationError(f"staged output headers mismatch: {filename}")
        if actual_rows != rows or len(actual_rows) != metadata.get("rows"):
            raise MigrationError(f"staged output rows mismatch: {filename}")
        parsed_tables[filename] = actual_rows
    validate_package_tables(parsed_tables)

    registry_path = stage / "schema_field_registry.json"
    registry_metadata = output_meta["schema_field_registry.json"]
    if not registry_path.is_file() or sha256_file(registry_path) != output_hashes["schema_field_registry.json"]:
        raise MigrationError("staged schema field registry hash mismatch")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if registry != build_schema_field_registry():
        raise MigrationError("staged schema field registry does not match implementation")
    if registry_metadata.get("bytes") != registry_path.stat().st_size or registry_metadata.get("rows") != len(registry["fields"]):
        raise MigrationError("staged schema field registry metadata mismatch")

    expected_counts = {
        "cases": len(parsed_tables["cases.csv"]),
        "candidate_entries": len(parsed_tables["candidate_entries.csv"]),
        "provisional_work_items": sum(row["statement_record_status"] in {"provisional_work_item", "superseded_placeholder"} for row in parsed_tables["statements.csv"]),
        "reviewed_scholarly_statements": sum(row["statement_record_status"] == "reviewed_statement" for row in parsed_tables["statements.csv"]),
        "legacy_values": len(parsed_tables["legacy_v1_values.csv"]),
        "legacy_empty_cells": sum(row["is_empty_cell"] == "true" for row in parsed_tables["legacy_v1_values.csv"]),
    }
    if manifest.get("counts") != expected_counts:
        raise MigrationError("manifest counts do not match validated output tables")
    if manifest.get("status_counts") != _manifest_status_counts(parsed_tables):
        raise MigrationError("manifest status counts do not match validated output tables")
    if manifest.get("missingness_counts") != _manifest_missingness_counts(parsed_tables):
        raise MigrationError("manifest missingness counts do not match validated output tables")
    validation_results = manifest.get("validation_results", {})
    if not validation_results or any(value != "passed" for value in validation_results.values()):
        raise MigrationError("manifest does not record successful pre-publication validation")

    expected_files = expected_output_names | {"manifest.json", "MANIFEST.sha256"}
    actual_files = {path.name for path in stage.iterdir() if path.is_file()}
    if actual_files != expected_files or any(path.is_dir() for path in stage.iterdir()):
        raise MigrationError("staged directory contains missing or unexpected files")


def _safe_remove_owned(path: Path, parent: Path, token: str, *, directory: bool) -> None:
    try:
        resolved_parent = parent.resolve()
        resolved_path = path.resolve()
        if resolved_path.parent != resolved_parent:
            return
        if directory:
            if path.name.startswith(".") and path.name.endswith(f".staging-{token}") and path.is_dir():
                shutil.rmtree(path)
        elif path.is_file() and path.read_text(encoding="ascii") == token:
            path.unlink()
    except FileNotFoundError:
        return


def migrate_package(
    input_dir: Path,
    output_dir: Path,
    *,
    expected_hashes: Mapping[str, str] | None = None,
    validator=None,
) -> dict[str, object]:
    """Validate inputs, stage a deterministic package, and atomically publish it."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    expected = dict(expected_hashes or EXPECTED_INPUT_HASHES)
    if output_dir.exists():
        raise MigrationError(f"output directory already exists: {output_dir}")
    if not output_dir.parent.is_dir():
        raise MigrationError(f"output parent directory does not exist: {output_dir.parent}")

    payloads, input_hashes = _verify_inputs(input_dir, expected)
    source_metadata = _validate_manifest_metadata(payloads[MANIFEST_NAME], input_hashes[FROZEN_NAME], input_hashes[KEY_NAME])
    frozen_headers, frozen_rows = read_csv(input_dir / FROZEN_NAME)
    working_headers, working_rows = read_csv(input_dir / WORKING_NAME)
    if frozen_headers != EXPECTED_HEADERS or working_headers != EXPECTED_HEADERS:
        raise MigrationError("input CSV headers/order do not match the frozen v1 pilot schema")
    joined = _validate_and_join(frozen_rows, working_rows)
    tables = _build_tables(joined, source_metadata)
    tables["column_mapping.csv"] = _build_column_mapping(frozen_headers, working_headers, source_metadata)
    validate_package_tables(tables)

    token = uuid.uuid4().hex
    lock_path = output_dir.parent / f".{output_dir.name}.run-lock"
    stage = output_dir.parent / f".{output_dir.name}.staging-{token}"
    lock_fd = None
    owns_lock = False
    owns_stage = False
    try:
        try:
            lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise MigrationError(f"migration run lock already exists: {lock_path}") from exc
        owns_lock = True
        os.write(lock_fd, token.encode("ascii"))
        os.fsync(lock_fd)
        os.close(lock_fd)
        lock_fd = None

        if output_dir.exists():
            raise MigrationError(f"output directory already exists: {output_dir}")
        stage.mkdir()
        owns_stage = True

        for filename, rows in tables.items():
            write_csv_file(stage / filename, rows, OUTPUT_TABLES[filename])
        registry = build_schema_field_registry()
        registry_path = stage / "schema_field_registry.json"
        registry_path.write_text(
            json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )

        input_meta = {}
        for filename, payload in payloads.items():
            input_path = input_dir / filename
            encoding = "utf-8-sig" if payload.startswith(b"\xef\xbb\xbf") else "utf-8"
            if filename.endswith(".csv"):
                input_headers, input_rows = read_csv(input_path)
                row_count = len(input_rows)
            else:
                input_headers = []
                row_count = 1
            path_value = str(input_path.relative_to(ROOT)) if input_path.is_relative_to(ROOT) else str(input_path.resolve())
            input_meta[filename] = {
                "path": path_value,
                "sha256": input_hashes[filename],
                "bytes": len(payload),
                "row_count": row_count,
                "headers": input_headers,
                "encoding": encoding,
                "row_count_semantics": "CSV data rows excluding header" if filename.endswith(".csv") else "one top-level JSON object",
                "role": "content" if filename in {FROZEN_NAME, WORKING_NAME} else "read_only_provenance",
            }

        output_files = sorted(tables) + ["schema_field_registry.json"]
        outputs_hashes = {filename: sha256_file(stage / filename) for filename in output_files}
        output_metadata = {}
        for filename in sorted(tables):
            output_metadata[filename] = {
                "path": filename,
                "sha256": outputs_hashes[filename],
                "bytes": (stage / filename).stat().st_size,
                "rows": len(tables[filename]),
                "headers": OUTPUT_TABLES[filename],
                "encoding": "utf-8",
            }
        output_metadata["schema_field_registry.json"] = {
            "path": "schema_field_registry.json",
            "sha256": outputs_hashes["schema_field_registry.json"],
            "bytes": registry_path.stat().st_size,
            "rows": len(registry["fields"]),
            "headers": None,
            "encoding": "utf-8",
        }
        counts = {
            "cases": len(tables["cases.csv"]),
            "candidate_entries": len(tables["candidate_entries.csv"]),
            "provisional_work_items": sum(row["statement_record_status"] in {"provisional_work_item", "superseded_placeholder"} for row in tables["statements.csv"]),
            "reviewed_scholarly_statements": sum(row["statement_record_status"] == "reviewed_statement" for row in tables["statements.csv"]),
            "legacy_values": len(tables["legacy_v1_values.csv"]),
            "legacy_empty_cells": sum(row["is_empty_cell"] == "true" for row in tables["legacy_v1_values.csv"]),
        }
        script_path = Path(__file__).resolve()
        frozen_spec_path = ROOT / "dataset_discovery" / "target_feasibility" / "MANUAL_COLLATION_SCHEMA_V2_2_FINAL.md"
        manifest = {
            "schema_name": "manual_collation_schema",
            "schema_version": "2.2",
            "schema_status": "frozen_implementation_baseline",
            "implementation_version": IMPLEMENTATION_VERSION,
            "migration_script": str(script_path.relative_to(ROOT)),
            "script_sha256": sha256_file(script_path),
            "runtime": {
                "python_version": sys.version.split()[0],
                "python_implementation": sys.implementation.name,
                "platform": platform.platform(),
            },
            "frozen_specification": {
                "path": str(frozen_spec_path.relative_to(ROOT)),
                "sha256": sha256_file(frozen_spec_path),
            },
            "input_files": input_meta,
            "input_source_corpus_metadata": source_metadata,
            "outputs_sha256": outputs_hashes,
            "outputs": output_metadata,
            "manifest_checksum_file": "MANIFEST.sha256",
            "counts": counts,
            "status_counts": _manifest_status_counts(tables),
            "missingness_counts": _manifest_missingness_counts(tables),
            "not_assessed_counts_are_decisions": False,
            "row_mapping_file": "migration_mapping.csv",
            "column_mapping_file": "column_mapping.csv",
            "schema_field_registry_file": "schema_field_registry.json",
            "validation_results": {
                "pinned_input_hashes_and_manifest_history": "passed",
                "source_row_join_and_unique_keys": "passed",
                "field_schemas_enums_and_cross_field_invariants": "passed",
                "foreign_keys_and_row_links": "passed",
                "provisional_work_item_analytical_exclusion": "passed",
                "column_mapping_coverage": "passed",
                "output_hash_manifest_and_checksum_validation": "passed",
            },
            "annotations_inferred": False,
            "statement_segmentation_inferred": False,
            "rank_assignments_migrated": False,
            "provisional_work_items_excluded_from_analysis": True,
            "no_human_annotation_decisions_populated": True,
            "row_count_semantics": "provisional_work_items are operational placeholders, not scholarly statement counts.",
        }
        manifest_path = stage / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        manifest_hash = sha256_file(manifest_path)
        (stage / "MANIFEST.sha256").write_text(f"{manifest_hash}  manifest.json\n", encoding="ascii", newline="\n")

        validate = validator or _validate_staged_package
        try:
            validate(stage, tables)
        except Exception as exc:
            raise MigrationError(f"staged package validation failed: {exc}") from exc

        if output_dir.exists():
            raise MigrationError(f"output directory appeared before publication: {output_dir}")
        try:
            os.rename(stage, output_dir)
        except OSError as exc:
            raise MigrationError(f"atomic same-volume publication failed: {exc}") from exc
        owns_stage = False
        return manifest
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
        if owns_stage:
            _safe_remove_owned(stage, output_dir.parent, token, directory=True)
        if owns_lock:
            _safe_remove_owned(lock_path, output_dir.parent, token, directory=False)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    try:
        manifest = migrate_package(args.input_dir, args.output_dir)
    except MigrationError as exc:
        parser.exit(2, f"migration stopped: {exc}\n")
    print(
        f"Published schema v2.2 scaffold: {args.output_dir}\n"
        f"Cases: {manifest['counts']['cases']}; candidates: {manifest['counts']['candidate_entries']}; "
        f"provisional work items: {manifest['counts']['provisional_work_items']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
