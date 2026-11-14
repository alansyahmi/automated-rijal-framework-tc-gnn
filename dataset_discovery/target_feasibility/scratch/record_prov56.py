import csv
from pathlib import Path

working_path = Path("dataset_discovery/target_feasibility/manual_collation_pilot_10/MANUAL_COLLATION_PILOT_10_WORKING.csv")

with working_path.open(encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = list(reader.fieldnames)
    rows = list(reader)

for r in rows:
    if r["audit_record_id"] == "PROV-56":
        r["taqrib_entry_number"] = "7638"
        r["taqrib_printed_page"] = "596"
        r["taqrib_entry_name_verbatim"] = "يحيى ابن محمد ابن عبد الله ابن مهران المدني مولى بني نوفل يقال له الجاري بجيم وراء خفيفة"
        r["taqrib_grade_verbatim"] = "صدوق"
        r["taqrib_qualification_verbatim"] = "يخطىء"
        r["taqrib_rank_number"] = "5"
        r["taqrib_identity_match_status"] = "exact_match"
        r["taqrib_text_match_status"] = "minor_variation"
        r["assessment_author"] = "Ibn Hajar"
        r["assessment_attribution_status"] = "compiler_own_synthesis"
        r["compiler_or_transmitter"] = "Ibn Hajar"
        r["editorial_material_status"] = "none"
        r["attribution_evidence_verbatim"] = "صدوق يخطىء من كبار العاشرة"
        r["source_locator"] = "Taqrib, p. 596, entry 7638"
        r["source_verification_status"] = "verified_in_corpus"
        r["textual_fidelity"] = "high"
        r["attribution_fidelity"] = "high"
        r["identity_fidelity"] = "high"
        r["record_disposition"] = "verified_ibn_hajar_assessment"
        r["input_eligibility"] = "target_evaluation_only"
        r["exclusion_or_quarantine_reason"] = "none"
        r["reviewer_notes"] = "Resolved historical identity through 4-generation lineage, sobriquet al-Jari, patronage, and tabaqah. Ibn Hajar combines base grade صدوق with the defect qualification يخطىء, placing the narrator in Rank 5 under the project's 12-rank scheme. Text match recorded as minor_variation due to orthographic difference (يخطئ. vs يخطىء). Ibn Hajar's assessment appears alongside earlier reports of both favourable and critical evaluations; the precise textual and transmission relationship between those reports and his formulation has not yet been established. Dropping the qualification would falsely elevate a Rank 5 narrator to Rank 4. Corroboration remains unresolved."
        r["corroboration_status"] = "unresolved_corroboration"

with working_path.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)

content = working_path.read_text(encoding="utf-8-sig")
assert "\u2014" not in content, "Em-dash in CSV"
assert "\u2013" not in content, "En-dash in CSV"
print("PROV-56 recorded successfully in MANUAL_COLLATION_PILOT_10_WORKING.csv with ZERO forbidden dashes!")

