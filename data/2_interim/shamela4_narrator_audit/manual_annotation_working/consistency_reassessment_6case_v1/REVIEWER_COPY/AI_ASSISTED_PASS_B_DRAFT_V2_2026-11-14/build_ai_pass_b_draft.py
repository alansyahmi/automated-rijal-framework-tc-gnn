from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import date
from pathlib import Path


REPO = Path(__file__).resolve().parents[7]
PACKAGE = REPO / "data/2_interim/shamela4_narrator_audit/manual_annotation_working/consistency_reassessment_6case_v1"
REVIEWER = PACKAGE / "REVIEWER_COPY"
PASS_B = REVIEWER / "02_PASS_B_OPEN_AFTER_PASS_A_FREEZE"
OUT = REVIEWER / "AI_ASSISTED_PASS_B_DRAFT_V2_2026-11-14"
SCHEMA = REPO / "dataset_discovery/target_feasibility/MANUAL_COLLATION_SCHEMA_V2_2_FINAL.md"
PROTOCOL = REPO / "data/2_interim/shamela4_narrator_audit/manual_annotation_working/PILOT_EVALUATION_AND_ANNOTATION_PROTOCOL_V1.md"
HADITHDB = REPO / "data/1_raw/hadithdb/narrators_db.json"
SHAMELA_NARRATORS = REPO / "data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet"
TAQRIB_DIR = REPO / "data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/3076__تقريب-التهذيب"
TAQRIB_PAGES = TAQRIB_DIR / "pages.jsonl"
TAQRIB_META = TAQRIB_DIR / "book_metadata.json"
ALIFTA_URL = "https://sunna.alifta.gov.sa/BookToc/ViewServicePage?bookId=51&mainId=506655"

if OUT.exists() and any(path.name != Path(__file__).name for path in OUT.iterdir()):
    raise FileExistsError(f"Refusing to overwrite existing AI draft outputs in: {OUT}")
OUT.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def write_csv(name: str, template_name: str, rows: list[dict[str, str]]) -> None:
    headers, _ = read_csv(PASS_B / template_name)
    path = OUT / name
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers, extrasaction="raise", lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def make_row(headers: list[str], values: dict[str, str]) -> dict[str, str]:
    return {key: str(values.get(key, "")) for key in headers}


def arabic_digits(number: str) -> str:
    return str(number).translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))


with (PASS_B / "PASS_B_CASES.csv").open("r", encoding="utf-8-sig", newline="") as stream:
    cases = {row["repeat_case_id"]: row for row in csv.DictReader(stream)}

with (PASS_B / "PASS_B_CANDIDATES.csv").open("r", encoding="utf-8-sig", newline="") as stream:
    candidates = {(row["repeat_case_id"], row["candidate_key"]): row for row in csv.DictReader(stream)}

with (TAQRIB_PAGES).open("r", encoding="utf-8") as stream:
    page_rows = [json.loads(line) for line in stream]

with TAQRIB_META.open("r", encoding="utf-8") as stream:
    taqrib_metadata = json.load(stream)

metadata_text = taqrib_metadata["betaka_text"]
metadata_excerpt = (
    "المحقق: محمد عوامة\rالناشر: دار الرشيد - سوريا\r"
    "الطبعة: الأولى، ١٤٠٦ - ١٩٨٦\rعدد الصفحات: ٧٦٥\r"
    "[ترقيم الكتاب موافق للمطبوع]\r"
    "اعتمدنا على: نسخة محمد عوَّامة طبعة دار الرشيد بحلب الطبعة: الأولى ١٤٠٦هـ\r"
    "أرفقنا الفروقات التي بينها وبين طبعة: أبي الأشبال الباكستاني طبعة دار العاصمة الطبعة الأولى ١٤١٦هـ وذلك بوضعها بين معكوفتين هكذا [] ."
)
assert metadata_excerpt in metadata_text, "Expected edition metadata excerpt was not found verbatim."

case_sources: dict[str, dict[str, str]] = {}
for (case_id, candidate_key), candidate in candidates.items():
    entry_number = candidate["source_entry_number_from_text"]
    entry_text = candidate["taqrib_entry_text_verbatim"]
    page_match = None
    for page in page_rows:
        pattern = rf"(?<![٠-٩]){arabic_digits(entry_number)}\s*-"
        if re.search(pattern, page.get("body", "")) and entry_text in page.get("body", ""):
            page_match = page
            break
    assert page_match is not None, f"Could not verify Taqrib entry {entry_number} in local pages.jsonl."
    case_sources[f"{case_id}|{candidate_key}"] = {
        "page_num": str(page_match["page_num"]),
        "sequence_num": str(page_match["sequence_num"]),
        "page_id": str(page_match["page_id"]),
        "entry_number": entry_number,
        "entry_text": entry_text,
        "locator": (
            f"Taqrib, local corpus book_id 3076, page_num {page_match['page_num']}, "
            f"sequence_num {page_match['sequence_num']}, entry {entry_number} (page_id {page_match['page_id']})"
        ),
        "source_record_id": f"SRC-{case_id}-{candidate_key}-TAQRIB",
    }


RANK_RULES = {
    "rank_1": "فأما المراتب :\nفأولها : الصحابة , فأصرح بذلك لشرفهم .",
    "rank_2": "الثانية : من أكد مدحه ـ إما بأفعل ؛ كأوثق الناس، أو بتكرير الصفة لفظاً ؛ كثقة ثقة، أو معنى ؛ كثقة حافظ .",
    "rank_3": "الثالثة : من أفرد بصفة ؛ كثقة , أو متقن، أو ثَبْت، أو عدل .",
    "rank_6": "السادسة : من ليس له من الحديث إلا القليل، ولم يثبت فيه ما يترك حديثه من أجله، وإليه الإشارة بلفظ : مقبول، حيث يتابع، وإلا فلين الحديث .",
}


