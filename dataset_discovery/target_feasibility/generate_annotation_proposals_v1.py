#!/usr/bin/env python3
"""Generate read-only Annotation Automation v1 development proposals.

Only three explicitly authorized, exact Taqrib rank rules are executable in
this development dry-run. The registry remains a candidate registry; this
module does not promote rules to production or write reviewed annotations.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
PILOT_DIR = (
    ROOT
    / "data"
    / "2_interim"
    / "shamela4_narrator_audit"
    / "manual_annotation_working"
    / "manual_collation_pilot_10_review_round_1_working"
)
DEFAULT_REGISTRY = ROOT / "dataset_discovery" / "target_feasibility" / "ANNOTATION_AUTOMATION_RULE_REGISTRY_V1.csv"
DEFAULT_OUTPUT = ROOT / "data" / "2_interim" / "shamela4_narrator_audit" / "annotation_automation_v1_0_1_development_dry_run"
PACKAGE_VERSION = "1.0.1"

EXPECTED_RANK_RULES = {
    "RANK_THIQA_EXACT_001": ("ثقة", 3),
    "RANK_SADUQ_ERROR_EXACT_001": ("صدوق يخطىء", 5),
    "RANK_SADUQ_IKHTILAT_EXACT_001": ("صدوق اختلط في الآخر", 5),
}
PILOT_CASE_IDS = {"PROV-10", "PROV-40", "PROV-39", "PROV-56", "PROV-24", "PROV-51", "PROV-01", "PROV-02", "PROV-04", "PROV-37"}
PILOT_CANDIDATE_ENTRY_IDS = {
    "PROV-10-C01", "PROV-40-C01", "PROV-39-C01", "PROV-56-C01", "PROV-24-C01",
    "PROV-51-C01", "PROV-01-C01", "PROV-02-C01", "PROV-04-C01", "PROV-04-C02", "PROV-37-C01",
}

INPUT_FILES = {
    "candidate_entries": "candidate_entries.csv",
    "statements": "statements.csv",
    "sources": "sources.csv",
    "source_evidence": "source_evidence.csv",
    "working_manifest": "WORKING_COPY_MANIFEST.json",
}

TABLE_REQUIRED_FIELDS = {
    "candidate_entries": {
        "audit_record_id",
        "candidate_entry_id",
        "dataset_narrator_id",
        "dataset_narrator_name",
        "identity_match_status",
        "candidate_entry_text_status",
        "candidate_field_source_correspondence",
        "taqrib_source_record_id",
        "taqrib_entry_text_verbatim",
    },
    "statements": {
        "audit_record_id",
        "candidate_entry_id",
        "statement_id",
        "statement_record_status",
        "statement_text_verbatim",
        "statement_text_status",
        "taqrib_statement_validity",
        "statement_source_correspondence",
        "statement_source_span_verbatim",
        "statement_source_span_status",
        "statement_source_locator",
        "statement_source_evidence_record_id",
    },
    "sources": {
        "source_record_id",
        "candidate_entry_id",
        "source_work_id",
        "source_verification_status",
        "source_locator_verbatim",
    },
    "source_evidence": {
        "evidence_record_id",
        "source_record_id",
        "candidate_entry_id",
        "statement_id",
        "evidence_role",
        "evidence_text_verbatim",
        "evidence_text_status",
        "source_locator",
    },
}

PROPOSAL_FIELDS = [
    "proposal_id",
    "audit_record_id",
    "candidate_entry_id",
    "statement_id",
    "narrator_id",
    "narrator_name",
    "statement_text_verbatim",
    "statement_source_span_verbatim",
    "source_entry_text_verbatim",
    "source_span_occurrence_count",
    "statement_source_evidence_record_id",
    "source_record_id",
    "source_work_id",
    "source_verification_status",
    "statement_source_locator",
    "proposal_status",
    "rule_id",
    "rule_version",
    "rule_family",
    "proposed_taqrib_rank_number",
    "proposed_rank_status",
    "abstention_reason",
    "human_review_required",
    "auto_accept",
]

HUMAN_REVIEW_FIELDS = PROPOSAL_FIELDS + [
    "human_decision",
    "human_rank_number",
    "human_statement_type",
    "human_target_suitability",
    "human_historical_input_eligibility",
    "reviewer_notes",
    "reviewed_at",
]


class PreflightError(ValueError):
    """Raised when the input package is incomplete or inconsistent."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(data: object) -> bytes:
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise PreflightError(f"CSV has no header: {path}")
        rows = list(reader)
        if any(None in row for row in rows):
            raise PreflightError(f"CSV row has more fields than its header: {path}")
        return list(reader.fieldnames), rows


