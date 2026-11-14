import csv
from pathlib import Path

working_path = Path("dataset_discovery/target_feasibility/manual_collation_pilot_10/MANUAL_COLLATION_PILOT_10_WORKING.csv")

with working_path.open(encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = list(reader.fieldnames)
    rows = list(reader)

for r in rows:
    if r["audit_record_id"] == "PROV-37":
        r["taqrib_entry_number"] = "1650"
        r["taqrib_printed_page"] = "189"
        r["taqrib_entry_name_verbatim"] = "خالد ابن عبد الرحمن ابن بكير السلمي أبو أمية البصري"
        r["taqrib_grade_verbatim"] = "صدوق"
        r["taqrib_qualification_verbatim"] = "يخطىء"
        r["taqrib_rank_number"] = "5"
        r["taqrib_identity_match_status"] = "exact_match"
        r["taqrib_text_match_status"] = "minor_variation"
        r["assessment_author"] = "Ibn Hajar"
        r["assessment_attribution_status"] = "compiler_own_synthesis"
        r["compiler_or_transmitter"] = "Ibn Hajar"
        r["editorial_material_status"] = "none"
        r["attribution_evidence_verbatim"] = "صدوق يخطىء من الثامنة"
        r["source_locator"] = "Taqrib, p. 189, entry 1650"
        r["source_verification_status"] = "verified_in_corpus"
        r["textual_fidelity"] = "high"
        r["attribution_fidelity"] = "high"
        r["identity_fidelity"] = "high"
        r["record_disposition"] = "verified_ibn_hajar_assessment"
        r["input_eligibility"] = "target_evaluation_only"
        r["exclusion_or_quarantine_reason"] = "none"
        r["reviewer_notes"] = "Resolved historical identity through lineage (Ibn Bukayr), nisbah (al-Sulami, al-Basri), kunya (Abu Umayyah), tabaqah (eighth), and canonical symbols (خ ت س), decisively distinguishing the subject from homonym entry 1652 (Khalid ibn Abd al-Rahman al-Makhzumi al-Kufi, 9th tabaqah, also graded صدوق يخطىء). Ibn Hajar combines base grade صدوق with defect qualification يخطىء, placing the narrator in Rank 5 under the project's 12-rank scheme. Text match recorded as minor_variation due to orthographic difference (يخطئ. vs يخطىء). Earlier biographical sources reportedly contain both favourable and critical evaluations, including the expressions لا بأس به, يخطئ, and يخالف في حديثه; the original attribution and transmission relationships have not yet been independently collated."
        r["corroboration_status"] = "unresolved_corroboration"

with working_path.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)

content = working_path.read_text(encoding="utf-8-sig")
assert "\u2014" not in content, "Em-dash in CSV"
assert "\u2013" not in content, "En-dash in CSV"
print("PROV-37 recorded successfully in MANUAL_COLLATION_PILOT_10_WORKING.csv with ZERO forbidden dashes!")