SPECS = [
    dict(case="RPT-01", cand="CAND-01", n=1,
         text="ثقة ثبت فاضل إلا أن في روايته عن ثابت والأعمش [وعاصم بن أبي النجود] وهشام ابن عروة شيئا وكذا فيما حدث به بالبصرة",
         kind="qualified_narrator_grade", base="ثقة ثبت فاضل",
         qual="إلا أن في روايته عن ثابت والأعمش [وعاصم بن أبي النجود] وهشام ابن عروة شيئا وكذا فيما حدث به بالبصرة",
         rank_status="unresolved",
         target="unresolved", target_note="Candidate for the proposed ordinary narrator-grade task, but passage-level authorship/compiler synthesis and historical provenance are unresolved. No target-task manifest is frozen.",
         hist="not_assessed", note="No numeric rank is assigned to this compound phrase in this draft. It remains unresolved rather than being forced into a category by analogy; the 12-category Taqrib taxonomy is unchanged. The teacher/Basra qualification remains attached verbatim."),
    dict(case="RPT-01", cand="CAND-01", n=2, text="من كبار السابعة",
         kind="descriptive_or_generational_status", target="not_in_defined_task",
         target_note="Generation label, not a narrator-grade target.", hist="not_assessed",
         note="Generation classification only; do not treat السابعة as rank 7."),
    dict(case="RPT-01", cand="CAND-01", n=3, text="مات سنة أربع وخمسين",
         kind="biographical_or_factual_statement", target="not_in_defined_task",
         target_note="Death statement, not a narrator-grade target; retain year wording without normalizing the calendar.", hist="not_assessed",
         note="Preserve the source wording. No calendar conversion or reconciliation with other reported dates was performed."),
    dict(case="RPT-01", cand="CAND-01", n=4, text="وهو ابن ثمان وخمسين سنة",
         kind="biographical_or_factual_statement", target="not_in_defined_task",
         target_note="Age-at-death statement, not a narrator-grade target.", hist="not_assessed",
         note="Kept separate from the death-year statement."),

    dict(case="RPT-02", cand="CAND-01", n=1, text="وثقه النسائي",
         kind="attributed_earlier_critic_judgment", base="وثقه",
         rank_status="not_applicable", target="not_in_defined_task",
         target_note="The passage explicitly reports al-Nasa'i's judgement; this is not treated as Ibn Hajar's own ordinary-grade formulation.",
         hist="not_assessed", note="The quoted passage reports trustworthiness attributed to al-Nasa'i. It does not prove a direct quotation or traceable transmission route."),
    dict(case="RPT-02", cand="CAND-01", n=2, text="من الثالثة",
         kind="descriptive_or_generational_status", target="not_in_defined_task",
         target_note="Generation classification, not reliability rank 3.", hist="not_assessed",
         note="Do not confuse the generation number with the Taqrib reliability-rank taxonomy."),

    dict(case="RPT-03", cand="CAND-01", n=1, text="عابوا عليه أنه حدث عن أبيه بغير سماع",
         kind="specific_transmission_criticism", rank_status="not_applicable",
         target="not_in_defined_task", target_note="Specific transmission criticism, not a standardized general narrator grade.",
         hist="not_assessed", note="Collective critic identity and historical route remain unresolved; do not substitute related reports as the source of this collective wording."),
    dict(case="RPT-03", cand="CAND-01", n=2, text="من العاشرة",
         kind="descriptive_or_generational_status", target="not_in_defined_task",
         target_note="Generation classification, not reliability rank 10.", hist="not_assessed",
         note="Generation classification only."),

    dict(case="RPT-04", cand="CAND-01", n=1, text="صحابي",
         kind="descriptive_or_generational_status", rank=1, rank_status="assigned", rank_rule="rank_1",
         target="status_only_candidate", target_note="Taqrib's first taxonomy rank identifies Companions; this is status-only and never an ordinary reliability-grade target. No separate status-task version is approved.",
         hist="not_assessed", note="Rank 1 is recorded as Taqrib taxonomy/status, not an ordinary reliability score. The status claim is not used to support identity."),
    dict(case="RPT-04", cand="CAND-01", n=2, text="ابن صحابي",
         kind="biographical_or_factual_statement", target="not_in_defined_task",
         target_note="Parentage/relationship statement, not a narrator-grade target.", hist="not_assessed", note="Separate factual claim."),
    dict(case="RPT-04", cand="CAND-01", n=3, text="غزا تسع عشرة غزوة",
         kind="biographical_or_factual_statement", target="not_in_defined_task",
         target_note="Biographical statement, not a narrator-grade target.", hist="not_assessed", note="Kept separate from Companion status, parentage, death, and age."),
    dict(case="RPT-04", cand="CAND-01", n=4, text="ومات بالمدينة بعد السبعين",
         kind="biographical_or_factual_statement", target="not_in_defined_task",
         target_note="Death/location statement, not a narrator-grade target; wording is imprecise and not normalized.", hist="not_assessed", note="Preserves after-the-seventies wording without selecting a specific year."),
    dict(case="RPT-04", cand="CAND-01", n=5, text="وهو ابن أربع وتسعين",
         kind="biographical_or_factual_statement", target="not_in_defined_task",
         target_note="Age statement, not a narrator-grade target.", hist="not_assessed", note="Kept separate from death/location statement."),

    dict(case="RPT-05", cand="CAND-01", n=1, text="مقبول",
         kind="standardized_narrator_grade", base="مقبول", rank=6, rank_status="assigned", rank_rule="rank_6",
         target="not_in_defined_task", target_note="This is the grade in candidate entry 5570, not the original HadithDB field. The candidate-field comparison is not found, and the entry is a distinct homonym candidate.",
         hist="not_assessed", note="Rank 6 maps the exact Taqrib signal مقبول. This rank describes entry 5570 only; it must not be attached to HadithDB narrator ID 278."),
    dict(case="RPT-05", cand="CAND-01", n=2, text="من الثانية عشرة",
         kind="descriptive_or_generational_status", target="not_in_defined_task",
         target_note="Generation classification, not reliability rank 12.", hist="not_assessed", note="Generation field only."),
    dict(case="RPT-05", cand="CAND-01", n=3, text="مات سنة إحدى وثمانين",
         kind="biographical_or_factual_statement", target="not_in_defined_task",
         target_note="Death wording, not a narrator-grade target; do not infer or normalize the omitted century.", hist="not_assessed",
         note="Verbatim wording preserved; entry's generation context is not used to rewrite the date."),

    dict(case="RPT-05", cand="CAND-02", n=1, text="ثقة له أفراد",
         kind="qualified_narrator_grade", base="ثقة", qual="له أفراد", rank=3, rank_status="assigned", rank_rule="rank_3",
         target="unresolved", target_note="The field and entry text correspond; passage-level authorship/compiler synthesis is unresolved and the target-task manifest is not frozen.",
         hist="not_assessed", note="Rank 3 is based on the explicit single descriptor ثقة. Preserve له أفراد verbatim; no severity or impact is inferred from it."),
    dict(case="RPT-05", cand="CAND-02", n=2, text="من العاشرة",
         kind="descriptive_or_generational_status", target="not_in_defined_task",
         target_note="Generation classification, not reliability rank 10.", hist="not_assessed", note="Generation field only."),
    dict(case="RPT-05", cand="CAND-02", n=3, text="مات سنة سبع وعشرين",
         kind="biographical_or_factual_statement", target="not_in_defined_task",
         target_note="Death wording, not a narrator-grade target; do not expand to a century from another source.", hist="not_assessed",
         note="Verbatim wording preserved; no date normalization."),

    dict(case="RPT-06", cand="CAND-01", n=1, text="ثقة",
         kind="standardized_narrator_grade", base="ثقة", rank=3, rank_status="assigned", rank_rule="rank_3",
         target="unresolved", target_note="Passage and identity match are supported, but passage-level authorship/compiler synthesis is unresolved and the target-task manifest is not frozen.",
         hist="not_assessed", note="Rank 3 is based on the exact single descriptor ثقة. This taxonomy mapping does not establish attribution, historical provenance, or target eligibility."),
    dict(case="RPT-06", cand="CAND-01", n=2, text="يقال له رؤية",
         kind="biographical_or_factual_statement", target="not_in_defined_task",
         target_note="Reported biographical claim, not a narrator-grade target.", hist="not_assessed",
         note="Preserve يقال. It is a reported claim about ruʾyah and does not by itself establish Companion status."),
    dict(case="RPT-06", cand="CAND-01", n=3, text="مات سنة سبع أو ثمان وتسعين",
         kind="biographical_or_factual_statement", target="not_in_defined_task",
         target_note="Death-date statement, not a narrator-grade target; preserve both alternatives and do not normalize.", hist="not_assessed",
         note="Both alternative years remain verbatim; no selection or calendar conversion."),
]

