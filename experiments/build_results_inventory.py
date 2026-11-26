#!/usr/bin/env python3
"""Consolidate the saved v1.0-v1.3 model and paired-comparison outputs.

This script reads files under ``results/`` only. It does not import training
code, alter source results, or fit or score a model.
"""

import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
OUTPUT_DIR = RESULTS_DIR / "thesis_consolidation_v1"
VERSION_RE = re.compile(r"v1[_\.]([0-3])", re.IGNORECASE)
NEURAL_MODEL_RE = re.compile(r"MLP|GCN|GNN", re.IGNORECASE)

INVENTORY_COLUMNS = [
    "version",
    "model_name",
    "status",
    "n_seeds",
    "val_macro_f1",
    "test_r2_12_macro_f1",
    "test_12rank_macro_f1",
    "test_3tier_macro_f1",
    "test_3tier_acc",
    "test_qwk",
    "validation_selected",
    "validation_selection_metric",
    "validation_selected_score",
    "source_file",
]

BOOTSTRAP_COLUMNS = [
    "version",
    "comparison",
    "metric",
    "delta",
    "ci_low",
    "ci_high",
    "p_raw",
    "p_holm",
    "significant_raw (p<0.05)",
    "significant_holm (p_holm<0.05)",
]

METRIC_NAMES = ("Macro-F1", "Accuracy", "QWK")
METRIC_ORDER = {name: index for index, name in enumerate(METRIC_NAMES)}


def version_from_name(name: str) -> Optional[str]:
    match = VERSION_RE.search(name)
    if not match:
        return None
    return "v1." + match.group(1)


def version_sort_key(version: str) -> Tuple[int, int]:
    return tuple(int(part) for part in version[1:].split("."))


def discover_version_dirs() -> List[Tuple[str, Path]]:
    found = []
    for path in RESULTS_DIR.iterdir():
        if not path.is_dir():
            continue
        version = version_from_name(path.name)
        if version:
            found.append((version, path))
    return sorted(found, key=lambda item: (version_sort_key(item[0]), item[1].name))


def relative_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def parse_number(value: object) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"na", "nan", "none", "null", "n/a"}:
        return None
    number = float(text.replace(",", ""))
    if not math.isfinite(number):
        return None
    return number


def first_number(row: Dict[str, object], aliases: Iterable[str]) -> Optional[float]:
    for alias in aliases:
        if alias in row:
            value = parse_number(row[alias])
            if value is not None:
                return value
    return None


def ensure_eval(
    evaluations: Dict[Tuple[str, str], dict], version: str, model_name: str
) -> dict:
    key = (version, model_name)
    if key not in evaluations:
        evaluations[key] = {
            "version": version,
            "model_name": model_name,
            "n_seeds": infer_n_seeds(version, model_name),
            "_val_r2_12": None,
            "_val_12rank": None,
            "_test_r2_12": None,
            "_test_12rank": None,
            "_test_3tier_macro": None,
            "_test_3tier_acc": None,
            "_test_qwk": None,
            "_test_present": False,
            "_rank_f1": {},
            "_source_files": set(),
        }
    return evaluations[key]


def infer_n_seeds(version: str, model_name: str) -> int:
    """Use the seed protocol stated in the saved version results.

    v1.0 and v1.1 report one deterministic text-baseline run and five neural
    seeds. The v1.2 and v1.3 result summaries identify their tables as five-seed
    means, including deterministic baselines represented across that protocol.
    """
    if version in {"v1.0", "v1.1"}:
        return 5 if NEURAL_MODEL_RE.search(model_name) else 1
    return 5


def set_metric(record: dict, field: str, value: Optional[float], source: str, errors: List[str]) -> None:
    if value is None:
        return
    old = record.get(field)
    if old is not None and not math.isclose(old, value, rel_tol=1e-7, abs_tol=1e-8):
        errors.append(
            "Conflicting values for "
            f"{record['version']} {record['model_name']} {field}: "
            f"{old} vs {value} in {source}"
        )
        return
    record[field] = value