def read_table(path: Path, table_name: str) -> list[dict[str, str]]:
    headers, rows = read_csv(path)
    missing = TABLE_REQUIRED_FIELDS[table_name] - set(headers)
    if missing:
        raise PreflightError(f"{table_name} is missing required columns: {sorted(missing)}")
    return rows


def assert_unique(rows: Iterable[Mapping[str, str]], key: str, table_name: str) -> None:
    seen: set[str] = set()
    for row in rows:
        value = row.get(key, "")
        if not value or value in seen:
            raise PreflightError(f"{table_name} has a blank or duplicate {key}: {value!r}")
        seen.add(value)


def validate_working_manifest(input_paths: Mapping[str, Path], hashes: Mapping[str, str]) -> dict:
    manifest_path = input_paths["working_manifest"]
    sidecar_path = manifest_path.with_suffix(".sha256")
    if not sidecar_path.is_file():
        raise PreflightError(f"Working-copy manifest checksum is missing: {sidecar_path}")
    sidecar_text = sidecar_path.read_text(encoding="ascii").strip().split()
    if not sidecar_text or sidecar_text[0].lower() != hashes["working_manifest"]:
        raise PreflightError("Working-copy manifest checksum does not match its sidecar")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreflightError(f"Cannot read working-copy manifest: {exc}") from exc
    file_entries = manifest.get("files")
    if not isinstance(file_entries, dict):
        raise PreflightError("Working-copy manifest has no file-hash mapping")
    for key, filename in INPUT_FILES.items():
        if key == "working_manifest":
            continue
        entry = file_entries.get(filename)
        actual_path = input_paths[key]
        if not isinstance(entry, dict) or not actual_path.is_file():
            raise PreflightError(f"Manifest entry or input file missing for {filename}")
        digest = hashes[key]
        if entry.get("sha256") != digest or entry.get("bytes") != actual_path.stat().st_size:
            raise PreflightError(f"Input does not match the working-copy manifest: {filename}")
    return manifest


def validate_registry(registry_rows: list[dict[str, str]]) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    assert_unique(registry_rows, "rule_id", "rule registry")
    by_id = {row["rule_id"]: row for row in registry_rows}
    active: dict[str, dict[str, str]] = {}
    for rule_id, (phrase, rank) in EXPECTED_RANK_RULES.items():
        row = by_id.get(rule_id)
        if row is None:
            raise PreflightError(f"Authorized rank rule is missing from registry: {rule_id}")
        try:
            proposed = json.loads(row["proposed_fields_json"])
        except json.JSONDecodeError as exc:
            raise PreflightError(f"Invalid proposed_fields_json for {rule_id}") from exc
        if (
            row.get("rule_status") != "candidate_not_enabled"
            or row.get("rule_family") != "taxonomy_rank"
            or row.get("exact_complete_span") != phrase
            or proposed != {"taqrib_rank_number": rank, "rank_status": "assigned"}
            or row.get("auto_accept", "").lower() != "false"
            or row.get("human_review_required", "").lower() != "true"
        ):
            raise PreflightError(f"Registry differs from the authorized development rule: {rule_id}")
        active[phrase] = row
    disabled: dict[str, dict[str, str]] = {}
    for row in registry_rows:
        if row.get("rule_family") == "generation_status" and row.get("exact_complete_span"):
            if row.get("rule_status") == "candidate_not_enabled":
                disabled[row["exact_complete_span"]] = row
    return active, disabled