for spec in SPECS:
    key = f"{spec['case']}|{spec['cand']}"
    assert (spec["case"], spec["cand"]) in candidates, f"Missing candidate input {key}"
    assert spec["text"] in candidates[(spec["case"], spec["cand"])]["taqrib_entry_text_verbatim"], (
        f"Statement span is not verbatim in source: {key}, {spec['text']}"
    )

statement_headers, _ = read_csv(PASS_B / "PASS_B_STATEMENT_DECISIONS_BLANK.csv")
candidate_headers, _ = read_csv(PASS_B / "PASS_B_CANDIDATE_DECISIONS_BLANK.csv")
attribution_headers, _ = read_csv(PASS_B / "PASS_B_ATTRIBUTION_DECISIONS_BLANK.csv")
evidence_headers, _ = read_csv(PASS_B / "PASS_B_SOURCE_EVIDENCE_DECISIONS_BLANK.csv")
metadata_headers, _ = read_csv(PASS_B / "PASS_B_SOURCE_METADATA_DECISIONS_BLANK.csv")

candidate_rows = []
for key, c in sorted(candidates.items()):
    case_id, cand_key = key
    original = cases[case_id]["original_grade_verbatim"]
    entry = c["taqrib_entry_text_verbatim"]
    source = case_sources[f"{case_id}|{cand_key}"]
    span_map = {
        ("RPT-01", "CAND-01"): ("minor_variation", "ثقة ثبت فاضل إلا أن في روايته عن ثابت والأعمش [وعاصم بن أبي النجود] وهشام ابن عروة شيئا وكذا فيما حدث به بالبصرة", "Transcribed assessment is lexically the same; original field differs in orthographic/punctuation presentation and omits the corpus's square-bracket variant markup. Brackets are retained, not normalized."),
        ("RPT-02", "CAND-01"): ("minor_variation", "وثقه النسائي", "Same wording; the original field inserts a colon after وثقه. Punctuation-only difference."),
        ("RPT-03", "CAND-01"): ("exact", "عابوا عليه أنه حدث عن أبيه بغير سماع", "Exact assessment span occurs in the entry; this establishes textual correspondence only."),
        ("RPT-04", "CAND-01"): ("exact", "صحابي", "Exact original field occurs as the first status phrase in the entry."),
        ("RPT-05", "CAND-01"): ("not_found", "", "Original field ثقة له أفراد is absent from candidate entry 5570, whose grade phrase is مقبول. The matching phrase is in the other packet candidate entry 5569; this draft does not re-key or alter Pass A."),
        ("RPT-05", "CAND-02"): ("exact", "ثقة له أفراد", "Exact original field occurs in candidate entry 5569. The submitted Pass A candidate keys appear crossed relative to the packet; see the separate erratum."),
        ("RPT-06", "CAND-01"): ("exact", "ثقة", "Exact original field occurs in the entry; no inference about historical origin follows."),
    }
    status, span, rationale = span_map[(case_id, cand_key)]
    assert (span in entry) if span else (original not in entry)
    candidate_rows.append(make_row(candidate_headers, {
        "repeat_case_id": case_id,
        "candidate_key": cand_key,
        "candidate_field_source_correspondence": status,
        "candidate_comparison_source_span": span,
        "candidate_comparison_source_span_status": "transcribed" if span else "not_found_after_review",
        "candidate_comparison_rationale": rationale,
        "candidate_comparison_locator": source["locator"],
        "reviewer_notes": "AI-assisted draft based on the exact local Taqrib corpus transcription; not human sign-off. Original dataset field is not changed.",
    }))


