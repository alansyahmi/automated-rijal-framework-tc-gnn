# Annotation Exception Rules v1

| Item | Value |
| --- | --- |
| Status | Proposed; inactive |
| Registry version | 1.0 |
| Schema version | 1.0 |
| Activation | Requires explicit human approval recorded in the registry |
| Production integration | None; the current proposal generator does not load this registry |

This package defines an isolated, review-only exception registry for five patterns found in the ten-case pilot. It does not revise Schema v2.2, Protocol v1.0, frozen annotations, or the current base-rule registry. The proposed behaviors are computational controls for testing, not independently validated scholarly conclusions.

## Files

- [`annotation_rules/EXCEPTION_RULE_SCHEMA_V1.json`](annotation_rules/EXCEPTION_RULE_SCHEMA_V1.json) defines the registry fields, action values, exact-span trigger, and human-approval requirements.
- [`annotation_rules/EXCEPTION_RULE_REGISTRY_V1.json`](annotation_rules/EXCEPTION_RULE_REGISTRY_V1.json) contains five proposed, inactive rules.
- [`annotation_exception_rules_v1.py`](annotation_exception_rules_v1.py) validates and previews registry matches for isolated review/tests. The production generator does not import it.
- [`test_annotation_exception_registry_v1.py`](test_annotation_exception_registry_v1.py) tests the proposed behaviors and verifies the existing generator output against the saved v1.0.1 pilot output.

## Registry contract

Every rule has a stable ID and version, an exact complete statement-span trigger, a scoped interpretation dimension, scope gates for confirmed identity and verified text, explicit actions, a rationale, expected behavior, pilot references, evidence status, and an approval record. Target eligibility is explicitly outside every rule's scope. Rules are not matched by substring, normalized spelling, or fuzzy similarity.

The five initial patterns are:

| Pilot | Exact span | Proposed behavior |
| --- | --- | --- |
| PROV-04-C01-S01 | `ثقة له أفراد` | Suppress a naive standalone base match and abstain for review. |
| PROV-24-C01-S01 | `وثقه النسائي` | Preserve the attributed judgement, suppress a naive standalone grade, and abstain for review. |
| PROV-39-C01-S01 | `صدوق اختلط في الآخر` | Preserve the existing Rank 5 base result and the exact qualification; do not override the rank. |
| PROV-01-C01-S01 | `صحابي` | Keep Companion status separate from ordinary reliability and abstain for review. Any Rank 1 taxonomy mapping remains a separate decision. |
| PROV-51-C01-S01 | `عابوا عليه أنه حدث عن أبيه بغير سماع` | Treat as a specific transmission criticism for review; do not assign a conventional grade; retain unresolved attribution. |

PROV-02's longer compound statement is a negative test. It must not match a standalone phrase rule across the full compound span and remains an abstention in the current generator.

## Execution and conflict policy

The registry is inactive. Calling the isolated evaluator without its explicit preview flag returns no exception actions. Tests use preview mode to inspect proposed actions; the result always records that actions were not applied to the production generator and preserves the original base result.

An exact span that matches more than one rule returns `conflict_abstain`, with no selected rule or actions. The evaluator does not use priority to resolve conflicts. Missing identity, span, or source-verification prerequisites also fail closed to human review.

No exception may assign or force a narrator reliability rank. `preserve_qualification` keeps a separately supported base result intact; it does not create that rank. An unapproved rule must have null approval metadata; an approved but inactive rule may be retained as a staged decision, but it cannot run while `active=false` or while the registry status is `inactive`. Activation requires status `approved`, `active=true`, and a recorded approver, date, and approval reference. The registry in this package records none of those approvals.

## Generation-status base rules

The five reviewer-confirmed generation-status false abstentions remain ordinary base-rule candidates. They are not present in this exception registry. This package does not change their registry values or enable them.

## Research boundary

The five pilot patterns are development examples. They do not estimate accuracy or establish that a rule should be activated. Historical attribution, narrator reliability, rank suitability, and model eligibility remain outside this registry's decisions.