def _abstain(row: dict[str, str], reason: str, rule: Mapping[str, str] | None = None) -> dict[str, str]:
    result = {field: "" for field in PROPOSAL_FIELDS}
    result.update(
        {
            "proposal_id": f"AUTO1-{row['statement_id']}",
            "audit_record_id": row.get("audit_record_id", ""),
            "candidate_entry_id": row.get("candidate_entry_id", ""),
            "statement_id": row.get("statement_id", ""),
            "statement_text_verbatim": row.get("statement_text_verbatim", ""),
            "statement_source_span_verbatim": row.get("statement_source_span_verbatim", ""),
            "statement_source_evidence_record_id": row.get("statement_source_evidence_record_id", ""),
            "statement_source_locator": row.get("statement_source_locator", ""),
            "proposal_status": "abstain",
            "abstention_reason": reason,
            "human_review_required": "true",
            "auto_accept": "false",
        }
    )
    if rule is not None:
        result.update(
            {
                "rule_id": rule.get("rule_id", ""),
                "rule_version": rule.get("rule_version", ""),
                "rule_family": rule.get("rule_family", ""),
            }
        )
    return result


def _gate_reason(
    candidate: Mapping[str, str] | None,
    statement: Mapping[str, str],
    source: Mapping[str, str] | None,
    evidence: Mapping[str, str] | None,
) -> str:
    if candidate is None:
        return "candidate_entry_missing"
    if candidate.get("identity_match_status") != "confirmed":
        return "candidate_identity_not_confirmed"
    if candidate.get("candidate_entry_text_status") != "transcribed":
        return "candidate_entry_text_unverified"
    if candidate.get("candidate_field_source_correspondence") not in {"exact", "minor_variation"}:
        return "candidate_source_correspondence_unresolved"
    if statement.get("statement_text_status") != "transcribed":
        return "statement_text_unverified"
    if statement.get("statement_source_span_status") != "transcribed":
        return "statement_source_span_unverified"
    if statement.get("statement_source_span_verbatim") != statement.get("statement_text_verbatim"):
        return "statement_source_span_not_exact"
    entry_text = candidate.get("taqrib_entry_text_verbatim", "")
    statement_text = statement.get("statement_text_verbatim", "")
    if not entry_text or not statement_text:
        return "source_entry_or_statement_text_missing"
    occurrences = entry_text.count(statement_text)
    if occurrences == 0:
        return "statement_not_found_exactly_in_entry"
    if occurrences > 1:
        return "statement_span_ambiguous_in_entry"
    if statement.get("statement_source_correspondence") != "exact":
        return "statement_source_correspondence_not_exact"
    if statement.get("taqrib_statement_validity") != "supported_taqrib_statement":
        return "statement_not_supported_in_taqrib"
    if source is None or source.get("source_record_id") != candidate.get("taqrib_source_record_id"):
        return "taqrib_source_record_missing_or_mismatched"
    if source.get("candidate_entry_id") != candidate.get("candidate_entry_id"):
        return "taqrib_source_record_missing_or_mismatched"
    if source.get("source_work_id") != "3076":
        return "taqrib_source_work_not_confirmed"
    if source.get("source_verification_status") not in {"verified_in_corpus", "verified_external_edition"}:
        return "taqrib_source_not_verified"
    if evidence is None:
        return "statement_evidence_missing_or_mismatched"
    if (
        evidence.get("statement_id") != statement.get("statement_id")
        or evidence.get("source_record_id") != source.get("source_record_id")
        or evidence.get("evidence_role") != "passage_text"
        or evidence.get("evidence_text_status") != "transcribed"
        or evidence.get("evidence_text_verbatim") != statement.get("statement_text_verbatim")
        or evidence.get("source_locator") != statement.get("statement_source_locator")
    ):
        return "statement_evidence_missing_or_mismatched"
    return ""