statement_rows: list[dict[str, str]] = []
statement_id_by_key: dict[str, str] = {}
for s in SPECS:
    case_id, cand_key = s["case"], s["cand"]
    statement_id = f"{case_id}-{cand_key}-S{s['n']:02d}"
    statement_id_by_key[f"{case_id}|{cand_key}|{s['n']}"] = statement_id
    source = case_sources[f"{case_id}|{cand_key}"]
    text_evidence_id = f"EVID-{statement_id}-TEXT"
    values = {
        "repeat_case_id": case_id,
        "candidate_key": cand_key,
        "statement_id": statement_id,
        "statement_record_status": "reviewed_statement",
        "statement_type": s["kind"],
        "statement_text_verbatim": s["text"],
        "statement_text_status": "transcribed",
        "grade_base_verbatim": s.get("base", ""),
        "grade_base_text_status": "transcribed" if s.get("base") else "not_applicable",
        "grade_qualification_verbatim": s.get("qual", ""),
        "grade_qualification_text_status": "transcribed" if s.get("qual") else "not_applicable",
        "taqrib_rank_number": str(s.get("rank", "")),
        "rank_status": s.get("rank_status", "not_applicable"),
        "taqrib_statement_validity": "supported_taqrib_statement",
        "target_task_scope": s["target"],
        "statement_source_correspondence": "exact",
        "statement_source_span_verbatim": s["text"],
        "statement_source_span_status": "transcribed",
        "statement_source_correspondence_rationale": "The segmented span is an exact substring of the local Taqrib entry transcription. This says nothing by itself about historical authorship or provenance.",
        "statement_source_locator": source["locator"],
        "statement_source_evidence_record_id": text_evidence_id,
        "historical_input_eligibility": s["hist"],
        "historical_input_eligibility_rationale": "Not assessed: no frozen historical-input policy or evidence-route review was completed for this AI draft.",
        "target_task_scope_rationale": s["target_note"],
        "corroboration_status": "not_examined",
        "temporal_policy_id": "",
        "temporal_policy_version": "",
        "temporal_policy_result": "",
        "reviewer_notes": f"{s.get('note', '')} AI-assisted draft; require researcher review. No source field was edited.",
    }
    if s.get("rank_rule"):
        values["reviewer_notes"] += f" Taxonomy evidence: {s['rank_rule']} at the Taqrib introduction; see linked rank evidence."
    statement_rows.append(make_row(statement_headers, values))


attribution_specs = [
    dict(case="RPT-01", cand="CAND-01", n=1, evaluator="", evaluator_status="none_named",
         transmitter_status="none_identified", form="unclear", passage="no_evaluator_named",
         historical="unresolved", route="unresolved", evidence_mode="full_entry",
         note="No evaluator is named in the passage. This does not establish Ibn Hajar's own synthesis or authorship of the formulation."),
    dict(case="RPT-02", cand="CAND-01", n=1, evaluator="al-Nasa'i (النسائي)", evaluator_status="identified",
         transmitter_status="unknown", form="explicit_attribution", passage="explicit_individual_named",
         historical="explicitly_reported_but_historically_unverified", route="named_authority_route_unverified", evidence_mode="statement",
         note="Taqrib reports the judgement as al-Nasa'i's. The route to that report is not traced, and this is not treated as a direct quotation."),
    dict(case="RPT-03", cand="CAND-01", n=1, evaluator="", evaluator_status="collective_unidentified",
         transmitter_status="none_identified", form="collective_attribution", passage="collective_only",
         historical="unresolved", route="unresolved", evidence_mode="statement",
         note="عابوا identifies an unnamed collective only. Do not identify it with Abū Ḥātim or another critic based on related reports."),
    dict(case="RPT-05", cand="CAND-01", n=1, evaluator="", evaluator_status="none_named",
         transmitter_status="none_identified", form="unclear", passage="no_evaluator_named",
         historical="unresolved", route="unresolved", evidence_mode="full_entry",
         note="No evaluator is named; Taqrib work authorship is not passage-level authorship evidence."),
    dict(case="RPT-05", cand="CAND-02", n=1, evaluator="", evaluator_status="none_named",
         transmitter_status="none_identified", form="unclear", passage="no_evaluator_named",
         historical="unresolved", route="unresolved", evidence_mode="full_entry",
         note="No evaluator is named; Taqrib work authorship is not passage-level authorship evidence."),
    dict(case="RPT-06", cand="CAND-01", n=1, evaluator="", evaluator_status="none_named",
         transmitter_status="none_identified", form="unclear", passage="no_evaluator_named",
         historical="unresolved", route="unresolved", evidence_mode="full_entry",
         note="No evaluator is named. The Taqrib entry's work-level author metadata does not establish who formulated this grade historically."),
]