def read_csv_rows(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")
        return list(reader.fieldnames), list(reader)


def collect_model_comparisons(
    version_dirs: Sequence[Tuple[str, Path]],
    evaluations: Dict[Tuple[str, str], dict],
    errors: List[str],
) -> Dict[str, bool]:
    version_has_val_r2_12: Dict[str, bool] = defaultdict(bool)

    for version, folder in version_dirs:
        files = sorted(folder.rglob("MODEL_COMPARISON_*.csv"))
        for path in files:
            source = relative_path(path)
            try:
                headers, rows = read_csv_rows(path)
            except Exception as exc:
                errors.append(f"{source}: could not parse model-comparison CSV ({exc})")
                continue

            val_r2_aliases = (
                "val_r2_12_macro_f1",
                "val_r2_12_f1",
                "val_rank2_12_macro_f1",
            )
            if any(alias in headers for alias in val_r2_aliases):
                version_has_val_r2_12[version] = True

            for row_number, row in enumerate(rows, start=2):
                model_name = (row.get("model_name") or row.get("model") or "").strip()
                if not model_name:
                    errors.append(f"{source}:{row_number}: missing model_name")
                    continue
                record = ensure_eval(evaluations, version, model_name)
                record["_source_files"].add(source)

                try:
                    set_metric(
                        record,
                        "_val_r2_12",
                        first_number(row, val_r2_aliases),
                        source,
                        errors,
                    )
                    set_metric(
                        record,
                        "_val_12rank",
                        first_number(row, ("val_12rank_macro_f1", "val_12_rank_macro_f1", "val_macro_f1")),
                        source,
                        errors,
                    )
                    set_metric(
                        record,
                        "_test_r2_12",
                        first_number(
                            row,
                            ("test_r2_12_macro_f1", "test_rank2_12_macro_f1", "test_r2_12_f1"),
                        ),
                        source,
                        errors,
                    )
                    set_metric(
                        record,
                        "_test_12rank",
                        first_number(
                            row,
                            ("test_12rank_macro_f1", "test_12_rank_macro_f1", "test_macro_f1"),
                        ),
                        source,
                        errors,
                    )
                    set_metric(
                        record,
                        "_test_3tier_macro",
                        first_number(
                            row,
                            ("test_3tier_macro_f1", "test_tier3_macro_f1", "test_macro_f1_3tier"),
                        ),
                        source,
                        errors,
                    )
                    set_metric(
                        record,
                        "_test_3tier_acc",
                        first_number(
                            row,
                            ("test_3tier_acc", "test_tier3_acc", "test_tier3_accuracy"),
                        ),
                        source,
                        errors,
                    )
                    set_metric(
                        record,
                        "_test_qwk",
                        first_number(row, ("test_qwk", "test_quadratic_weighted_kappa")),
                        source,
                        errors,
                    )
                except (TypeError, ValueError) as exc:
                    errors.append(f"{source}:{row_number}: invalid numeric value ({exc})")
                    continue

                if any(
                    record.get(field) is not None
                    for field in (
                        "_test_r2_12",
                        "_test_12rank",
                        "_test_3tier_macro",
                        "_test_3tier_acc",
                        "_test_qwk",
                    )
                ):
                    record["_test_present"] = True

    return version_has_val_r2_12


def collect_per_rank_metrics(
    version_dirs: Sequence[Tuple[str, Path]],
    evaluations: Dict[Tuple[str, str], dict],
    errors: List[str],
) -> None:
    for version, folder in version_dirs:
        for path in sorted(folder.rglob("PER_RANK_METRICS_*.csv")):
            source = relative_path(path)
            try:
                _, rows = read_csv_rows(path)
            except Exception as exc:
                errors.append(f"{source}: could not parse per-rank CSV ({exc})")
                continue

            for row_number, row in enumerate(rows, start=2):
                model_name = (row.get("model_name") or row.get("model") or "").strip()
                rank_value = row.get("rank_1_to_12") or row.get("rank")
                if not model_name or not rank_value:
                    errors.append(f"{source}:{row_number}: missing model_name or rank")
                    continue
                try:
                    rank = int(float(rank_value))
                    if not 1 <= rank <= 12:
                        raise ValueError("rank must be between 1 and 12")
                    f1 = first_number(row, ("f1_5seed_mean", "f1", "macro_f1"))
                except (TypeError, ValueError) as exc:
                    errors.append(f"{source}:{row_number}: invalid per-rank row ({exc})")
                    continue
                if f1 is None:
                    errors.append(f"{source}:{row_number}: missing F1 value")
                    continue

                record = ensure_eval(evaluations, version, model_name)
                record["_source_files"].add(source)
                rank_scores = record["_rank_f1"]
                if rank in rank_scores and not math.isclose(
                    rank_scores[rank], f1, rel_tol=1e-7, abs_tol=1e-8
                ):
                    errors.append(
                        f"{source}:{row_number}: conflicting rank {rank} F1 "
                        f"for {model_name}"
                    )
                    continue
                rank_scores[rank] = f1
                record["_test_present"] = True


def complete_from_rank_scores(evaluations: Dict[Tuple[str, str], dict]) -> None:
    for record in evaluations.values():
        ranks = record["_rank_f1"]
        if all(rank in ranks for rank in range(1, 13)):
            record["_test_12rank"] = record["_test_12rank"] or sum(
                ranks[rank] for rank in range(1, 13)
            ) / 12.0
        if all(rank in ranks for rank in range(2, 13)):
            record["_test_r2_12"] = record["_test_r2_12"] or sum(
                ranks[rank] for rank in range(2, 13)
            ) / 11.0


def select_validation_models(
    evaluations: Dict[Tuple[str, str], dict],
    version_has_val_r2_12: Dict[str, bool],
) -> Tuple[Dict[str, Tuple[str, str]], Dict[str, str]]:
    selected: Dict[str, Tuple[str, str]] = {}
    metric_by_version: Dict[str, str] = {}
    versions = sorted({version for version, _ in evaluations}, key=version_sort_key)

    for version in versions:
        use_r2_12 = bool(version_has_val_r2_12.get(version, False))
        metric_by_version[version] = (
            "val_r2_12_macro_f1" if use_r2_12 else "val_12rank_macro_f1"
        )
        value_key = "_val_r2_12" if use_r2_12 else "_val_12rank"
        candidates = [
            (key, record)
            for key, record in evaluations.items()
            if key[0] == version and record.get(value_key) is not None
        ]
        if candidates:
            best_key, _ = max(candidates, key=lambda item: item[1][value_key])
            selected[version] = best_key
    return selected, metric_by_version


def inventory_rows(
    evaluations: Dict[Tuple[str, str], dict],
    selected: Dict[str, Tuple[str, str]],
    metric_by_version: Dict[str, str],
) -> List[dict]:
    rows = []
    for key, record in sorted(
        evaluations.items(), key=lambda item: (version_sort_key(item[0][0]), item[0][1])
    ):
        if not record["_test_present"]:
            continue
        version, model_name = key
        selected_this = selected.get(version) == key
        status = "superseded_leak" if version == "v1.0" else (
            "canonical" if selected_this else "exploratory"
        )
        value_key = "_val_r2_12" if metric_by_version.get(version) == "val_r2_12_macro_f1" else "_val_12rank"
        sources = sorted(record["_source_files"])
        rows.append(
            {
                "version": version,
                "model_name": model_name,
                "status": status,
                "n_seeds": record["n_seeds"],
                "val_macro_f1": record.get("_val_12rank"),
                "test_r2_12_macro_f1": record.get("_test_r2_12"),
                "test_12rank_macro_f1": record.get("_test_12rank"),
                "test_3tier_macro_f1": record.get("_test_3tier_macro"),
                "test_3tier_acc": record.get("_test_3tier_acc"),
                "test_qwk": record.get("_test_qwk"),
                "validation_selected": selected_this,
                "validation_selection_metric": metric_by_version.get(version, ""),
                "validation_selected_score": record.get(value_key) if selected_this else None,
                "source_file": ";".join(sources),
            }
        )
    return rows


def parse_ci(text: str) -> Tuple[Optional[float], Optional[float]]:
    match = re.search(r"\[\s*([^,]+?)\s*,\s*([^\]]+?)\s*\]", text)
    if not match:
        return None, None
    return parse_number(match.group(1)), parse_number(match.group(2))


def add_comparison(
    comparisons: Dict[Tuple[str, str, str, str], dict],
    version: str,
    family: str,
    comparison: str,
    metric: str,
    delta: Optional[float],
    ci_low: Optional[float],
    ci_high: Optional[float],
    p_raw: Optional[float],
    source: str,
    priority: int,
) -> None:
    comparison = comparison.strip().strip("`")
    key = (version, family, comparison, metric)
    record = comparisons.setdefault(
        key,
        {
            "version": version,
            "family": family,
            "comparison_raw": comparison,
            "metric": metric,
            "delta": None,
            "ci_low": None,
            "ci_high": None,
            "p_raw": None,
            "_priorities": {},
            "_sources": set(),
        },
    )
    record["_sources"].add(source)
    for field, value in (
        ("delta", delta),
        ("ci_low", ci_low),
        ("ci_high", ci_high),
        ("p_raw", p_raw),
    ):
        if value is None:
            continue
        old_priority = record["_priorities"].get(field, -1)
        if record[field] is None or priority >= old_priority:
            record[field] = value
            record["_priorities"][field] = priority


def parse_markdown_bullets(
    text: str, version: str, family: str, source: str, comparisons: Dict[Tuple[str, str, str, str], dict]
) -> int:
    parsed = 0
    for line in text.splitlines():
        bullet = re.match(r"\s*-\s*\*\*(.+?):\*\*(.*)$", line)
        if not bullet:
            continue
        comparison, details = bullet.group(1).strip(), bullet.group(2)

        macro = re.search(r"delta\s+Macro-F1\s*=\s*`([^`]+)`", details, re.IGNORECASE)
        macro_p = None
        ci_low = ci_high = None
        if macro:
            ci_match = re.search(
                r"95%\s*CI\s*`(\[[^`]+\])`\s*,\s*p=`([^`]+)`",
                details,
                re.IGNORECASE,
            )
            if ci_match:
                ci_low, ci_high = parse_ci(ci_match.group(1))
                macro_p = parse_number(ci_match.group(2))
            else:
                after_delta = details[macro.end() :]
                p_match = re.search(r"\bp=`([^`]+)`", after_delta, re.IGNORECASE)
                if p_match:
                    macro_p = parse_number(p_match.group(1))
            add_comparison(
                comparisons,
                version,
                family,
                comparison,
                "Macro-F1",
                parse_number(macro.group(1)),
                ci_low,
                ci_high,
                macro_p,
                source,
                1,
            )
            parsed += 1

        for metric, label in (("Accuracy", "Acc"), ("QWK", "QWK")):
            match = re.search(
                rf"delta\s+{label}\s*=\s*`([^`]+)`\s*\(p=`([^`]+)`\)",
                details,
                re.IGNORECASE,
            )
            if match:
                add_comparison(
                    comparisons,
                    version,
                    family,
                    comparison,
                    metric,
                    parse_number(match.group(1)),
                    None,
                    None,
                    parse_number(match.group(2)),
                    source,
                    1,
                )
                parsed += 1
    return parsed


def parse_markdown_comparison_tables(
    text: str, version: str, family: str, source: str, comparisons: Dict[Tuple[str, str, str, str], dict]
) -> int:
    lines = text.splitlines()
    parsed = 0
    index = 0
    while index < len(lines):
        line = lines[index]
        if "Mean Delta Macro-F1" not in line or "p (F1)" not in line:
            index += 1
            continue
        index += 1
        if index < len(lines) and lines[index].lstrip().startswith("|"):
            index += 1  # Header separator.
        while index < len(lines) and lines[index].lstrip().startswith("|"):
            cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
            if len(cells) >= 8 and not all(set(cell) <= {"-", ":", " "} for cell in cells):
                comparison = cells[0].strip().strip("`")
                ci_low, ci_high = parse_ci(cells[2])
                values = (
                    ("Macro-F1", cells[1], ci_low, ci_high, cells[3]),
                    ("Accuracy", cells[4], None, None, cells[5]),
                    ("QWK", cells[6], None, None, cells[7]),
                )
                for metric, delta_text, low, high, p_text in values:
                    add_comparison(
                        comparisons,
                        version,
                        family,
                        comparison,
                        metric,
                        parse_number(delta_text.strip("`")),
                        low,
                        high,
                        parse_number(p_text.strip("`")),
                        source,
                        1,
                    )
                    parsed += 1
            index += 1
        continue
    return parsed


def parse_markdown_file(
    path: Path,
    version: str,
    comparisons: Dict[Tuple[str, str, str, str], dict],
    errors: List[str],
) -> None:
    source = relative_path(path)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        errors.append(f"{source}: could not read comparison Markdown ({exc})")
        return
    if not re.search(r"paired\s+bootstrap|bootstrap\s+comparisons?|bootstrap\s+tests", text, re.I):
        return
    family = path.parent.relative_to(RESULTS_DIR).as_posix()
    count = parse_markdown_bullets(text, version, family, source, comparisons)
    count += parse_markdown_comparison_tables(text, version, family, source, comparisons)
    if count == 0:
        errors.append(f"{source}: bootstrap section found but no comparison rows were recognized")


def json_number(metrics: dict, aliases: Sequence[str]) -> Optional[float]:
    for alias in aliases:
        if alias in metrics:
            return parse_number(metrics[alias])
    return None


def json_ci(metrics: dict, aliases: Sequence[str]) -> Tuple[Optional[float], Optional[float]]:
    for alias in aliases:
        value = metrics.get(alias)
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return parse_number(value[0]), parse_number(value[1])
    return None, None


def parse_json_comparison_file(
    path: Path,
    version: str,
    comparisons: Dict[Tuple[str, str, str, str], dict],
    errors: List[str],
) -> None:
    source = relative_path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        if re.search(r"bootstrap|comparison|metrics|diagnostic|audit", path.name, re.I):
            errors.append(f"{source}: could not parse comparison JSON ({exc})")
        return
    if not isinstance(payload, dict):
        return

    section_name = None
    for candidate in ("paired_bootstrap", "comparisons_5seed"):
        if isinstance(payload.get(candidate), dict):
            section_name = candidate
            break
    if section_name is None:
        return

    family = path.parent.relative_to(RESULTS_DIR).as_posix()
    section = payload[section_name]
    recognized = 0
    for comparison, metrics in section.items():
        if not isinstance(metrics, dict):
            continue
        metric_specs = (
            (
                "Macro-F1",
                ("delta_macro_f1", "mean_delta_macro_f1", "delta_f1", "mean_delta_f1"),
                ("p_f1", "p_delta_f1", "p_macro_f1"),
                ("ci_low_macro_f1", "macro_f1_ci_low", "ci_low_f1"),
                ("ci_high_macro_f1", "macro_f1_ci_high", "ci_high_f1"),
            ),
            (
                "Accuracy",
                ("delta_acc", "mean_delta_acc", "delta_accuracy", "mean_delta_accuracy"),
                ("p_acc", "p_delta_acc", "p_accuracy"),
                ("ci_low_acc", "accuracy_ci_low"),
                ("ci_high_acc", "accuracy_ci_high"),
            ),
            (
                "QWK",
                ("delta_qwk", "mean_delta_qwk"),
                ("p_qwk", "p_delta_qwk"),
                ("ci_low_qwk", "qwk_ci_low"),
                ("ci_high_qwk", "qwk_ci_high"),
            ),
        )
        for metric, delta_aliases, p_aliases, low_aliases, high_aliases in metric_specs:
            delta = json_number(metrics, delta_aliases)
            p_raw = json_number(metrics, p_aliases)
            if delta is None and p_raw is None:
                continue
            ci_low = json_number(metrics, low_aliases)
            ci_high = json_number(metrics, high_aliases)
            if metric == "Macro-F1" and (ci_low is None or ci_high is None):
                array_low, array_high = json_ci(
                    metrics,
                    ("ci95_delta_f1", "ci95_f1", "ci95_macro_f1", "ci95_delta_macro_f1"),
                )
                ci_low = ci_low if ci_low is not None else array_low
                ci_high = ci_high if ci_high is not None else array_high
            add_comparison(
                comparisons,
                version,
                family,
                str(comparison),
                metric,
                delta,
                ci_low,
                ci_high,
                p_raw,
                source,
                2,
            )
            recognized += 1
    if not recognized:
        errors.append(f"{source}: {section_name} found but contained no recognized comparison metrics")


def collect_bootstrap_comparisons(
    version_dirs: Sequence[Tuple[str, Path]], errors: List[str]
) -> List[dict]:
    comparisons: Dict[Tuple[str, str, str, str], dict] = {}
    for version, folder in version_dirs:
        for path in sorted(folder.rglob("*.md")):
            parse_markdown_file(path, version, comparisons, errors)
        for path in sorted(folder.rglob("*.json")):
            if path.name.lower().startswith("manifest"):
                continue
            parse_json_comparison_file(path, version, comparisons, errors)

    macro_families: Dict[Tuple[str, str], List[dict]] = defaultdict(list)
    for record in comparisons.values():
        if record["metric"] == "Macro-F1" and record["p_raw"] is not None:
            macro_families[(record["version"], record["family"])].append(record)

    for family_records in macro_families.values():
        adjusted = holm_adjust([record["p_raw"] for record in family_records])
        for record, p_holm in zip(family_records, adjusted):
            record["p_holm"] = p_holm
            record["significant_holm"] = p_holm < 0.05

    rows = []
    for record in sorted(
        comparisons.values(),
        key=lambda item: (
            version_sort_key(item["version"]),
            item["family"],
            item["comparison_raw"],
            METRIC_ORDER[item["metric"]],
        ),
    ):
        family_name = Path(record["family"]).name
        rows.append(
            {
                "version": record["version"],
                "comparison": f"{family_name} :: {record['comparison_raw']}",
                "metric": record["metric"],
                "delta": record["delta"],
                "ci_low": record["ci_low"],
                "ci_high": record["ci_high"],
                "p_raw": record["p_raw"],
                "p_holm": record.get("p_holm"),
                "significant_raw (p<0.05)": (
                    record["p_raw"] < 0.05 if record["p_raw"] is not None else None
                ),
                "significant_holm (p_holm<0.05)": record.get("significant_holm"),
                "_family": record["family"],
                "_comparison_raw": record["comparison_raw"],
            }
        )
    return rows


def holm_adjust(p_values: Sequence[float]) -> List[float]:
    """Return Holm step-down adjusted p-values in their original order."""
    values = [float(value) for value in p_values]
    if any(not math.isfinite(value) or value < 0.0 or value > 1.0 for value in values):
        raise ValueError("p-values must be finite numbers between 0 and 1")
    count = len(values)
    if count == 0:
        return []

    ordered = sorted(enumerate(values), key=lambda item: (item[1], item[0]))
    adjusted = [0.0] * count
    running_max = 0.0
    for rank, (original_index, p_value) in enumerate(ordered):
        step_value = min(1.0, (count - rank) * p_value)
        running_max = max(running_max, step_value)
        adjusted[original_index] = running_max
    return adjusted


def csv_number(value: Optional[float]) -> str:
    if value is None:
        return ""
    return format(value, ".10g")


def write_csv(path: Path, columns: Sequence[str], rows: Sequence[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            clean = {}
            for column in columns:
                value = row.get(column)
                if isinstance(value, float):
                    clean[column] = csv_number(value)
                elif value is None:
                    clean[column] = ""
                else:
                    clean[column] = value
            writer.writerow(clean)


def comparison_family_summary(rows: Sequence[dict]) -> List[dict]:
    families: Dict[Tuple[str, str], List[dict]] = defaultdict(list)
    for row in rows:
        if row["metric"] == "Macro-F1" and row.get("p_raw") is not None:
            families[(row["version"], row["_family"])].append(row)
    return [
        {
            "version": version,
            "family": family,
            "records": records,
            "significant": [row for row in records if row.get("significant_holm (p_holm<0.05)") is True],
            "not_significant": [row for row in records if row.get("significant_holm (p_holm<0.05)") is False],
            "raw_only": [
                row
                for row in records
                if row.get("significant_raw (p<0.05)") is True
                and row.get("significant_holm (p_holm<0.05)") is False
            ],
        }
        for (version, family), records in sorted(
            families.items(), key=lambda item: (version_sort_key(item[0][0]), item[0][1])
        )
    ]


def report_text(
    inventory: Sequence[dict],
    bootstrap_rows: Sequence[dict],
    selected: Dict[str, Tuple[str, str]],
    metric_by_version: Dict[str, str],
    errors: Sequence[str],
) -> str:
    counts: Dict[str, int] = defaultdict(int)
    for row in inventory:
        counts[row["version"]] += 1

    lines = [
        "# Results consolidation — Brief 1",
        "",
        "The inventory counts distinct version/model rows with saved test metrics. `n_seeds` follows each result set’s stated seed protocol. No model was trained, rerun, or rescored.",
        "",
        "Primary thesis metric: test R2-12 Macro-F1 (Ranks 2-12). Rank 1 is Companion status, not a reliability grade. The 12-rank, 3-tier, accuracy, and QWK values are also retained in the inventory. Validation selection uses R2-12 Macro-F1 when present; the saved comparison files have no validation R2-12 column, so all four versions use the 12-rank `val_macro_f1` fallback.",
        "",
        "## Test-set inventory and validation selection",
        "",
    ]

    for version in sorted(counts, key=version_sort_key):
        selected_key = selected.get(version)
        selected_row = next(
            (
                row
                for row in inventory
                if selected_key == (row["version"], row["model_name"])
            ),
            None,
        )
        if selected_row:
            val_score = csv_number(selected_row["val_macro_f1"])
            r2_score = csv_number(selected_row["test_r2_12_macro_f1"])
            selection_metric = metric_by_version.get(version, "val_12rank_macro_f1")
            lines.append(
                f"- **{version}:** {counts[version]} distinct model evaluations. Validation selected `{selected_row['model_name']}` using `{selection_metric}` ({val_score}); its test R2-12 Macro-F1 is {r2_score}."
            )
        else:
            lines.append(f"- **{version}:** {counts[version]} distinct model evaluations; no validation score was available to select a model.")
    lines.extend(
        [
            "",
            "All v1.0 rows are marked `superseded_leak` as directed. Its validation-selected row is still recorded but is not treated as canonical.",
            "",
            "## Paired-bootstrap Macro-F1 comparisons",
            "",
            "Holm correction was applied separately to all Macro-F1 comparisons in each source report. Accuracy and QWK rows remain in `BOOTSTRAP_HOLM.csv` with raw p-values; they are outside the specified Holm family. The CSV marks every Macro-F1 comparison that did not survive correction as `False`.",
            "",
        ]
    )

    family_summaries = comparison_family_summary(bootstrap_rows)
    if not family_summaries:
        lines.append("No paired-bootstrap Macro-F1 comparisons were found in the targeted result folders.")
    else:
        for family in family_summaries:
            significant = family["significant"]
            label = Path(family["family"]).name
            if significant:
                names = "; ".join(row["_comparison_raw"] for row in significant)
                lines.append(
                    f"- **{family['version']} / {label}:** {len(significant)}/{len(family['records'])} remained significant: {names}. The other {len(family['not_significant'])} did not."
                )
            else:
                lines.append(
                    f"- **{family['version']} / {label}:** 0/{len(family['records'])} remained significant; all {len(family['not_significant'])} did not."
                )
            for row in family["raw_only"]:
                lines.append(
                    f"  - Raw-significant but not Holm-significant: `{row['_comparison_raw']}` (p={csv_number(row['p_raw'])}, adjusted p={csv_number(row['p_holm'])})."
                )

    lines.extend(["", "## Parsing", ""])
    if errors:
        lines.append("Files or rows that could not be parsed:")
        for error in errors:
            lines.append(f"- {error}")
    else:
        lines.append("All targeted model-comparison CSVs, per-rank CSVs, and paired-comparison JSON/Markdown files parsed; no file failures were recorded.")
    lines.append("")
    return "\n".join(lines)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_manifest() -> None:
    paths = [
        ROOT / "experiments" / "build_results_inventory.py",
        ROOT / "experiments" / "test_holm.py",
        OUTPUT_DIR / "TEST_SET_USAGE_INVENTORY.csv",
        OUTPUT_DIR / "BOOTSTRAP_HOLM.csv",
        OUTPUT_DIR / "REPORT.md",
    ]
    lines = [f"{sha256(path)}  {relative_path(path)}" for path in paths if path.is_file()]
    (OUTPUT_DIR / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    errors: List[str] = []
    version_dirs = discover_version_dirs()
    evaluations: Dict[Tuple[str, str], dict] = {}
    version_has_val_r2_12 = collect_model_comparisons(version_dirs, evaluations, errors)
    collect_per_rank_metrics(version_dirs, evaluations, errors)
    complete_from_rank_scores(evaluations)
    selected, metric_by_version = select_validation_models(evaluations, version_has_val_r2_12)
    inventory = inventory_rows(evaluations, selected, metric_by_version)
    bootstrap_rows = collect_bootstrap_comparisons(version_dirs, errors)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT_DIR / "TEST_SET_USAGE_INVENTORY.csv", INVENTORY_COLUMNS, inventory)
    write_csv(OUTPUT_DIR / "BOOTSTRAP_HOLM.csv", BOOTSTRAP_COLUMNS, bootstrap_rows)
    (OUTPUT_DIR / "REPORT.md").write_text(
        report_text(inventory, bootstrap_rows, selected, metric_by_version, errors),
        encoding="utf-8",
    )
    write_manifest()

    per_version: Dict[str, int] = defaultdict(int)
    for row in inventory:
        per_version[row["version"]] += 1
    print(f"Distinct test evaluations: {len(inventory)}")
    for version in sorted(per_version, key=version_sort_key):
        print(f"{version}: {per_version[version]}")
    if errors:
        print(f"Parse issues recorded in REPORT.md: {len(errors)}")
    else:
        print("Parse issues: 0")


if __name__ == "__main__":
    main()