def build_proposals(
    candidate_rows: list[dict[str, str]],
    statement_rows: list[dict[str, str]],
    source_rows: list[dict[str, str]],
    evidence_rows: list[dict[str, str]],
    registry_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Return one proposal or explicit abstention per reviewed statement."""
    active_rules, disabled_rules = validate_registry(registry_rows)
    assert_unique(candidate_rows, "candidate_entry_id", "candidate entries")
    assert_unique(statement_rows, "statement_id", "statements")
    assert_unique(source_rows, "source_record_id", "sources")
    assert_unique(evidence_rows, "evidence_record_id", "source evidence")
    candidates = {row["candidate_entry_id"]: row for row in candidate_rows}
    sources = {row["source_record_id"]: row for row in source_rows}
    evidence_by_id = {row["evidence_record_id"]: row for row in evidence_rows}

    proposals: list[dict[str, str]] = []
    for statement in statement_rows:
        if statement.get("statement_record_status") != "reviewed_statement":
            continue
        candidate = candidates.get(statement.get("candidate_entry_id", ""))
        source = sources.get(candidate.get("taqrib_source_record_id", "")) if candidate else None
        evidence = evidence_by_id.get(statement.get("statement_source_evidence_record_id", ""))
        rule = active_rules.get(statement.get("statement_text_verbatim", ""))
        disabled_rule = disabled_rules.get(statement.get("statement_text_verbatim", ""))

        if candidate is None:
            proposal = _abstain(statement, "candidate_entry_missing")
        elif candidate.get("identity_match_status") != "confirmed":
            proposal = _abstain(statement, "candidate_identity_not_confirmed", rule or disabled_rule)
        elif rule is None and disabled_rule is None:
            proposal = _abstain(statement, "no_exact_enabled_rule_match")
        elif disabled_rule is not None:
            proposal = _abstain(statement, "candidate_rule_not_enabled", disabled_rule)
        else:
            gate_reason = _gate_reason(candidate, statement, source, evidence)
            if gate_reason:
                proposal = _abstain(statement, gate_reason, rule)
            else:
                proposed = json.loads(rule["proposed_fields_json"])
                proposal = _abstain(statement, "", rule)
                proposal.update(
                    {
                        "proposal_status": "proposed_for_human_review",
                        "proposed_taqrib_rank_number": str(proposed["taqrib_rank_number"]),
                        "proposed_rank_status": proposed["rank_status"],
                        "abstention_reason": "",
                    }
                )

        if candidate:
            entry_text = candidate.get("taqrib_entry_text_verbatim", "")
            statement_text = statement.get("statement_text_verbatim", "")
            proposal.update(
                {
                    "narrator_id": candidate.get("dataset_narrator_id", ""),
                    "narrator_name": candidate.get("dataset_narrator_name", ""),
                    "source_entry_text_verbatim": candidate.get("taqrib_entry_text_verbatim", ""),
                    "source_span_occurrence_count": str(entry_text.count(statement_text)) if statement_text else "0",
                }
            )
        if source:
            proposal.update(
                {
                    "source_record_id": source.get("source_record_id", ""),
                    "source_work_id": source.get("source_work_id", ""),
                    "source_verification_status": source.get("source_verification_status", ""),
                }
            )
        proposals.append(proposal)
    return proposals


def _write_csv(path: Path, fieldnames: list[str], rows: list[Mapping[str, str]]) -> None:
    # The UTF-8 BOM helps Windows Excel detect Arabic text when opening a CSV directly.
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _relative_input_record(path: Path, label: str, root: Path) -> dict[str, object]:
    try:
        display_path = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        display_path = path.name
    return {
        "input_id": label,
        "path": display_path,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _build_human_rows(proposals: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for proposal in proposals:
        row = {field: proposal.get(field, "") for field in PROPOSAL_FIELDS}
        row.update(
            {
                "human_decision": "",
                "human_rank_number": "",
                "human_statement_type": "",
                "human_target_suitability": "",
                "human_historical_input_eligibility": "",
                "reviewer_notes": "",
                "reviewed_at": "",
            }
        )
        rows.append(row)
    return rows


def run_pipeline(
    input_paths: Mapping[str, Path],
    registry_path: Path,
    output_dir: Path,
    *,
    generated_at_utc: str | None = None,
    run_scope: str = "development_only_existing_pilot",
) -> dict:
    """Validate inputs, create a new output directory, and write a dry-run package."""
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing output directory: {output_dir}")
    if run_scope not in {"development_only_existing_pilot", "unit_test_fixture"}:
        raise ValueError(f"Unsupported run scope: {run_scope}")
    normalized = {key: Path(value) for key, value in input_paths.items()}
    missing_keys = set(INPUT_FILES) - set(normalized)
    if missing_keys:
        raise PreflightError(f"Missing input paths: {sorted(missing_keys)}")
    for key, path in normalized.items():
        if not path.is_file():
            raise PreflightError(f"Required input file is missing: {path}")
    if not Path(registry_path).is_file():
        raise PreflightError(f"Rule registry is missing: {registry_path}")

    hashes = {key: sha256_file(path) for key, path in normalized.items()}
    working_manifest = validate_working_manifest(normalized, hashes)
    table_rows = {
        key: read_table(normalized[key], key)
        for key in ("candidate_entries", "statements", "sources", "source_evidence")
    }
    if run_scope == "development_only_existing_pilot":
        expected_input_paths = {key: (PILOT_DIR / filename).resolve() for key, filename in INPUT_FILES.items()}
        if {key: path.resolve() for key, path in normalized.items()} != expected_input_paths:
            raise PreflightError("The development run is restricted to the existing PROV pilot input directory")
        actual_case_ids = {row["audit_record_id"] for row in table_rows["candidate_entries"]}
        actual_candidate_ids = {row["candidate_entry_id"] for row in table_rows["candidate_entries"]}
        if actual_case_ids != PILOT_CASE_IDS or actual_candidate_ids != PILOT_CANDIDATE_ENTRY_IDS:
            raise PreflightError("The development input is not the registered 10-case PROV pilot sample")
    _, registry_rows = read_csv(Path(registry_path))
    validate_registry(registry_rows)
    proposals = build_proposals(
        table_rows["candidate_entries"],
        table_rows["statements"],
        table_rows["sources"],
        table_rows["source_evidence"],
        registry_rows,
    )
    reviewed_count = sum(row.get("statement_record_status") == "reviewed_statement" for row in table_rows["statements"])
    skipped_count = len(table_rows["statements"]) - reviewed_count
    if len(proposals) != reviewed_count:
        raise PreflightError("Proposal rows do not match the number of reviewed statements")

    registry_bytes = Path(registry_path).read_bytes()
    registry_hash = sha256_bytes(registry_bytes)
    sample_manifest = {
        "package_version": PACKAGE_VERSION,
        "scope": run_scope,
        "research_status": "rule_development_only_not_evaluation",
        "statement_annotation_population": "reviewed_statement rows only; non-statement placeholders excluded",
        "case_ids": sorted({row["audit_record_id"] for row in table_rows["candidate_entries"]}),
        "candidate_entry_ids": sorted(row["candidate_entry_id"] for row in table_rows["candidate_entries"]),
        "counts": {
            "case_count": len({row["audit_record_id"] for row in table_rows["candidate_entries"]}),
            "candidate_entry_count": len(table_rows["candidate_entries"]),
            "statement_rows_in_input": len(table_rows["statements"]),
            "reviewed_statement_count": reviewed_count,
            "excluded_placeholder_or_nonreviewed_count": skipped_count,
        },
        "inputs": [
            _relative_input_record(normalized[key], filename, ROOT)
            for key, filename in INPUT_FILES.items()
        ]
        + [
            _relative_input_record(normalized["working_manifest"].with_suffix(".sha256"), "working_manifest_sha256_sidecar", ROOT),
            _relative_input_record(Path(registry_path), "rule_registry", ROOT),
        ],
        "source_packet_manifest_sha256": working_manifest.get("source_packet_manifest_sha256", ""),
        "limit": "The purposive ten-case pilot is used only as development material. No accuracy, precision, expert-validity, or corpus-wide coverage claim is produced.",
    }

    active_rule_ids = sorted(EXPECTED_RANK_RULES)
    counts_by_status = Counter(row["proposal_status"] for row in proposals)
    abstentions_by_reason = Counter(row["abstention_reason"] for row in proposals if row["proposal_status"] == "abstain")
    suggestions_by_rule = Counter(row["rule_id"] for row in proposals if row["proposal_status"] == "proposed_for_human_review")
    generated_at_utc = generated_at_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        datetime.fromisoformat(generated_at_utc.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("generated_at_utc must be an ISO-8601 timestamp") from exc

    # All content is validated before creating the destination. mkdir(exist_ok=False)
    # is the final no-overwrite guard for concurrent runs.
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(exist_ok=False)
    try:
        sample_manifest_bytes = canonical_json(sample_manifest)
        (output_dir / "INPUT_SAMPLE_MANIFEST.json").write_bytes(sample_manifest_bytes)
        (output_dir / "RULE_REGISTRY_SNAPSHOT.csv").write_bytes(registry_bytes)
        _write_csv(output_dir / "ANNOTATION_AUTO_PROPOSALS.csv", PROPOSAL_FIELDS, proposals)
        _write_csv(output_dir / "HUMAN_REVIEW.csv", HUMAN_REVIEW_FIELDS, _build_human_rows(proposals))

        output_names = [
            "INPUT_SAMPLE_MANIFEST.json",
            "RULE_REGISTRY_SNAPSHOT.csv",
            "ANNOTATION_AUTO_PROPOSALS.csv",
            "HUMAN_REVIEW.csv",
        ]
        output_hashes = {name: sha256_file(output_dir / name) for name in output_names}
        run_manifest = {
            "package_version": PACKAGE_VERSION,
            "csv_encoding": "UTF-8 with BOM for spreadsheet compatibility",
            "generated_at_utc": generated_at_utc,
            "scope": run_scope,
            "run_type": "controlled_read_only_dry_run",
            "rules_enabled_for_this_run": active_rule_ids,
            "registry_rule_status_preserved": True,
            "rank_taxonomy": {
                "research_target_label_space": "Ibn Hajar's complete 12-rank taxonomy",
                "rank_values": list(range(1, 13)),
                "initial_executable_subset_only": {rule_id: {"exact_span": span, "rank": rank} for rule_id, (span, rank) in EXPECTED_RANK_RULES.items()},
                "rank_1_companion_status_is_separate": True,
                "equal_interval_assumption": False,
            },
            "proposed_dimensions": ["Taqrib taxonomy rank only"],
            "not_proposed": ["candidate identity", "statement segmentation", "historical evaluator", "compiler authorship", "transmission route", "target suitability", "historical-input eligibility"],
            "counts": {
                "case_count": sample_manifest["counts"]["case_count"],
                "candidate_entry_count": sample_manifest["counts"]["candidate_entry_count"],
                "reviewed_statement_count": reviewed_count,
                "excluded_placeholder_or_nonreviewed_count": skipped_count,
                "proposal_row_count": len(proposals),
                "proposed_for_human_review_count": counts_by_status["proposed_for_human_review"],
                "abstention_count": counts_by_status["abstain"],
                "proposals_by_rule": dict(sorted(suggestions_by_rule.items())),
                "abstentions_by_reason": dict(sorted(abstentions_by_reason.items())),
            },
            "input_manifest_sha256": sha256_file(output_dir / "INPUT_SAMPLE_MANIFEST.json"),
            "rule_registry_sha256": registry_hash,
            "software": {
                "python_version": platform.python_version(),
                "script_path": Path(__file__).resolve().relative_to(ROOT).as_posix(),
                "script_sha256": sha256_file(Path(__file__).resolve()),
            },
            "output_sha256": output_hashes,
            "integrity_notes": [
                "Original inputs and working annotations were read only.",
                "Human review fields are blank; no machine proposal is auto-accepted.",
                "The registry remains unchanged; only the three user-authorized rank rule IDs were used for this development run.",
                "S00 and other non-reviewed placeholders are excluded from the proposal population.",
                "No semantics are inferred from the dataset's integer source IDs.",
                "This run does not estimate accuracy, precision, or corpus-wide coverage.",
            ],
        }
        run_bytes = canonical_json(run_manifest)
        (output_dir / "RUN_MANIFEST.json").write_bytes(run_bytes)
        (output_dir / "RUN_MANIFEST.sha256").write_text(
            f"{sha256_bytes(run_bytes)} *RUN_MANIFEST.json\n", encoding="ascii"
        )
    except Exception:
        # Leave a failed directory in place as evidence; never erase or replace it.
        raise
    return run_manifest


def default_input_paths() -> dict[str, Path]:
    return {key: PILOT_DIR / filename for key, filename in INPUT_FILES.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    inputs = default_input_paths()
    try:
        manifest = run_pipeline(inputs, args.registry, args.output_dir)
    except (OSError, PreflightError, ValueError) as exc:
        print(f"Annotation Automation v1 stopped: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(manifest["counts"], ensure_ascii=False, sort_keys=True, indent=2))
    print(f"Output: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