attribution_rows: list[dict[str, str]] = []
for a in attribution_specs:
    stid = statement_id_by_key[f"{a['case']}|{a['cand']}|{a['n']}"]
    source = case_sources[f"{a['case']}|{a['cand']}"]
    attrib_id = f"ATTR-{stid}"
    candidate = candidates[(a["case"], a["cand"])]
    evidence_text = candidate["taqrib_entry_text_verbatim"] if a["evidence_mode"] == "full_entry" else SPECS[
        next(i for i, spec in enumerate(SPECS) if spec["case"] == a["case"] and spec["cand"] == a["cand"] and spec["n"] == a["n"])
    ]["text"]
    attribution_rows.append(make_row(attribution_headers, {
        "repeat_case_id": a["case"],
        "candidate_key": a["cand"],
        "attribution_link_id": attrib_id,
        "statement_id": stid,
        "named_historical_evaluator": a["evaluator"],
        "evaluator_value_status": a["evaluator_status"],
        "intermediary_transmitter": "",
        "transmitter_value_status": a["transmitter_status"],
        "surviving_wording_author": "",
        "wording_author_value_status": "unknown",
        "attribution_form": a["form"],
        "passage_evaluator_naming_status": a["passage"],
        "historical_evaluator_attribution_status": a["historical"],
        "transmission_route_status": a["route"],
        "compiler_authorship_status": "unresolved",
        "attribution_evidence_verbatim": evidence_text,
        "attribution_evidence_text_status": "transcribed",
        "attribution_evidence_locator": source["locator"],
        "transmission_route_evidence_record_id": "",
        "reviewer_notes": f"{a['note']} AI-assisted draft; no historical route evidence was examined.",
    }))


source_metadata_rows: list[dict[str, str]] = []
source_evidence_rows: list[dict[str, str]] = []


def add_evidence(case_id: str, cand_key: str, evidence_id: str, source_id: str, role: str,
                 text: str, locator: str, statement_id: str = "", attribution_id: str = "") -> None:
    source_evidence_rows.append(make_row(evidence_headers, {
        "repeat_case_id": case_id,
        "candidate_key": cand_key,
        "evidence_record_id": evidence_id,
        "source_record_id": source_id,
        "statement_id": statement_id,
        "attribution_link_id": attribution_id,
        "evidence_role": role,
        "evidence_text_verbatim": text,
        "evidence_text_status": "transcribed",
        "source_locator": locator,
    }))


def add_metadata(row: dict[str, str]) -> None:
    source_metadata_rows.append(make_row(metadata_headers, row))


# Metadata and evidence for the local source records that supplied the original fields.
for case_id, case in cases.items():
    source_id = f"SRC-{case_id}-INPUT"
    narrator_id = case["dataset_narrator_id"]
    if case["dataset_name"] == "HadithDB":
        source_title = "HadithDB narrators_db.json (local raw snapshot)"
        source_work_id = "HADITHDB-LOCAL-NARRATORS"
        corpus_path = "data/1_raw/hadithdb/narrators_db.json"
        locator = f"JSON pointer /{narrator_id}; field data/الرتبة عند ابن حجر"
        witness_id = "HadithDB local JSON snapshot"
        witness_type = "local JSON database snapshot"
    else:
        source_title = "Shamela4 Full DB narrator metadata parquet"
        source_work_id = "SHAMELA4-LOCAL-NARRATORS"
        corpus_path = "data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet"
        locator = f"Parquet row id={narrator_id}; biography_text.summary/الرتبة عند ابن حجر"
        witness_id = "Shamela4 Full DB local metadata snapshot"
        witness_type = "local Parquet metadata snapshot"
    add_metadata({
        "repeat_case_id": case_id, "candidate_key": "", "source_record_id": source_id,
        "source_work_id": source_work_id, "source_work_title": source_title,
        "consulted_edition": "Local raw snapshot inspected 2026-11-14",
        "consulted_editor": "", "consulted_witness_id": witness_id, "consulted_witness_type": witness_type,
        "consulted_corpus_artifact_id": corpus_path, "consulted_corpus_artifact_type": "local raw dataset artifact",
        "source_page_numbering_note": "not_applicable", "source_work_author_compiler": "",
        "source_author_metadata_status": "not_applicable", "source_locator_verbatim": locator,
        "canonical_source_locator_key": f"{source_work_id}:{narrator_id}:grade-field",
        "source_verification_status": "verified_in_corpus", "edition_variant_status": "not_applicable",
        "edition_metadata_evidence_record_id": "",
        "reviewer_notes": "Raw source record/field checked locally for this AI draft; evidence concerns the stored dataset value only.",
    })
    add_evidence(case_id, "", f"EVID-{case_id}-INPUT-FIELD", source_id, "other",
                 case["original_grade_verbatim"], locator)


# Metadata and exact statement-span evidence for each consulted Taqrib entry.
for (case_id, cand_key), candidate in candidates.items():
    source = case_sources[f"{case_id}|{cand_key}"]
    meta_evidence_id = f"EVID-META-{case_id}-{cand_key}-TAQRIB"
    variant_status = "variant_marked_in_edition_metadata" if "[" in candidate["taqrib_entry_text_verbatim"] else "not_assessed"
    add_metadata({
        "repeat_case_id": case_id, "candidate_key": cand_key, "source_record_id": source["source_record_id"],
        "source_work_id": "3076", "source_work_title": "تقريب التهذيب",
        "consulted_edition": "دار الرشيد، الطبعة الأولى، ١٤٠٦هـ/١٩٨٦م (as recorded in local Shamela4 book metadata)",
        "consulted_editor": "محمد عوامة", "consulted_witness_id": f"Shamela4 local book 3076 page_id {source['page_id']}",
        "consulted_witness_type": "local digital page transcription; no printed page image inspected",
        "consulted_corpus_artifact_id": "data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/3076__تقريب-التهذيب/pages.jsonl",
        "consulted_corpus_artifact_type": "JSON Lines transcription of Shamela4 book pages",
        "source_page_numbering_note": "Local corpus page_num is recorded. Book metadata says numbering matches print; the printed page image was not visually inspected in this AI review.",
        "source_work_author_compiler": "ابن حجر العسقلاني", "source_author_metadata_status": "recorded",
        "source_locator_verbatim": source["locator"],
        "canonical_source_locator_key": f"3076:{source['page_num']}:{source['entry_number']}",
        "source_verification_status": "verified_in_corpus", "edition_variant_status": variant_status,
        "edition_metadata_evidence_record_id": meta_evidence_id,
        "reviewer_notes": "This confirms text in the local transcription, not historical attribution or direct inspection of the printed page. Square brackets in entry 6809 are explicitly tied by book metadata to inter-edition differences.",
    })
    add_evidence(case_id, cand_key, meta_evidence_id, source["source_record_id"], "edition_metadata",
                 metadata_excerpt, "data/1_raw/Shamela4_Full_DB/26__التراجم-والطبقات/3076__تقريب-التهذيب/book_metadata.json:betaka_text")

    for spec in [x for x in SPECS if x["case"] == case_id and x["cand"] == cand_key]:
        stid = statement_id_by_key[f"{case_id}|{cand_key}|{spec['n']}"]
        add_evidence(case_id, cand_key, f"EVID-{stid}-TEXT", source["source_record_id"], "passage_text",
                     spec["text"], source["locator"], statement_id=stid)


# Separate passage-level attribution evidence; it never proves a historical route by itself.
for a in attribution_specs:
    stid = statement_id_by_key[f"{a['case']}|{a['cand']}|{a['n']}"]
    source = case_sources[f"{a['case']}|{a['cand']}"]
    candidate = candidates[(a["case"], a["cand"])]
    attribution_id = f"ATTR-{stid}"
    evidence_text = candidate["taqrib_entry_text_verbatim"] if a["evidence_mode"] == "full_entry" else next(
        x["text"] for x in SPECS if x["case"] == a["case"] and x["cand"] == a["cand"] and x["n"] == a["n"]
    )
    add_evidence(a["case"], a["cand"], f"EVID-{stid}-ATTR", source["source_record_id"], "historical_attribution",
                 evidence_text, source["locator"], statement_id=stid, attribution_id=attribution_id)


# Rank taxonomy excerpts are separate source records and are linked to the relevant statement.
for spec in [x for x in SPECS if x.get("rank_rule")]:
    case_id, cand_key = spec["case"], spec["cand"]
    stid = statement_id_by_key[f"{case_id}|{cand_key}|{spec['n']}"]
    intro_source_id = f"SRC-{case_id}-{cand_key}-TAQRIB-INTRO"
    rank_number = spec["rank"]
    intro_locator = f"Taqrib introduction, author preface, rank {rank_number}; {ALIFTA_URL}"
    add_metadata({
        "repeat_case_id": case_id, "candidate_key": cand_key, "source_record_id": intro_source_id,
        "source_work_id": "3076", "source_work_title": "تقريب التهذيب (مقدمة المؤلف، مراتب الرواة)",
        "consulted_edition": "Official Alifta HadithWeb digital transcription",
        "consulted_editor": "", "consulted_witness_id": "HadithWeb bookId=51, mainId=506655",
        "consulted_witness_type": "official online digitized text",
        "consulted_corpus_artifact_id": "", "consulted_corpus_artifact_type": "",
        "source_page_numbering_note": "Section locator used; printed page image not inspected. The site displays [1/81] at the fifth-rank passage; no other pagination is inferred.",
        "source_work_author_compiler": "ابن حجر العسقلاني", "source_author_metadata_status": "recorded",
        "source_locator_verbatim": intro_locator,
        "canonical_source_locator_key": f"alifta:book51:main506655:rank-{rank_number}",
        "source_verification_status": "verified_external_edition", "edition_variant_status": "not_assessed",
        "edition_metadata_evidence_record_id": "",
        "reviewer_notes": f"Retrieved official digital text for rank {rank_number}; this supports taxonomy mapping only, not the narrator-specific historical attribution or target eligibility.",
    })
    add_evidence(case_id, cand_key, f"EVID-{stid}-RANK", intro_source_id, "other",
                 RANK_RULES[spec["rank_rule"]], intro_locator, statement_id=stid)


write_csv("PASS_B_CANDIDATE_DECISIONS_AI_DRAFT.csv", "PASS_B_CANDIDATE_DECISIONS_BLANK.csv", candidate_rows)
write_csv("PASS_B_STATEMENT_DECISIONS_AI_DRAFT.csv", "PASS_B_STATEMENT_DECISIONS_BLANK.csv", statement_rows)
write_csv("PASS_B_ATTRIBUTION_DECISIONS_AI_DRAFT.csv", "PASS_B_ATTRIBUTION_DECISIONS_BLANK.csv", attribution_rows)
write_csv("PASS_B_SOURCE_EVIDENCE_AI_DRAFT.csv", "PASS_B_SOURCE_EVIDENCE_DECISIONS_BLANK.csv", source_evidence_rows)
write_csv("PASS_B_SOURCE_METADATA_AI_DRAFT.csv", "PASS_B_SOURCE_METADATA_DECISIONS_BLANK.csv", source_metadata_rows)


AI_REVIEW_NOTES = f"""# AI-assisted Pass B annotation draft

**Status:** version 2 draft for researcher review; not a human annotation, not blinded, not independent validation, and not a consistency-repeat result.
**Created:** {date.today().isoformat()}
**Schema basis:** Manual Collation Schema v2.2.

## What this package contains

This draft applies Pass B segmentation and source comparison to the six-case packet: 6 cases, 7 candidate-entry rows, 22 statement rows, and 6 attribution links. It preserves every original field and the supplied Taqrib text. It does not edit the blank reviewer templates, the frozen Pass A file, source data, or prior audit outputs.

The annotator is an AI system that has already seen earlier discussion of these cases. This work therefore cannot be treated as a blind repeat by the researcher or as a second independent annotator. Do not calculate inter-reviewer agreement or delayed within-researcher consistency from these files. Use them only as a concrete AI proposal for the researcher to accept, correct, or reject.

## RPT-05 key correction requiring attention

The packet candidate key says **CAND-01 = Taqrib entry 5570** and **CAND-02 = entry 5569**. The frozen Pass A rows instead attach entry 5569 evidence to CAND-01 and entry 5570 evidence to CAND-02. That is a key mismatch in the frozen submission; the frozen file is preserved unchanged and a separate `PASS_A_RPT05_KEY_ERRATUM.md` records the discrepancy.

The local HadithDB record 278 gives Qays ibn Hafs ibn al-Qaʿqaʿ, kunya Abū Muḥammad, al-Tamīmī/al-Dārimī, al-Baṣrī, and death 227 AH. Those identifiers correspond to Taqrib entry 5569 (packet CAND-02), whose text is `قيس ابن حفص التميمي الدارمي أبو محمد البصري ثقة له أفراد من العاشرة مات سنة سبع وعشرين`. Entry 5570 (packet CAND-01) explicitly says “another” Qays ibn Hafs, settled in Egypt, with a different generation/date description and the grade `مقبول`. The human's intended identity match appears to be supported for CAND-02; CAND-01 is the homonym candidate. This is a proposed correction to the alias mapping, not a silent modification of Pass A.

**Do not reconcile the two rows by swapping them in place.** If you agree, add a dated correction record after reviewing the packet-to-source key, preserving the frozen Pass A bytes and hashes.

## Annotation summary and qualifications

- **RPT-01:** one qualified grade, `ثقة ثبت فاضل` with the teacher/Basra qualification kept intact; separate generation, death-year, and age statements. `rank_status=unresolved` and the rank number is blank; no analogy or additional rank category is introduced.
- **RPT-02:** `وثقه النسائي` is an earlier-critic judgement explicitly reported as al-Nasa'i's, not treated as Ibn Hajar's own grade. `من الثالثة` is a generation label, not rank 3. The historical route remains unverified.
- **RPT-03:** the no-audition criticism is a specific transmission criticism and `من العاشرة` is generation information. The collective behind `عابوا` is not identified, and no related report is substituted for its route.
- **RPT-04:** five separate claims are preserved: Companion status, parentage, campaigns, death/location, and age. `صحابي` receives rank 1 only as Taqrib taxonomy/status, never as an ordinary reliability grade. A separate status-task specification is not approved.
- **RPT-05 CAND-01 / entry 5570:** `مقبول` maps to rank 6 in the introduction, but the candidate does not match the original dataset grade field; the statement must not be attached to narrator ID 278.
- **RPT-05 CAND-02 / entry 5569:** `ثقة له أفراد` matches the original field. Rank 3 is mapped from the explicit descriptor `ثقة`; `له أفراد` is preserved and not assigned an assumed severity. Attribution remains unresolved.
- **RPT-06:** `ثقة` maps to rank 3; `يقال له رؤية` stays a reported biographical claim and is not converted into Companion status; the alternative death years remain verbatim.

## Source and eligibility boundaries

The local corpus confirms that the cited Taqrib spans are present in the local transcription. The book metadata records the Awwāma/Dār al-Rashīd edition and explains square-bracketed differences; the printed page images were not inspected in this AI review. The rank excerpts were checked in the official Alifta digital text of Taqrib's introduction. These sources establish text and taxonomy rules only; they do not establish historical authorship, the origin of a judgement, or a traceable route.

Only the local source records needed for these comparisons and the Taqrib introduction were checked for this draft. Other bibliographic references inherited in `PASS_B_SOURCE_REFERENCES.csv` were not re-opened. Corroboration is `not_examined`; historical-input eligibility is `not_assessed` throughout. No statement is cleared as a training target. Target-scope values are provisional diagnostics against the proposed ordinary narrator-grade task; no versioned target-task manifest is frozen.

## Human review order

1. Resolve the RPT-05 alias-key discrepancy in a separate correction record before using either candidate's identity outcome.
2. Review the statement boundaries and exact Arabic spans, especially RPT-01's unresolved rank status and RPT-04's five factual/status claims.
3. Review the attribution rows. Keep work-level authorship distinct from wording authorship and historical evaluator attribution.
4. Keep all target and historical-input eligibility fields open unless the task manifest and required provenance evidence are established.
5. If you disagree, edit a separate researcher-reviewed copy and record why; retain this AI draft unchanged.
"""

(OUT / "AI_REVIEW_NOTES.md").write_text(AI_REVIEW_NOTES, encoding="utf-8")

ERRATUM = """# Pass A RPT-05 candidate-key erratum

**Status:** Additive erratum; the frozen Pass A CSV and its manifest are unchanged.

## Recorded mismatch

The six-case source packet defines the RPT-05 keys as:

| Packet key | Taqrib locator | Entry identity wording |
|---|---|---|
| CAND-01 | local corpus page 456, entry 5570 | `قيس ابن حفص آخر بصري سكن مصر يكنى أبا محمد` |
| CAND-02 | local corpus page 456, entry 5569 | `قيس ابن حفص التميمي الدارمي أبو محمد البصري` |

The frozen Pass A file records CAND-01 as confirmed using locator `3076; 382; 5569` and evidence text from entry 5569. It records CAND-02 as unresolved using locator `3076; 383; 5570` and text from entry 5570. Thus the evidence and locators in the two rows are associated with the opposite packet keys. This is a key-association defect in the frozen annotation record; it is not repaired here.

## Local evidence checked for this erratum

- HadithDB record 278: `قيس بن حفص بن القعقاع`; kunya `أبو محمد`; affiliation `التميمي, الدارمي مولاهم, البصري`; death `227 هـ`; stored Ibn Hajar field `ثقة له أفراد`.
- Taqrib entry 5569: `قيس ابن حفص التميمي الدارمي أبو محمد البصري ثقة له أفراد من العاشرة مات سنة سبع وعشرين`.
- Taqrib entry 5570: `قيس ابن حفص آخر بصري سكن مصر يكنى أبا محمد مقبول من الثانية عشرة مات سنة إحدى وثمانين تمييز`.
- The packet's identity excerpt for entry 5570 quotes al-Mizzi's Tamyiz entry 4900, describing the Basran who settled in Egypt and died in 281 AH. The excerpt is inherited packet text; this erratum did not independently reopen the cited al-Mizzi page.

## Provisional implication

The HadithDB biographical fields and original grade correspond to packet candidate CAND-02 / Taqrib 5569. Candidate CAND-01 / Taqrib 5570 is a distinct homonym candidate. This strongly suggests the Pass A identity values were attached to the wrong candidate keys. It does not authorize swapping cells in the frozen record. If the researcher confirms the packet key and source row, record a new dated correction/addendum linked to the original SHA-256; preserve the original freeze unchanged.
"""
(OUT / "PASS_A_RPT05_KEY_ERRATUM.md").write_text(ERRATUM, encoding="utf-8")


input_paths = [
    PASS_B / "PASS_B_CASES.csv",
    PASS_B / "PASS_B_CANDIDATES.csv",
    PASS_B / "PASS_B_SOURCE_REFERENCES.csv",
    PASS_B / "PASS_B_CANDIDATE_DECISIONS_BLANK.csv",
    PASS_B / "PASS_B_STATEMENT_DECISIONS_BLANK.csv",
    PASS_B / "PASS_B_ATTRIBUTION_DECISIONS_BLANK.csv",
    PASS_B / "PASS_B_SOURCE_EVIDENCE_DECISIONS_BLANK.csv",
    PASS_B / "PASS_B_SOURCE_METADATA_DECISIONS_BLANK.csv",
    REVIEWER / "PASS_A_SUBMISSIONS/PASS_A_FROZEN_IMMEDIATE_2026-11-14/PASS_A_IDENTITY_DECISIONS.csv",
    REVIEWER / "PASS_A_SUBMISSIONS/PASS_A_FROZEN_IMMEDIATE_2026-11-14/PASS_A_FREEZE_MANIFEST.json",
    SCHEMA, PROTOCOL, HADITHDB, SHAMELA_NARRATORS, TAQRIB_PAGES, TAQRIB_META,
]
output_paths = [
    OUT / name for name in (
        "PASS_B_CANDIDATE_DECISIONS_AI_DRAFT.csv",
        "PASS_B_STATEMENT_DECISIONS_AI_DRAFT.csv",
        "PASS_B_ATTRIBUTION_DECISIONS_AI_DRAFT.csv",
        "PASS_B_SOURCE_EVIDENCE_AI_DRAFT.csv",
        "PASS_B_SOURCE_METADATA_AI_DRAFT.csv",
        "AI_REVIEW_NOTES.md",
        "PASS_A_RPT05_KEY_ERRATUM.md",
        "build_ai_pass_b_draft.py",
    )
]

manifest = {
    "package_name": "ai_assisted_pass_b_draft_six_case_v2",
    "created_on": date.today().isoformat(),
    "status": "ai_assisted_draft_for_human_review_not_blinded_not_independent",
    "schema_baseline": "Manual Collation Schema v2.2",
    "protocol_baseline": "Pilot Evaluation and Annotation Protocol v1.0",
    "case_count": len(cases),
    "candidate_row_count": len(candidates),
    "statement_row_count": len(statement_rows),
    "attribution_link_count": len(attribution_rows),
    "source_evidence_row_count": len(source_evidence_rows),
    "source_metadata_row_count": len(source_metadata_rows),
    "input_hashes_sha256": {str(path.relative_to(REPO)): sha256(path) for path in input_paths},
    "output_hashes_sha256": {path.name: sha256(path) for path in output_paths},
    "manifest_hashing": "This manifest is excluded from its own output hashes; PASS_B_AI_DRAFT_MANIFEST.sha256 hashes this manifest.",
    "limitations": [
        "The AI has seen earlier discussion of these cases; this is not a blind repeat, independent annotator, or inter-reviewer agreement result.",
        "RPT-05 frozen Pass A candidate-key association is crossed; preserved unchanged and documented by an additive erratum.",
        "Local Taqrib corpus text and metadata were inspected; printed page images were not visually inspected.",
        "Inherited bibliographic references other than the local corpus sources and the official Taqrib introduction were not reopened.",
        "Historical evaluator provenance, transmission routes, corroboration, and historical-input eligibility remain unresolved or not assessed.",
        "No statement is certified as a supervised-learning target; the target-task manifest is not frozen.",
        "RPT-01's compound descriptor is left rank-unresolved; the draft does not create or propose any category outside Ibn Hajar's twelve ranks.",
    ],
}
(OUT / "PASS_B_AI_DRAFT_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(OUT / "PASS_B_AI_DRAFT_MANIFEST.sha256").write_text(
    f"{sha256(OUT / 'PASS_B_AI_DRAFT_MANIFEST.json')}  PASS_B_AI_DRAFT_MANIFEST.json\n", encoding="ascii"
)

print(json.dumps({
    "output_directory": str(OUT),
    "cases": len(cases),
    "candidates": len(candidate_rows),
    "statements": len(statement_rows),
    "attribution_links": len(attribution_rows),
    "source_evidence": len(source_evidence_rows),
    "source_metadata": len(source_metadata_rows),
    "manifest_sha256": sha256(OUT / "PASS_B_AI_DRAFT_MANIFEST.json"),
}, ensure_ascii=False, indent=2))
